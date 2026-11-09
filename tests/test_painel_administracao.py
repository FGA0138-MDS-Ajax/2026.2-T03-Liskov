"""Administração com login (T01 a T03), no modo de exemplo e com respostas HTTP simuladas.

Estes testes verificam as telas e o tratamento de erros do cliente. A integração com
as rotas reais está em tests/test_api_administracao.py.
"""

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
import requests
from streamlit.testing.v1 import AppTest

from src.apresentacao.contrato import (
    ErroAutenticacao,
    ErroFonteDados,
    SessaoAdministrador,
)
from src.apresentacao.fontes.administracao_api import AdministracaoApi
from src.apresentacao.fontes.administracao_mock import (
    SENHA_EXEMPLO,
    USUARIO_EXEMPLO,
    AdministracaoMock,
    AdministracaoMockComErro,
)
from src.apresentacao.fontes.mock import ANALISES_DE_EXEMPLO

FIXTURES = Path(__file__).resolve().parent / "fixtures"


def sessao_valida() -> SessaoAdministrador:
    return AdministracaoMock().entrar(USUARIO_EXEMPLO, SENHA_EXEMPLO)


# --- Modo de exemplo ----------------------------------------------------------


def test_mock_recusa_credencial_errada():
    with pytest.raises(ErroAutenticacao, match="Usuário ou senha inválidos"):
        AdministracaoMock().entrar(USUARIO_EXEMPLO, "errada")


def test_token_nao_aparece_na_representacao_da_sessao():
    assert "token-de-exemplo" not in repr(sessao_valida())


def test_mock_recusa_sessao_expirada():
    expirada = SessaoAdministrador(
        token=sessao_valida().token,
        usuario=USUARIO_EXEMPLO,
        expira_em=datetime.now(UTC) - timedelta(seconds=1),
    )
    with pytest.raises(ErroAutenticacao, match="sessão expirou"):
        AdministracaoMock().listar_fontes_coleta(expirada)


def test_mock_importa_csv_valido_dos_fixtures():
    conteudo = (FIXTURES / "dataset_valido.csv").read_bytes()
    linhas = len(conteudo.decode("utf-8-sig").strip().splitlines()) - 1
    resultado = AdministracaoMock().importar_dataset(
        sessao_valida(), "dataset_valido.csv", conteudo
    )
    assert resultado.registros_lidos == linhas
    assert resultado.registros_importados + resultado.registros_descartados == linhas


@pytest.mark.parametrize(
    ("conteudo", "mensagem"),
    [
        ((FIXTURES / "dataset_invalido.csv").read_bytes(), "colunas"),
        (b"texto,fonte\n", "registros"),
        (b"texto,fonte\n,origem\n", "registros"),
        ("texto,fonte\nolá,x\n".encode("latin-1"), "UTF-8"),
    ],
)
def test_mock_recusa_csv_invalido_com_mensagem_clara(conteudo, mensagem):
    with pytest.raises(ErroFonteDados, match=mensagem):
        AdministracaoMock().importar_dataset(sessao_valida(), "arquivo.csv", conteudo)


def test_mock_conta_descartes_por_motivo():
    resultado = AdministracaoMock().importar_dataset(
        sessao_valida(), "a.csv", b"texto,fonte\nbom,x\n,x\nruim,\n"
    )
    assert resultado.registros_importados == 1
    assert resultado.descartes_por_motivo == {"texto_vazio": 1, "fonte_vazia": 1}


def test_mock_recusa_fonte_desconhecida():
    with pytest.raises(ErroFonteDados, match="desconhecida"):
        AdministracaoMock().iniciar_coleta(sessao_valida(), "rede_inexistente")


# --- Cliente HTTP (respostas simuladas) ---------------------------------------


class RespostaFalsa:
    def __init__(self, status_code=200, corpo=None):
        self.status_code = status_code
        self._corpo = corpo

    def json(self):
        if self._corpo is None:
            raise ValueError("corpo não é JSON")
        return self._corpo


class SessaoHttpFalsa:
    def __init__(self, resposta=None, excecao=None):
        self.resposta = resposta
        self.excecao = excecao
        self.chamadas = []

    def _registrar(self, metodo, url, **kwargs):
        self.chamadas.append({"metodo": metodo, "url": url, **kwargs})
        if self.excecao is not None:
            raise self.excecao
        return self.resposta

    def get(self, url, **kwargs):
        return self._registrar("get", url, **kwargs)

    def post(self, url, **kwargs):
        return self._registrar("post", url, **kwargs)


def cliente(status=200, corpo=None, excecao=None):
    http = SessaoHttpFalsa(RespostaFalsa(status, corpo), excecao)
    return AdministracaoApi("http://api", timeout_segundos=3, sessao=http), http


SESSAO_API = SessaoAdministrador(
    token="abc", usuario="admin", expira_em=datetime(2030, 1, 1, tzinfo=UTC)
)
COLETA_JSON = {"id": "c1", "fonte": "tweetsentbr", "situacao": "em_andamento"}


def test_login_envia_credenciais_e_le_a_sessao():
    api, http = cliente(
        corpo={"token": "abc", "usuario": "admin", "expira_em": "2030-01-01T00:00:00Z"}
    )
    sessao = api.entrar("admin", "s3nha")
    assert http.chamadas[0]["url"] == "http://api/auth/login"
    assert http.chamadas[0]["json"] == {"usuario": "admin", "senha": "s3nha"}
    assert http.chamadas[0]["headers"] == {}
    assert sessao.expira_em == datetime(2030, 1, 1, tzinfo=UTC)


def test_login_com_401_informa_credencial_invalida():
    api, _ = cliente(status=401)
    with pytest.raises(ErroAutenticacao, match="Usuário ou senha inválidos"):
        api.entrar("admin", "errada")


@pytest.mark.parametrize(
    "corpo",
    [
        {"token": "", "usuario": "admin", "expira_em": "2030-01-01T00:00:00Z"},
        {"token": "abc", "usuario": "admin", "expira_em": "2030-01-01T00:00:00"},
        {"token": "abc", "usuario": "admin"},
    ],
)
def test_login_fora_do_contrato_vira_erro_claro(corpo):
    api, _ = cliente(corpo=corpo)
    with pytest.raises(ErroFonteDados, match="não segue o contrato"):
        api.entrar("admin", "s3nha")


def test_rotas_protegidas_enviam_o_token_e_401_expira_a_sessao():
    api, http = cliente(status=401)
    with pytest.raises(ErroAutenticacao, match="sessão expirou"):
        api.listar_fontes_coleta(SESSAO_API)
    assert http.chamadas[0]["headers"] == {"Authorization": "Bearer abc"}


def test_403_informa_falta_de_permissao():
    api, _ = cliente(status=403)
    with pytest.raises(ErroAutenticacao, match="permissão"):
        api.listar_fontes_coleta(SESSAO_API)


def test_importacao_envia_o_arquivo_e_le_o_relatorio():
    api, http = cliente(
        status=201,
        corpo={
            "id_dataset": "ds1",
            "nome_arquivo": "a.csv",
            "registros_lidos": 3,
            "registros_importados": 2,
            "registros_descartados": 1,
            "descartes_por_motivo": {"texto_vazio": 1},
        },
    )
    resultado = api.importar_dataset(SESSAO_API, "a.csv", b"texto,fonte\n")
    assert http.chamadas[0]["url"] == "http://api/datasets"
    assert http.chamadas[0]["files"] == {"arquivo": ("a.csv", b"texto,fonte\n", "text/csv")}
    assert resultado.descartes_por_motivo == {"texto_vazio": 1}


def test_importacao_com_contagens_incoerentes_vira_erro():
    api, _ = cliente(
        status=201,
        corpo={
            "id_dataset": "ds1",
            "nome_arquivo": "a.csv",
            "registros_lidos": 3,
            "registros_importados": 3,
            "registros_descartados": 1,
        },
    )
    with pytest.raises(ErroFonteDados, match="não segue o contrato"):
        api.importar_dataset(SESSAO_API, "a.csv", b"")


@pytest.mark.parametrize(
    ("status", "corpo", "mensagem"),
    [
        (422, {"mensagem": "Coluna fonte ausente."}, "Coluna fonte ausente."),
        (422, {"mensagem": "x" * 301}, "não está no formato esperado"),
        (400, None, "não está no formato esperado"),
        (413, None, "maior que o limite"),
        (500, None, "HTTP 500"),
    ],
)
def test_erros_da_importacao_viram_mensagens_para_o_usuario(status, corpo, mensagem):
    api, _ = cliente(status=status, corpo=corpo)
    with pytest.raises(ErroFonteDados, match=mensagem):
        api.importar_dataset(SESSAO_API, "a.csv", b"")


def test_coleta_e_iniciada_com_202_e_consultada_pelo_id():
    api, http = cliente(status=202, corpo=COLETA_JSON)
    assert api.iniciar_coleta(SESSAO_API, "tweetsentbr").situacao == "em_andamento"
    assert http.chamadas[0]["json"] == {"fonte": "tweetsentbr"}

    api, http = cliente(corpo={**COLETA_JSON, "id": "a/b", "situacao": "concluida"})
    api.consultar_coleta(SESSAO_API, "a/b")
    assert http.chamadas[0]["url"] == "http://api/coletas/a%2Fb"


@pytest.mark.parametrize(
    "corpo",
    [
        {**COLETA_JSON, "situacao": "pausada"},
        {**COLETA_JSON, "textos_coletados": 1, "textos_analisados": 2},
        {**COLETA_JSON, "textos_coletados": True},
        {"fonte": "tweetsentbr", "situacao": "concluida"},
    ],
)
def test_coleta_fora_do_contrato_vira_erro(corpo):
    api, _ = cliente(corpo=corpo)
    with pytest.raises(ErroFonteDados, match="não segue o contrato"):
        api.consultar_coleta(SESSAO_API, "c1")


def test_logout_aceita_204_sem_corpo():
    api, http = cliente(status=204)
    assert api.sair(SESSAO_API) is None
    assert http.chamadas[0]["url"] == "http://api/auth/logout"


@pytest.mark.parametrize(
    ("excecao", "mensagem"),
    [
        (requests.Timeout(), "demorou demais"),
        (requests.ConnectionError(), "Não foi possível conectar"),
    ],
)
def test_falhas_de_rede_viram_mensagens_claras(excecao, mensagem):
    api, _ = cliente(excecao=excecao)
    with pytest.raises(ErroFonteDados, match=mensagem):
        api.entrar("admin", "s3nha")


# --- Telas --------------------------------------------------------------------


def _pagina_admin():
    from src.apresentacao.paginas.administracao import renderizar

    renderizar()


@pytest.fixture
def ambiente(monkeypatch):
    def configurar(fonte="mock", cenario="normal", url="http://127.0.0.1:9"):
        monkeypatch.setenv("SENTIA_FONTE_DADOS", fonte)
        monkeypatch.setenv("SENTIA_MOCK_CENARIO", cenario)
        monkeypatch.setenv("SENTIA_API_URL", url)
        monkeypatch.setenv("SENTIA_API_TIMEOUT_SEGUNDOS", "5")
        return AppTest.from_function(_pagina_admin, default_timeout=10)

    return configurar


def entrar(app: AppTest, usuario=USUARIO_EXEMPLO, senha=SENHA_EXEMPLO) -> AppTest:
    app.run()
    app.text_input(key="login_usuario").input(usuario)
    app.text_input(key="login_senha").input(senha)
    return app.button(key="entrar").click().run()


def test_sem_login_so_aparece_o_formulario_de_entrada(ambiente):
    app = ambiente().run()
    assert app.subheader[0].value == "Entrar como administrador"
    assert not [b for b in app.button if b.key in ("iniciar_coleta", "importar")]


def test_login_valido_libera_as_ferramentas_do_administrador(ambiente):
    app = entrar(ambiente())
    assert not app.exception
    assert app.subheader[0].value == "Administração"
    assert "admin" in app.caption[0].value
    assert app.session_state["sessao_admin"].usuario == USUARIO_EXEMPLO


@pytest.mark.parametrize(
    ("usuario", "senha", "mensagem"),
    [
        (USUARIO_EXEMPLO, "errada", "Usuário ou senha inválidos."),
        ("", "", "Informe o usuário e a senha."),
    ],
)
def test_login_recusado_mostra_mensagem_e_nao_libera_acesso(ambiente, usuario, senha, mensagem):
    app = entrar(ambiente(), usuario, senha)
    assert app.error[0].value == mensagem
    assert "sessao_admin" not in app.session_state


def test_login_com_api_indisponivel_mostra_erro(ambiente):
    app = entrar(ambiente(fonte="api"))
    assert "Não foi possível conectar" in app.error[0].value


def test_login_no_cenario_de_erro_mostra_a_falha_simulada(ambiente):
    app = entrar(ambiente(cenario="erro"))
    assert app.error[0].value == AdministracaoMockComErro.MENSAGEM


def test_coleta_iniciada_e_acompanhada_ate_concluir(ambiente):
    app = entrar(ambiente())
    app.button(key="iniciar_coleta").click().run()
    assert "em andamento" in app.info[0].value
    app.button(key="atualizar_coleta").click().run()
    assert f"{len(ANALISES_DE_EXEMPLO)} texto(s) analisado(s)" in app.success[0].value


def test_importar_sem_arquivo_pede_um_csv(ambiente):
    app = entrar(ambiente())
    app.button(key="importar").click().run()
    assert app.error[0].value == "Escolha um arquivo CSV."


def test_sair_encerra_a_sessao_e_volta_ao_login(ambiente):
    app = entrar(ambiente())
    app.button(key="sair").click().run()
    assert "sessao_admin" not in app.session_state
    assert app.subheader[0].value == "Entrar como administrador"
    assert app.warning[0].value == "Você saiu da administração."


def test_sessao_expirada_volta_ao_login_com_aviso(ambiente):
    app = ambiente()
    app.session_state["sessao_admin"] = SessaoAdministrador(
        token="token-de-exemplo",
        usuario=USUARIO_EXEMPLO,
        expira_em=datetime.now(UTC) - timedelta(minutes=1),
    )
    app.run()
    assert app.subheader[0].value == "Entrar como administrador"
    assert "sessão expirou" in app.warning[0].value
