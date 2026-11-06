"""Integra aquisição CSV e classificação BERTweet no pipeline do SentIA."""

import math
from datetime import datetime, timezone
from typing import Any, Iterable

from .aquisicao import converter_rotulo_para_sentia, iterar_dataset_csv
from .classificacao.rotulos import ROTULOS
from .classificacao.bertweet import ClassificadorBertweet


class ErroPipeline(ValueError):
    """Erro de validação ou execução do pipeline."""


def _normalizar_data_publicacao(valor: Any, indice: int) -> datetime | None:
    """Converte data ISO 8601 para datetime UTC; não inventa datas."""
    if valor is None or (isinstance(valor, str) and not valor.strip()):
        return None

    if isinstance(valor, datetime):
        data = valor
    elif isinstance(valor, str):
        try:
            data = datetime.fromisoformat(valor.strip().replace("Z", "+00:00"))
        except ValueError as erro:
            raise ErroPipeline(
                f"Registro {indice}: data_publicacao não está em formato ISO 8601."
            ) from erro
    else:
        raise ErroPipeline(
            f"Registro {indice}: tipo inválido para data_publicacao."
        )

    if data.tzinfo is None:
        raise ErroPipeline(
            f"Registro {indice}: data_publicacao precisa informar fuso horário."
        )

    return data.astimezone(timezone.utc)


class PipelineClassificacao:
    """Processa registros importados e associa previsões aos dados originais."""

    def __init__(
        self,
        classificador: Any | None = None,
        tamanho_lote: int = 32,
        versao_modelo: str | None = None,
    ) -> None:
        if isinstance(tamanho_lote, bool) or not isinstance(tamanho_lote, int):
            raise ValueError("tamanho_lote deve ser um número inteiro.")
        if tamanho_lote <= 0:
            raise ValueError("tamanho_lote deve ser maior que zero.")

        self.tamanho_lote = tamanho_lote
        self.classificador = (
            classificador
            if classificador is not None
            else ClassificadorBertweet(
                tamanho_lote=tamanho_lote
            )
        )
        self.versao_modelo = versao_modelo

        nome = getattr(self.classificador, "nome_modelo", None)
        if not isinstance(nome, str) or not nome.strip():
            raise ErroPipeline("O classificador precisa informar nome_modelo.")

    def _processar_lote(
        self, registros: list[dict[str, Any]], indice_inicial: int
    ) -> list[dict[str, Any]]:
        textos = []
        for deslocamento, registro in enumerate(registros):
            indice = indice_inicial + deslocamento
            if not isinstance(registro, dict):
                raise ErroPipeline(f"Registro {indice}: esperado um dicionário.")
            texto = registro.get("texto_original")
            if not isinstance(texto, str) or not texto.strip():
                raise ErroPipeline(
                    f"Registro {indice}: texto_original ausente ou vazio."
                )
            metadados = registro.get("metadados")
            if metadados is not None and not isinstance(metadados, dict):
                raise ErroPipeline(
                    f"Registro {indice}: metadados precisam ser um dicion?rio."
                )

            textos.append(texto)

        try:
            previsoes = self.classificador.prever_com_probabilidades(textos)
        except Exception as erro:
            raise ErroPipeline(
                f"Falha ao classificar o lote iniciado no registro {indice_inicial}."
            ) from erro

        if not isinstance(previsoes, list) or len(previsoes) != len(registros):
            raise ErroPipeline(
                "O classificador retornou quantidade de previsões diferente "
                "da quantidade de registros."
            )

        resultados = []
        nome_modelo = self.classificador.nome_modelo

        for deslocamento, (registro, previsao) in enumerate(
            zip(registros, previsoes)
        ):
            indice = indice_inicial + deslocamento

            if not isinstance(previsao, dict):
                raise ErroPipeline(
                    f"Registro {indice}: previsão retornada em formato inválido."
                )

            if "sentimento" not in previsao or "probabilidades" not in previsao:
                raise ErroPipeline(
                    f"Registro {indice}: previsão sem sentimento ou probabilidades."
                )

            probabilidades = previsao["probabilidades"]
            if not isinstance(probabilidades, dict):
                raise ErroPipeline(
                    f"Registro {indice}: probabilidades em formato inválido."
                )

            if set(probabilidades) != set(ROTULOS):
                raise ErroPipeline(
                    f"Registro {indice}: probabilidades devem conter "
                    "positivo, negativo e neutro."
                )

            for rotulo in ROTULOS:
                valor = probabilidades[rotulo]
                if isinstance(valor, bool) or not isinstance(valor, (int, float)):
                    raise ErroPipeline(
                        f"Registro {indice}: probabilidade inv?lida para {rotulo}."
                    )
                try:
                    finito = math.isfinite(float(valor))
                except (OverflowError, TypeError, ValueError):
                    finito = False
                if not finito or not 0 <= valor <= 1:
                    raise ErroPipeline(
                        f"Registro {indice}: probabilidade fora do intervalo [0, 1]."
                    )

            if not math.isclose(
                sum(probabilidades.values()), 1.0, rel_tol=0.0, abs_tol=1e-3
            ):
                raise ErroPipeline(
                    f"Registro {indice}: soma das probabilidades deve ser 1."
                )

            try:
                sentimento = converter_rotulo_para_sentia(
                    previsao["sentimento"]
                )
                rotulo_padronizado = converter_rotulo_para_sentia(
                    registro.get("rotulo_padronizado")
                )
                data_publicacao = _normalizar_data_publicacao(
                    registro.get("data_publicacao"), indice
                )
            except ValueError as erro:
                raise ErroPipeline(str(erro)) from erro

            documento = {
                "id_origem": registro.get("id_origem"),
                "fonte": registro.get("fonte"),
                "texto_original": registro["texto_original"],
                "sentimento": sentimento,
                "probabilidades": dict(probabilidades),
                "modelo": {"nome": nome_modelo},
                "data_processamento": datetime.now(timezone.utc),
            }

            if self.versao_modelo:
                documento["modelo"]["versao"] = self.versao_modelo

            if registro.get("rotulo_original") is not None:
                documento["rotulo_original"] = registro["rotulo_original"]

            if rotulo_padronizado is not None:
                documento["rotulo_padronizado"] = rotulo_padronizado

            if data_publicacao is not None:
                documento["data_publicacao"] = data_publicacao

            metadados = registro.get("metadados")
            if metadados:
                if not isinstance(metadados, dict):
                    raise ErroPipeline(
                        f"Registro {indice}: metadados precisam ser um dicionário."
                    )
                documento["metadados"] = dict(metadados)

            resultados.append(documento)

        return resultados

    def processar_registros(
        self, registros: Iterable[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Classifica registros em lotes e devolve documentos para persistência."""
        resultados = []
        lote = []
        indice_inicial = 1
        total_lido = 0

        for registro in registros:
            lote.append(registro)
            total_lido += 1

            if len(lote) == self.tamanho_lote:
                resultados.extend(self._processar_lote(lote, indice_inicial))
                indice_inicial += len(lote)
                lote = []

        if lote:
            resultados.extend(self._processar_lote(lote, indice_inicial))

        if total_lido == 0:
            raise ErroPipeline("Nenhum registro foi recebido para classificação.")

        return resultados

    def processar_csv(
        self,
        caminho_arquivo: str,
        delimitador: str = ",",
        *,
        modo_estrito: bool = True,
    ) -> list[dict[str, Any]]:
        """Importa um CSV e classifica seus registros."""
        registros = iterar_dataset_csv(
            caminho_arquivo,
            delimitador=delimitador,
            modo_estrito=modo_estrito,
        )
        return self.processar_registros(registros)
