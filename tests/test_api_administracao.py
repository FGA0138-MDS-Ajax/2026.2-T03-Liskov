"""Autenticação e rotas de administração da API (issues #58 a #61).

O classificador é substituído por um falso: estes testes verificam as rotas, não
o BERTweet. A persistência ainda é em memória (issue #20).
"""

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.apresentacao.contrato import ErroAutenticacao, ErroFonteDados
from src.apresentacao.fontes.administracao_api import AdministracaoApi
from src.servico.administracao import (
    ContextoAdministracao,
    ErroClassificadorIndisponivel,
    obter_contexto,
)
from src.servico.autenticacao import (
    Autenticador,
    ConfiguracaoAdmin,
    ErroConfiguracaoAdmin,
    GerenciadorSessoes,
    LimitadorTentativas,
    gerar_hash_senha,
    verificar_senha,
)
from src.servico.main import app

USUARIO = "admin"
SENHA = "uma-senha-de-teste"
HASH = gerar_hash_senha(SENHA)

CSV_VALIDO = (
    "texto,fonte,data\n"
    "Adorei o atendimento,teste,2026-10-01\n"
    "Não gostei do produto,teste,\n"
    '"   ",teste,2026-10-02\n'
    "Texto sem fonte,,2026-10-03\n"
).encode()


class PipelineFalso:
    def __init__(self) -> None:
        self.lotes: list[int] = []

    def processar_registros(self, registros):
        registros = list(registros)
        self.lotes.append(len(registros))
        return [{**r, "sentimento": "neutro"} for r in registros]


def _contexto(tmp_path: Path, **opcoes) -> ContextoAdministracao:
    opcoes.setdefault("criar_pipeline", PipelineFalso)
    opcoes.setdefault("caminho_tweetsentbr", tmp_path / "nao-existe.csv")
    configuracao = opcoes.pop("configuracao", ConfiguracaoAdmin(USUARIO, HASH))
    return ContextoAdministracao(Autenticador(configuracao), **opcoes)


@pytest.fixture
def contexto(tmp_path):
    return _contexto(tmp_path)


@pytest.fixture
def cliente(contexto):
    app.dependency_overrides[obter_contexto] = lambda: contexto
    with TestClient(app) as cliente:
        yield cliente
    app.dependency_overrides.clear()


def _entrar(cliente) -> dict[str, str]:
    resposta = cliente.post("/auth/login", json={"usuario": USUARIO, "senha": SENHA})
    assert resposta.status_code == 200
    return {"Authorization": f"Bearer {resposta.json()['token']}"}


def _importar(cliente, cabecalho, conteudo=CSV_VALIDO, nome="comentarios.csv"):
    return cliente.post(
        "/datasets", headers=cabecalho, files={"arquivo": (nome, conteudo, "text/csv")}
    )


# Senha e configuração


def test_hash_confere_so_com_a_senha_certa_e_nao_contem_a_senha():
    assert verificar_senha(SENHA, HASH)
    assert not verificar_senha("outra", HASH)
    assert SENHA not in HASH
    assert gerar_hash_senha(SENHA) != HASH  # sal aleatório


def test_hash_em_formato_invalido_e_recusado_sem_ser_repetido_na_mensagem():
    with pytest.raises(ErroConfiguracaoAdmin) as erro:
        ConfiguracaoAdmin(USUARIO, "texto-qualquer")
    assert "texto-qualquer" not in str(erro.value)


def test_sem_variaveis_de_ambiente_a_administracao_fica_desligada(monkeypatch):
    monkeypatch.delenv("SENTIA_ADMIN_USUARIO", raising=False)
    monkeypatch.delenv("SENTIA_ADMIN_SENHA_HASH", raising=False)
    assert ConfiguracaoAdmin.do_ambiente() is None


def test_configuracao_lida_do_ambiente(monkeypatch):
    monkeypatch.setenv("SENTIA_ADMIN_USUARIO", USUARIO)
    monkeypatch.setenv("SENTIA_ADMIN_SENHA_HASH", HASH)
    monkeypatch.setenv("SENTIA_SESSAO_MINUTOS", "15")
    assert ConfiguracaoAdmin.do_ambiente() == ConfiguracaoAdmin(USUARIO, HASH, 15)


# Login e sessão (T03)


def test_login_devolve_token_e_expiracao_com_fuso(cliente):
    resposta = cliente.post("/auth/login", json={"usuario": USUARIO, "senha": SENHA})
    assert resposta.status_code == 200
    dados = resposta.json()
    assert dados["usuario"] == USUARIO
    assert len(dados["token"]) >= 32
    expira = datetime.fromisoformat(dados["expira_em"])
    restante = expira - datetime.now(UTC)
    assert timedelta(minutes=59) < restante <= timedelta(minutes=60)


@pytest.mark.parametrize(
    "credenciais",
    [{"usuario": USUARIO, "senha": "errada"}, {"usuario": "outro", "senha": SENHA}],
)
def test_credencial_errada_tem_mensagem_que_nao_diz_qual_campo_errou(cliente, credenciais):
    resposta = cliente.post("/auth/login", json=credenciais)
    assert resposta.status_code == 401
    assert resposta.json() == {"mensagem": "Usuário ou senha inválidos."}


def test_muitas_falhas_bloqueiam_o_login_mesmo_com_a_senha_certa(cliente):
    for _ in range(5):
        cliente.post("/auth/login", json={"usuario": USUARIO, "senha": "errada"})
    resposta = cliente.post("/auth/login", json={"usuario": USUARIO, "senha": SENHA})
    assert resposta.status_code == 429


def test_bloqueio_termina_quando_a_janela_passa():
    agora = [0.0]
    limitador = LimitadorTentativas(maximo=2, janela_segundos=60, relogio=lambda: agora[0])
    limitador.registrar_falha("chave")
    limitador.registrar_falha("chave")
    assert limitador.bloqueado("chave")
    agora[0] = 61
    assert not limitador.bloqueado("chave")


def test_login_sem_configuracao_responde_503(tmp_path):
    app.dependency_overrides[obter_contexto] = lambda: _contexto(tmp_path, configuracao=None)
    try:
        resposta = TestClient(app).post(
            "/auth/login", json={"usuario": USUARIO, "senha": SENHA}
        )
    finally:
        app.dependency_overrides.clear()
    assert resposta.status_code == 503
    assert "não está configurada" in resposta.json()["mensagem"]


@pytest.mark.parametrize(
    "cabecalho", [{}, {"Authorization": "Bearer token-inventado"}, {"Authorization": "Basic x"}]
)
@pytest.mark.parametrize("metodo, rota", [("get", "/coletas/fontes"), ("post", "/auth/logout")])
def test_rotas_protegidas_recusam_quem_nao_entrou(cliente, cabecalho, metodo, rota):
    resposta = getattr(cliente, metodo)(rota, headers=cabecalho)
    assert resposta.status_code == 401
    assert resposta.headers["WWW-Authenticate"] == "Bearer"


def test_importacao_tambem_exige_login(cliente):
    assert _importar(cliente, {}).status_code == 401


def test_sair_invalida_o_token(cliente):
    cabecalho = _entrar(cliente)
    assert cliente.post("/auth/logout", headers=cabecalho).status_code == 204
    assert cliente.get("/coletas/fontes", headers=cabecalho).status_code == 401


def test_sessao_expira():
    agora = [datetime(2026, 11, 9, tzinfo=UTC)]
    sessoes = GerenciadorSessoes(relogio=lambda: agora[0])
    token, _ = sessoes.criar(USUARIO, timedelta(minutes=60))
    assert sessoes.validar(token) is not None
    agora[0] += timedelta(minutes=60)
    assert sessoes.validar(token) is None


# Importação de dataset (RF01)


def test_importa_csv_e_conta_os_descartes(cliente, contexto):
    resposta = _importar(cliente, _entrar(cliente))
    assert resposta.status_code == 201
    dados = resposta.json()
    assert dados["nome_arquivo"] == "comentarios.csv"
    assert dados["registros_importados"] == 2
    assert dados["registros_descartados"] == 2
    assert dados["registros_lidos"] == 4
    assert dados["descartes_por_motivo"] == {"texto_vazio": 1, "fonte_vazia": 1}
    assert len(contexto.repositorio.obter_dataset(dados["id_dataset"]).registros) == 2


def test_dataset_importado_vira_fonte_de_coleta(cliente):
    cabecalho = _entrar(cliente)
    dados = _importar(cliente, cabecalho).json()
    fontes = cliente.get("/coletas/fontes", headers=cabecalho).json()["fontes"]
    assert {"id": dados["id_dataset"], "nome": "Dataset importado: comentarios.csv"} in fontes


def test_arquivo_sem_extensao_csv_e_recusado(cliente):
    resposta = _importar(cliente, _entrar(cliente), nome="planilha.xlsx")
    assert resposta.status_code == 415


def test_arquivo_maior_que_o_limite_e_recusado(tmp_path):
    contexto = _contexto(tmp_path, limite_csv_bytes=10)
    app.dependency_overrides[obter_contexto] = lambda: contexto
    try:
        cliente = TestClient(app)
        resposta = _importar(cliente, _entrar(cliente))
    finally:
        app.dependency_overrides.clear()
    assert resposta.status_code == 413
    assert contexto.repositorio.listar_datasets() == []


@pytest.mark.parametrize(
    "conteudo, trecho",
    [
        (b"texto,data\nOi,2026-10-01\n", "Colunas obrigatórias ausentes: fonte"),
        (b"", "vazio"),
        ("texto,fonte\nOlá,teste\n".encode("latin-1"), "UTF-8"),
        (b"texto,fonte\n,teste\n", "não possui registros"),
    ],
)
def test_csv_invalido_tem_mensagem_clara(cliente, contexto, conteudo, trecho):
    resposta = _importar(cliente, _entrar(cliente), conteudo=conteudo)
    assert resposta.status_code == 422
    assert trecho in resposta.json()["mensagem"]
    assert contexto.repositorio.listar_datasets() == []


# Coleta e análise (RF02, UC03)


def test_coleta_analisa_todos_os_textos_do_dataset(cliente, contexto):
    cabecalho = _entrar(cliente)
    id_dataset = _importar(cliente, cabecalho).json()["id_dataset"]

    resposta = cliente.post("/coletas", headers=cabecalho, json={"fonte": id_dataset})
    assert resposta.status_code == 202
    assert resposta.json()["situacao"] == "pendente"

    # O TestClient espera a tarefa em segundo plano terminar.
    situacao = cliente.get(f"/coletas/{resposta.json()['id']}", headers=cabecalho).json()
    assert situacao["situacao"] == "concluida"
    assert situacao["textos_coletados"] == situacao["textos_analisados"] == 2
    assert situacao["mensagem"] is None
    assert len(contexto.repositorio.analises) == 2


def test_coleta_do_tweetsentbr_respeita_o_limite(tmp_path):
    caminho = tmp_path / "tweetsent.csv"
    linhas = "".join(f"tw_{i},Texto número {i},TweetSentBR\n" for i in range(50))
    caminho.write_text("id,texto,fonte\n" + linhas, encoding="utf-8")
    contexto = _contexto(tmp_path, caminho_tweetsentbr=caminho, limite_coleta=40)
    app.dependency_overrides[obter_contexto] = lambda: contexto
    try:
        cliente = TestClient(app)
        cabecalho = _entrar(cliente)
        fontes = cliente.get("/coletas/fontes", headers=cabecalho).json()["fontes"]
        assert {"id": "tweetsentbr", "nome": "TweetSentBR"} in fontes
        id_coleta = cliente.post(
            "/coletas", headers=cabecalho, json={"fonte": "tweetsentbr"}
        ).json()["id"]
        situacao = cliente.get(f"/coletas/{id_coleta}", headers=cabecalho).json()
    finally:
        app.dependency_overrides.clear()
    assert situacao["situacao"] == "concluida"
    assert situacao["textos_analisados"] == 40
    assert contexto.pipeline().lotes == [32, 8]


def test_tweetsentbr_some_da_lista_sem_o_arquivo(cliente):
    fontes = cliente.get("/coletas/fontes", headers=_entrar(cliente)).json()["fontes"]
    assert all(f["id"] != "tweetsentbr" for f in fontes)


def test_fonte_desconhecida_e_recusada(cliente):
    resposta = cliente.post(
        "/coletas", headers=_entrar(cliente), json={"fonte": "inventada"}
    )
    assert resposta.status_code == 422
    assert resposta.json() == {"mensagem": "Fonte de coleta desconhecida."}


def _falhar_coleta(tmp_path, criar_pipeline) -> dict:
    contexto = _contexto(tmp_path, criar_pipeline=criar_pipeline)
    app.dependency_overrides[obter_contexto] = lambda: contexto
    try:
        cliente = TestClient(app)
        cabecalho = _entrar(cliente)
        id_dataset = _importar(cliente, cabecalho).json()["id_dataset"]
        id_coleta = cliente.post(
            "/coletas", headers=cabecalho, json={"fonte": id_dataset}
        ).json()["id"]
        return cliente.get(f"/coletas/{id_coleta}", headers=cabecalho).json()
    finally:
        app.dependency_overrides.clear()


def test_coleta_falha_com_mensagem_simples_sem_o_classificador(tmp_path):
    def sem_classificador():
        raise ErroClassificadorIndisponivel

    situacao = _falhar_coleta(tmp_path, sem_classificador)
    assert situacao["situacao"] == "falhou"
    assert situacao["mensagem"] == (
        "O classificador de sentimentos não está instalado neste servidor."
    )


def test_erro_na_analise_marca_a_coleta_como_falha_sem_derrubar_a_api(tmp_path):
    class PipelineQuebrado:
        def processar_registros(self, registros):
            raise RuntimeError("detalhe interno")

    situacao = _falhar_coleta(tmp_path, PipelineQuebrado)
    assert situacao["situacao"] == "falhou"
    assert situacao["textos_analisados"] == 0
    assert "detalhe interno" not in situacao["mensagem"]


def test_coleta_inexistente_responde_404_com_mensagem(cliente):
    resposta = cliente.get("/coletas/col_x", headers=_entrar(cliente))
    assert resposta.status_code == 404
    assert resposta.json() == {"mensagem": "Coleta não encontrada."}


# Painel e API juntos: o cliente do painel conversa com as rotas reais.


@pytest.fixture
def painel(cliente):
    return AdministracaoApi("http://testserver", sessao=cliente)


def test_painel_faz_o_fluxo_completo_na_api_real(painel):
    sessao = painel.entrar(USUARIO, SENHA)
    assert not sessao.expirada()

    resultado = painel.importar_dataset(sessao, "comentarios.csv", CSV_VALIDO)
    assert resultado.registros_importados == 2
    assert resultado.descartes_por_motivo == {"texto_vazio": 1, "fonte_vazia": 1}

    fontes = painel.listar_fontes_coleta(sessao)
    assert [f.id for f in fontes] == [resultado.id_dataset]

    coleta = painel.iniciar_coleta(sessao, resultado.id_dataset)
    coleta = painel.consultar_coleta(sessao, coleta.id)
    assert coleta.situacao == "concluida"
    assert coleta.textos_analisados == 2

    painel.sair(sessao)
    with pytest.raises(ErroAutenticacao, match="sessão expirou"):
        painel.listar_fontes_coleta(sessao)


def test_painel_mostra_as_mensagens_da_api(painel):
    with pytest.raises(ErroAutenticacao, match="Usuário ou senha inválidos"):
        painel.entrar(USUARIO, "errada")
    sessao = painel.entrar(USUARIO, SENHA)
    with pytest.raises(ErroFonteDados, match="Colunas obrigatórias ausentes"):
        painel.importar_dataset(sessao, "a.csv", b"texto\nOi\n")
    with pytest.raises(ErroFonteDados, match="Coleta não encontrada"):
        painel.consultar_coleta(sessao, "col_x")
