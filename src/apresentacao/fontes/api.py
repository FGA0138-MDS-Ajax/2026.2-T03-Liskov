"""Cliente HTTP da API do SentIA.

Hoje o backend só oferece GET /health. As rotas /analises e /analises/resumo
seguem a PROPOSTA de docs/frontend/CONTRATO-API.md e ainda não existem: até a
conclusão das issues #19, #21 e #23, este modo mostra uma mensagem de erro.
"""

from datetime import datetime
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


def _para_analise(dados: dict[str, Any]) -> Analise:
    publicacao = dados.get("data_publicacao")
    return Analise(
        id_origem=dados["id_origem"],
        fonte=dados["fonte"],
        texto_original=dados["texto_original"],
        sentimento=dados["sentimento"],
        modelo_nome=dados["modelo"]["nome"],
        data_processamento=datetime.fromisoformat(dados["data_processamento"]),
        data_publicacao=datetime.fromisoformat(publicacao) if publicacao else None,
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
        return self._obter("/health").get("status") == "ok"

    def listar(
        self, filtros: FiltrosAnalises, pagina: int = 1, tamanho: int = 20
    ) -> PaginaAnalises:
        parametros = {**_para_parametros(filtros), "pagina": pagina, "tamanho": tamanho}
        dados = self._obter("/analises", parametros)
        try:
            return PaginaAnalises(
                itens=[_para_analise(item) for item in dados["itens"]],
                pagina=dados["pagina"],
                tamanho=dados["tamanho"],
                total=dados["total"],
            )
        except (KeyError, TypeError, ValueError) as erro:
            raise ErroFonteDados("A resposta da API não segue o contrato.") from erro

    def resumir(self, filtros: FiltrosAnalises) -> ResumoAnalises:
        dados = self._obter("/analises/resumo", _para_parametros(filtros))
        try:
            return ResumoAnalises(
                total=dados["total"],
                por_sentimento={s: dados["por_sentimento"][s] for s in SENTIMENTOS},
                sem_data_publicacao=dados.get("sem_data_publicacao", 0),
            )
        except (KeyError, TypeError) as erro:
            raise ErroFonteDados("A resposta da API não segue o contrato.") from erro
