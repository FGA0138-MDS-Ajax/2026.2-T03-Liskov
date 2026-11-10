"""Cliente HTTP da API do SentIA.

Hoje o backend só oferece GET /health. As rotas /analises e /analises/resumo
seguem a PROPOSTA de docs/frontend/CONTRATO-API.md e ainda não existem: até a
conclusão das issues #19, #21 e #23, este modo mostra uma mensagem de erro.
"""

from datetime import UTC, datetime
from typing import Any

import requests

from src.apresentacao.contrato import (
    SENTIMENTOS,
    Analise,
    ErroFonteDados,
    FiltrosAnalises,
    PaginaAnalises,
    ResumoAnalises,
)


def _para_parametros(filtros: FiltrosAnalises) -> dict[str, str]:
    parametros = {}
    if filtros.inicio is not None:
        parametros["inicio"] = filtros.inicio.isoformat()
    if filtros.fim is not None:
        parametros["fim"] = filtros.fim.isoformat()
    if filtros.sentimento is not None:
        parametros["sentimento"] = filtros.sentimento
    return parametros


def _objeto(valor: Any) -> dict[str, Any]:
    if not isinstance(valor, dict):
        raise TypeError("Objeto JSON esperado.")
    return valor


def _inteiro(valor: Any, minimo: int = 0) -> int:
    # bool é subclasse de int, mas não representa contagem nem paginação.
    if type(valor) is not int or valor < minimo:
        raise ValueError("Inteiro fora do contrato.")
    return valor


def _texto(valor: Any, nao_vazio: bool = False) -> str:
    if not isinstance(valor, str) or (nao_vazio and not valor.strip()):
        raise ValueError("Texto fora do contrato.")
    return valor


def _data_com_fuso(valor: Any) -> datetime:
    data = datetime.fromisoformat(_texto(valor))
    if data.utcoffset() is None:
        raise ValueError("Data deve informar o fuso horário.")
    return data.astimezone(UTC)


def _para_analise(valor: Any) -> Analise:
    dados = _objeto(valor)
    publicacao = dados.get("data_publicacao")
    sentimento = dados["sentimento"]
    if not isinstance(sentimento, str) or sentimento not in SENTIMENTOS:
        raise ValueError("Sentimento fora do contrato.")
    return Analise(
        id_origem=_texto(dados["id_origem"], nao_vazio=True),
        fonte=_texto(dados["fonte"]),
        texto_original=_texto(dados["texto_original"]),
        sentimento=sentimento,
        modelo_nome=_texto(_objeto(dados["modelo"])["nome"], nao_vazio=True),
        data_processamento=_data_com_fuso(dados["data_processamento"]),
        data_publicacao=_data_com_fuso(publicacao) if publicacao is not None else None,
    )


class FonteApi:
    def __init__(
        self, url_base: str, timeout_segundos: float = 5, sessao: Any = None
    ) -> None:
        self._url_base = url_base
        self._timeout = timeout_segundos
        self._sessao = sessao if sessao is not None else requests.Session()

    def _obter(self, rota: str, parametros: dict[str, Any] | None = None) -> Any:
        try:
            resposta = self._sessao.get(
                f"{self._url_base}{rota}", params=parametros, timeout=self._timeout
            )
        except requests.Timeout as erro:
            raise ErroFonteDados("A API demorou demais para responder.") from erro
        except requests.RequestException as erro:
            raise ErroFonteDados(
                "Não foi possível conectar à API. Verifique se ela está em execução."
            ) from erro

        if resposta.status_code in (400, 422):
            raise ErroFonteDados("A API recusou os filtros informados.")
        if resposta.status_code == 404:
            raise ErroFonteDados(f"A API não oferece a rota {rota}.")
        if resposta.status_code != 200:
            raise ErroFonteDados(
                f"A API retornou um erro inesperado (HTTP {resposta.status_code})."
            )

        try:
            return resposta.json()
        except ValueError as erro:
            raise ErroFonteDados("A API retornou uma resposta inválida.") from erro

    def verificar_saude(self) -> bool:
        """Consulta GET /health, a única rota que já existe no backend."""
        dados = self._obter("/health")
        if not isinstance(dados, dict):
            raise ErroFonteDados("A resposta da API não segue o contrato.")
        return dados.get("status") == "ok"

    def listar(
        self, filtros: FiltrosAnalises, pagina: int = 1, tamanho: int = 20
    ) -> PaginaAnalises:
        try:
            _inteiro(pagina, minimo=1)
            _inteiro(tamanho, minimo=1)
        except ValueError as erro:
            raise ErroFonteDados(
                "Página e tamanho devem ser inteiros positivos."
            ) from erro
        parametros = {**_para_parametros(filtros), "pagina": pagina, "tamanho": tamanho}
        dados = self._obter("/analises", parametros)
        try:
            dados = _objeto(dados)
            numero = _inteiro(dados["pagina"], minimo=1)
            limite = _inteiro(dados["tamanho"], minimo=1)
            total = _inteiro(dados["total"])
            itens = dados["itens"]
            if not isinstance(itens, list):
                raise TypeError("Itens deve ser uma lista.")
            restantes = max(0, total - (numero - 1) * limite)
            if len(itens) > min(limite, restantes):
                raise ValueError("Quantidade de itens incompatível com a paginação.")
            return PaginaAnalises(
                itens=[_para_analise(item) for item in itens],
                pagina=numero,
                tamanho=limite,
                total=total,
            )
        except (KeyError, TypeError, ValueError, OverflowError) as erro:
            raise ErroFonteDados("A resposta da API não segue o contrato.") from erro

    def resumir(self, filtros: FiltrosAnalises) -> ResumoAnalises:
        dados = self._obter("/analises/resumo", _para_parametros(filtros))
        try:
            dados = _objeto(dados)
            total = _inteiro(dados["total"])
            contagens = _objeto(dados["por_sentimento"])
            if set(contagens) != set(SENTIMENTOS):
                raise ValueError("Classes incompatíveis com o contrato.")
            por_sentimento = {s: _inteiro(contagens[s]) for s in SENTIMENTOS}
            sem_data = _inteiro(dados.get("sem_data_publicacao", 0))
            if sum(por_sentimento.values()) != total:
                raise ValueError("Contagens incompatíveis com o total filtrado.")
            if filtros.inicio is None and filtros.fim is None and sem_data != 0:
                raise ValueError(
                    "Sem filtro de período não há exclusão por falta de data."
                )
            return ResumoAnalises(
                total=total,
                por_sentimento=por_sentimento,
                sem_data_publicacao=sem_data,
            )
        except (KeyError, TypeError, ValueError) as erro:
            raise ErroFonteDados("A resposta da API não segue o contrato.") from erro
