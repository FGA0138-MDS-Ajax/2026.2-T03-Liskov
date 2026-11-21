"""Classificador de sentimentos em português com BERTweet via PySentimiento.

O analisador é carregado uma vez e deve ser reutilizado pela aplicação. O
pré-processamento de texto adequado a tweets é feito pelo PySentimiento.
"""
from __future__ import annotations

import gc
import logging
import os
from collections.abc import Iterable, Mapping

from .rotulos import ROTULOS, normalizar_rotulo

NOME_MODELO = "pysentimiento/bertweet-pt-sentiment"
logger = logging.getLogger(__name__)


class ClassificadorBertweet:
    """Classifica textos e devolve rótulos e probabilidades por texto.

    Args:
        analisador: analisador compatível com ``pysentimiento``. Injetável
            para testes ou integração com uma instância já carregada.
        tamanho_lote: número máximo de textos enviados em cada chamada.

    Entradas devem ser strings não vazias. Uma string isolada é tratada como
    um único texto; uma coleção vazia retorna uma lista vazia.

    ``SENTIA_DISPOSITIVO`` aceita ``cpu`` (padrão), ``cuda`` ou ``auto``.
    ``SENTIA_GPU_INDEX`` seleciona o índice físico da GPU (padrão: 0).

    Um analisador injetado é usado exatamente como recebido; seleção de
    dispositivo e recuperação de OOM aplicam-se ao analisador criado aqui.
    """

    def __init__(self, analisador=None, tamanho_lote: int = 32):
        if isinstance(tamanho_lote, bool) or not isinstance(tamanho_lote, int):
            raise TypeError("tamanho_lote deve ser um número inteiro")
        if tamanho_lote <= 0:
            raise ValueError("tamanho_lote deve ser maior que zero")

        self.tamanho_lote = tamanho_lote
        self.nome_modelo = NOME_MODELO
        self._factory = None
        self.dispositivo_ativo = "injetado"

        if analisador is None:
            self._carregar_variaveis_ambiente()
            self._factory = self._obter_factory()
            dispositivo = self._selecionar_dispositivo()
            self.dispositivo_ativo = dispositivo
            logger.info(
                "Dispositivo selecionado para inferência BERTweet: %s.",
                dispositivo,
            )
            self._analisador = self._criar_analisador(dispositivo)
        else:
            self._analisador = analisador

    @staticmethod
    def _carregar_variaveis_ambiente() -> None:
        # .env é opcional; variáveis já definidas no processo têm prioridade.
        try:
            from dotenv import load_dotenv
        except ImportError:
            return
        load_dotenv()

    @staticmethod
    def _obter_factory():
        from pysentimiento import create_analyzer

        return create_analyzer

    @staticmethod
    def _ler_configuracao() -> tuple[str, int]:
        dispositivo = os.getenv("SENTIA_DISPOSITIVO", "cpu").strip().lower()
        if dispositivo not in {"cpu", "cuda", "auto"}:
            raise ValueError(
                "SENTIA_DISPOSITIVO deve ser 'cpu', 'cuda' ou 'auto'"
            )

        valor_indice = os.getenv("SENTIA_GPU_INDEX", "0").strip()
        try:
            indice = int(valor_indice)
        except ValueError as exc:
            raise ValueError("SENTIA_GPU_INDEX deve ser um inteiro não negativo") from exc
        if indice < 0:
            raise ValueError("SENTIA_GPU_INDEX deve ser um inteiro não negativo")
        return dispositivo, indice

    def _selecionar_dispositivo(self) -> str:
        modo, indice = self._ler_configuracao()
        if modo == "cpu":
            return "cpu"

        try:
            import torch
        except ImportError as exc:
            if modo == "auto":
                logger.warning(
                    "PyTorch indisponível; BERTweet será carregado na CPU."
                )
                return "cpu"

            raise RuntimeError(
                "SENTIA_DISPOSITIVO=cuda exige PyTorch instalado."
            ) from exc

        cuda = torch.cuda
        if cuda.is_initialized() and indice != 0:
            mensagem = (
                "A GPU selecionada precisa ser configurada antes da primeira "
                "inicialização do runtime CUDA; reinicie o processo para aplicar "
                "SENTIA_GPU_INDEX."
            )
            if modo == "auto":
                logger.warning("%s Usando CPU.", mensagem)
                return "cpu"
            raise RuntimeError(mensagem)

        # No ROCm, PyTorch também expõe as GPUs AMD pela API torch.cuda.
        # A máscara deve ser definida antes de o runtime CUDA/HIP inicializar.
        if not cuda.is_initialized():
            mascaras = (
                "CUDA_VISIBLE_DEVICES",
                "HIP_VISIBLE_DEVICES",
            )
            mascaras_existentes = [
                nome for nome in mascaras
                if os.environ.get(nome, "").strip()
            ]

            if mascaras_existentes and indice != 0:
                nomes = ", ".join(mascaras_existentes)
                raise RuntimeError(
                    f"{nomes} is already configured. "
                    "To use SENTIA_GPU_INDEX other than zero, "
                    "remove or adjust the masks before starting the process."
                )

            if not mascaras_existentes:
                os.environ["CUDA_VISIBLE_DEVICES"] = str(indice)
                os.environ["HIP_VISIBLE_DEVICES"] = str(indice)

        if cuda.is_available() and cuda.device_count() > 0:
            return "cuda"

        if modo == "auto":
            logger.info("GPU indisponível; BERTweet será carregado na CPU.")
            return "cpu"
        raise RuntimeError(
            f"SENTIA_DISPOSITIVO=cuda, mas não foi possível acessar a GPU "
            f"de índice {indice}."
        )

    def _criar_analisador(self, dispositivo: str):
        # PySentimiento 0.7.3 cria um Transformers Trainer
        # internamente. TrainingArguments/Accelerate lê
        # ACCELERATE_USE_CPU ao inicializar.
        anterior = os.environ.get("ACCELERATE_USE_CPU")
        os.environ["ACCELERATE_USE_CPU"] = (
            "true" if dispositivo == "cpu" else "false"
        )

        try:
            analisador = self._factory(
                task="sentiment",
                lang="pt",
                model_name=NOME_MODELO,
                batch_size=self.tamanho_lote,
            )

            # Garante que o modelo esteja no dispositivo selecionado.
            modelo = getattr(analisador, "model", None)
            if modelo is not None and hasattr(modelo, "to"):
                modelo.to(dispositivo)

                # FP16 e utilizado somente na GPU.
                # Na CPU, preservamos a precisao FP32.
                if dispositivo == "cuda" and hasattr(modelo, "half"):
                    modelo.half()
                    logger.info("Inferencia BERTweet configurada com FP16 na GPU.")

            return analisador
        finally:
            if anterior is None:
                os.environ.pop("ACCELERATE_USE_CPU", None)
            else:
                os.environ["ACCELERATE_USE_CPU"] = anterior

    @staticmethod
    def _eh_erro_memoria_gpu(erro: RuntimeError) -> bool:
        mensagem = str(erro).lower()
        return "out of memory" in mensagem or "cuda oom" in mensagem

    def _recuperar_na_cpu(self) -> None:
        logger.warning(
            "Memória insuficiente na GPU durante a inferência BERTweet. "
            "Recriando o analisador na CPU e repetindo o lote."
        )
        self._analisador = None
        gc.collect()
        try:
            import torch

            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except (ImportError, RuntimeError, AttributeError):
            logger.debug("Não foi possível limpar o cache da GPU.", exc_info=True)

        self._analisador = self._criar_analisador("cpu")
        self.dispositivo_ativo = "cpu"

    def _prever_lote(self, lote: list[str]) -> list:
        """Executa inferência direta, evitando Dataset.map() do PySentimiento."""
        analisador = self._analisador

        # Analisadores internos sem a API de inferência direta usam predict().
        if getattr(self, "_factory", None) is None:
            return analisador.predict(lote)

        atributos_necessarios = (
            "tokenizer",
            "model",
            "_get_output",
            "preprocessing_args",
        )
        try:
            atributos_instancia = vars(analisador)
        except TypeError:
            # Objetos com __slots__ podem não possuir __dict__.
            atributos_instancia = {}

        if not all(
            attr in atributos_instancia or hasattr(type(analisador), attr)
            for attr in atributos_necessarios
        ):
            return analisador.predict(lote)

        import torch
        from pysentimiento.preprocessing import preprocess_tweet

        textos_processados = [
            preprocess_tweet(texto, **analisador.preprocessing_args)
            for texto in lote
        ]

        entradas = analisador.tokenizer(
            textos_processados,
            padding=True,
            truncation=True,
            max_length=analisador.tokenizer.model_max_length,
            return_tensors="pt",
        )

        modelo = analisador.model
        dispositivo = next(modelo.parameters()).device
        entradas = {
            nome: tensor.to(dispositivo)
            for nome, tensor in entradas.items()
        }

        modelo.eval()
        with torch.inference_mode():
            logits = modelo(**entradas).logits

        if not torch.isfinite(logits).all():
            raise RuntimeError("O modelo BERTweet produziu logits não finitos")

        return [
            analisador._get_output(
                texto,
                logits[indice].unsqueeze(0),
                context=None,
            )
            for indice, texto in enumerate(textos_processados)
        ]

    @staticmethod
    def _validar_textos(textos: Iterable[str] | str) -> list[str]:
        if isinstance(textos, Mapping):
            raise TypeError("textos não pode ser um dicionário ou mapeamento")

        if isinstance(textos, str):
            textos = [textos]
        else:
            try:
                textos = list(textos)
            except TypeError as exc:
                raise TypeError(
                    "textos deve ser uma string ou uma coleção de strings"
                ) from exc

        for indice, texto in enumerate(textos):
            if not isinstance(texto, str):
                raise TypeError(
                    f"texto na posição {indice} deve ser uma string"
                )
            if not texto.strip():
                raise ValueError(
                    f"texto na posição {indice} não pode ser vazio"
                )

        return textos

    def prever(self, textos: Iterable[str] | str) -> list[str]:
        """Retorna apenas os rótulos padronizados dos textos recebidos."""
        return [r["sentimento"] for r in self.prever_com_probabilidades(textos)]

    def prever_com_probabilidades(self, textos: Iterable[str] | str) -> list[dict]:
        """Retorna ``[{sentimento, probabilidades}, ...]`` na ordem de entrada."""
        textos = self._validar_textos(textos)
        saidas: list[dict] = []
        for i in range(0, len(textos), self.tamanho_lote):
            lote = textos[i : i + self.tamanho_lote]
            try:
                resultados = self._prever_lote(lote)
            except RuntimeError as erro:
                if (
                    self.dispositivo_ativo != "cuda"
                    or self._factory is None
                    or not self._eh_erro_memoria_gpu(erro)
                ):
                    raise
                self._recuperar_na_cpu()
                resultados = self._prever_lote(lote)

            if len(resultados) != len(lote):
                raise RuntimeError("o analisador retornou quantidade inesperada de resultados")
            for resultado in resultados:
                probabilidades = {rotulo: 0.0 for rotulo in ROTULOS}
                for rotulo, valor in resultado.probas.items():
                    probabilidades[normalizar_rotulo(rotulo)] = float(valor)
                saidas.append(
                    {
                        "sentimento": normalizar_rotulo(resultado.output),
                        "probabilidades": probabilidades,
                    }
                )
        return saidas
