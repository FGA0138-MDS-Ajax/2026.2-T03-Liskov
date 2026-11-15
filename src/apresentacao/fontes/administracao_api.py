"""Cliente HTTP das rotas de administração.

As rotas seguem a PROPOSTA de docs/frontend/CONTRATO-API.md e ainda não existem
no backend (issues #21 e #58). Até lá, este modo mostra uma mensagem de erro.
"""

from typing import Any
from urllib.parse import quote

import requests

from src.apresentacao.contrato import (
    FONTE_PESQUISA,
    SENTIMENTOS,
    SITUACOES_COLETA,
    Coleta,
    ErroAutenticacao,
    ErroFonteDados,
    ExemploAnalise,
    FonteColeta,
    ResultadoImportacao,
    SessaoAdministrador,
)
from src.apresentacao.fontes.api import _data_com_fuso, _inteiro, _objeto, _texto

TAMANHO_MAXIMO_MENSAGEM = 300
_FORA_DO_CONTRATO = "A resposta da API não segue o contrato."


def _mensagem_da_api(resposta: Any) -> str | None:
    """Usa a `mensagem` do corpo de erro, se for um texto curto para o usuário."""
    try:
        mensagem = resposta.json().get("mensagem")
    except (AttributeError, ValueError):
        return None
    if isinstance(mensagem, str) and 0 < len(mensagem.strip()) <= TAMANHO_MAXIMO_MENSAGEM:
        return mensagem.strip()
    return None


def _para_coleta(valor: Any) -> Coleta:
    dados = _objeto(valor)
    situacao = dados["situacao"]
    if not isinstance(situacao, str) or situacao not in SITUACOES_COLETA:
        raise ValueError("Situação fora do contrato.")
    coletados = _inteiro(dados.get("textos_coletados", 0))
    analisados = _inteiro(dados.get("textos_analisados", 0))
    if analisados > coletados:
        raise ValueError("Mais textos analisados do que coletados.")
    mensagem = dados.get("mensagem")
    if mensagem is not None:
        mensagem = _texto(mensagem)
    termo = dados.get("termo")
    if termo is not None:
        termo = _texto(termo, nao_vazio=True)
    contagens = _objeto(dados.get("por_sentimento") or {})
    if not set(contagens) <= set(SENTIMENTOS):
        raise ValueError("Sentimento fora do contrato.")
    por_sentimento = {s: _inteiro(contagens.get(s, 0)) for s in SENTIMENTOS} if contagens else {}
    if sum(por_sentimento.values()) > analisados:
        raise ValueError("Mais sentimentos do que textos analisados.")
    exemplos_brutos = dados.get("exemplos") or []
    if not isinstance(exemplos_brutos, list):
        raise TypeError("Exemplos deve ser uma lista.")
    exemplos = []
    for exemplo in exemplos_brutos:
        exemplo = _objeto(exemplo)
        sentimento = exemplo["sentimento"]
        if sentimento not in SENTIMENTOS:
            raise ValueError("Sentimento fora do contrato.")
        origem_exemplo = exemplo.get("origem")
        if origem_exemplo is not None and origem_exemplo not in ("base", "x"):
            raise ValueError("Origem fora do contrato.")
        exemplos.append(
            ExemploAnalise(
                texto=_texto(exemplo["texto"], nao_vazio=True),
                sentimento=sentimento,
                origem=origem_exemplo,
            )
        )
    origem = dados.get("origem")
    if origem is not None:
        origem = _objeto(origem)
        if set(origem) != {"base", "x", "duplicatas"}:
            raise ValueError("Origem fora do contrato.")
        origem = {chave: _inteiro(valor) for chave, valor in origem.items()}
    return Coleta(
        id=_texto(dados["id"], nao_vazio=True),
        fonte=_texto(dados["fonte"], nao_vazio=True),
        situacao=situacao,
        textos_coletados=coletados,
        textos_analisados=analisados,
        mensagem=mensagem,
        termo=termo,
        por_sentimento=por_sentimento,
        exemplos=tuple(exemplos),
        origem=origem,
    )


class AdministracaoApi:
    def __init__(
        self, url_base: str, timeout_segundos: float = 5, sessao: Any = None
    ) -> None:
        self._url_base = url_base
        self._timeout = timeout_segundos
        self._sessao = sessao if sessao is not None else requests.Session()

    def _chamar(
        self,
        metodo: str,
        rota: str,
        *,
        sessao: SessaoAdministrador | None = None,
        esperado: tuple[int, ...] = (200,),
        recusa: str = "A API recusou os dados enviados.",
        **kwargs: Any,
    ) -> Any:
        cabecalhos = {"Authorization": f"Bearer {sessao.token}"} if sessao else {}
        try:
            resposta = getattr(self._sessao, metodo)(
                f"{self._url_base}{rota}",
                headers=cabecalhos,
                timeout=self._timeout,
                **kwargs,
            )
        except requests.Timeout as erro:
            raise ErroFonteDados("A API demorou demais para responder.") from erro
        except requests.RequestException as erro:
            raise ErroFonteDados(
                "Não foi possível conectar à API. Verifique se ela está em execução."
            ) from erro

        codigo = resposta.status_code
        if codigo == 401:
            raise ErroAutenticacao(
                "Sua sessão expirou. Entre novamente."
                if sessao
                else "Usuário ou senha inválidos."
            )
        if codigo == 403:
            raise ErroAutenticacao("Este usuário não tem permissão de administrador.")
        if codigo == 404:
            raise ErroFonteDados(
                _mensagem_da_api(resposta) or f"A API não oferece a rota {rota}."
            )
        if codigo == 503:
            raise ErroFonteDados(
                _mensagem_da_api(resposta) or "A API está indisponível no momento."
            )
        if codigo == 413:
            raise ErroFonteDados("O arquivo é maior que o limite aceito pela API.")
        if codigo in (400, 415, 422):
            raise ErroFonteDados(_mensagem_da_api(resposta) or recusa)
        if codigo == 429:
            raise ErroFonteDados("Muitas tentativas. Aguarde um pouco e tente de novo.")
        if codigo not in esperado:
            raise ErroFonteDados(f"A API retornou um erro inesperado (HTTP {codigo}).")
        if codigo == 204:
            return None
        try:
            return resposta.json()
        except ValueError as erro:
            raise ErroFonteDados("A API retornou uma resposta inválida.") from erro

    def entrar(self, usuario: str, senha: str) -> SessaoAdministrador:
        dados = self._chamar(
            "post", "/auth/login", json={"usuario": usuario, "senha": senha}
        )
        try:
            dados = _objeto(dados)
            return SessaoAdministrador(
                token=_texto(dados["token"], nao_vazio=True),
                usuario=_texto(dados["usuario"], nao_vazio=True),
                expira_em=_data_com_fuso(dados["expira_em"]),
            )
        except (KeyError, TypeError, ValueError) as erro:
            raise ErroFonteDados(_FORA_DO_CONTRATO) from erro

    def sair(self, sessao: SessaoAdministrador) -> None:
        self._chamar("post", "/auth/logout", sessao=sessao, esperado=(200, 204))

    def importar_dataset(
        self, sessao: SessaoAdministrador, nome_arquivo: str, conteudo: bytes
    ) -> ResultadoImportacao:
        dados = self._chamar(
            "post",
            "/datasets",
            sessao=sessao,
            esperado=(201,),
            recusa="O arquivo não está no formato esperado.",
            files={"arquivo": (nome_arquivo, conteudo, "text/csv")},
        )
        try:
            dados = _objeto(dados)
            lidos = _inteiro(dados["registros_lidos"])
            importados = _inteiro(dados["registros_importados"])
            descartados = _inteiro(dados["registros_descartados"])
            if importados + descartados != lidos:
                raise ValueError("Contagens incompatíveis.")
            motivos = _objeto(dados.get("descartes_por_motivo", {}))
            return ResultadoImportacao(
                id_dataset=_texto(dados["id_dataset"], nao_vazio=True),
                nome_arquivo=_texto(dados["nome_arquivo"], nao_vazio=True),
                registros_lidos=lidos,
                registros_importados=importados,
                registros_descartados=descartados,
                descartes_por_motivo={
                    _texto(m, nao_vazio=True): _inteiro(n) for m, n in motivos.items()
                },
            )
        except (KeyError, TypeError, ValueError) as erro:
            raise ErroFonteDados(_FORA_DO_CONTRATO) from erro

    def listar_fontes_coleta(self, sessao: SessaoAdministrador) -> list[FonteColeta]:
        dados = self._chamar("get", "/coletas/fontes", sessao=sessao)
        try:
            fontes = _objeto(dados)["fontes"]
            if not isinstance(fontes, list):
                raise TypeError("Fontes deve ser uma lista.")
            return [
                FonteColeta(
                    id=_texto(_objeto(f)["id"], nao_vazio=True),
                    nome=_texto(f["nome"], nao_vazio=True),
                )
                for f in fontes
            ]
        except (KeyError, TypeError, ValueError) as erro:
            raise ErroFonteDados(_FORA_DO_CONTRATO) from erro

    def iniciar_coleta(self, sessao: SessaoAdministrador, fonte: str) -> Coleta:
        dados = self._chamar(
            "post",
            "/coletas",
            sessao=sessao,
            esperado=(202,),
            recusa="A API recusou a fonte escolhida.",
            json={"fonte": fonte},
        )
        return self._coleta(dados)

    def pesquisar(
        self,
        sessao: SessaoAdministrador,
        termo: str,
        quantidade: int,
        complementar_com_x: bool,
    ) -> Coleta:
        dados = self._chamar(
            "post",
            "/coletas",
            sessao=sessao,
            esperado=(202,),
            recusa="A API recusou a pesquisa.",
            json={
                "fonte": FONTE_PESQUISA,
                "termo": termo,
                "quantidade": quantidade,
                "complementar_com_x": complementar_com_x,
            },
        )
        return self._coleta(dados)

    def consultar_coleta(self, sessao: SessaoAdministrador, id_coleta: str) -> Coleta:
        dados = self._chamar("get", f"/coletas/{quote(id_coleta, safe='')}", sessao=sessao)
        return self._coleta(dados)

    @staticmethod
    def _coleta(dados: Any) -> Coleta:
        try:
            return _para_coleta(dados)
        except (KeyError, TypeError, ValueError) as erro:
            raise ErroFonteDados(_FORA_DO_CONTRATO) from erro
