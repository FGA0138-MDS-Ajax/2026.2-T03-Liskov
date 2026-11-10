"""Conectividade e CLI sem MongoDB, credenciais reais ou acesso à rede."""

import runpy
import subprocess
import sys
import traceback
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from pymongo.errors import (
    ConfigurationError,
    ConnectionFailure,
    OperationFailure,
    ServerSelectionTimeoutError,
)

import test_mongo as script
from src.dados import database

URI_TESTE = "mongodb://127.0.0.1:27017/sentia_teste"
SEGREDO_SINTETICO = "CREDENCIAL_FICTICIA_NAO_PUBLICAR_NA_SAIDA"
URI_SIGILOSA = f"mongodb://usuario_ficticio:{SEGREDO_SINTETICO}@cluster.exemplo.invalid/sentia"
RAIZ = Path(__file__).resolve().parents[1]


@pytest.fixture(autouse=True)
def sem_configuracao_externa(monkeypatch):
    monkeypatch.delenv("MONGODB_URI", raising=False)
    monkeypatch.setattr(database, "load_dotenv", Mock())
    fabrica = Mock()
    monkeypatch.setattr(database, "MongoClient", fabrica)
    return fabrica


def test_import_nao_cria_cliente_nem_le_dotenv():
    with patch("pymongo.MongoClient") as fabrica, patch("dotenv.load_dotenv") as dotenv:
        runpy.run_path(database.__file__)
    fabrica.assert_not_called()
    dotenv.assert_not_called()


@pytest.mark.parametrize("uri", [None, "", "   ", 123])
def test_uri_ausente_ou_vazia_falha_antes_do_cliente(uri, sem_configuracao_externa):
    with pytest.raises(database.ErroConfiguracaoMongoDB, match="MONGODB_URI"):
        database.connect_to_mongodb(uri)
    sem_configuracao_externa.assert_not_called()


@pytest.mark.parametrize(
    "uri", [URI_TESTE, "mongodb+srv://cluster.exemplo.invalid/sentia"]
)
def test_uri_local_ou_atlas_e_timeout_chegam_a_fabrica_sem_rede(uri):
    fabrica = Mock()
    cliente = database.connect_to_mongodb(uri, timeout_ms=1234, client_factory=fabrica)
    fabrica.assert_called_once_with(
        uri, serverSelectionTimeoutMS=1234, connectTimeoutMS=1234, socketTimeoutMS=1234
    )
    assert cliente is fabrica.return_value
    cliente.admin.command.assert_called_once_with("ping")
    cliente.close.assert_not_called()
    database.disconnect_from_mongodb(cliente)
    cliente.close.assert_called_once()


def test_uri_do_ambiente(monkeypatch, sem_configuracao_externa):
    monkeypatch.setenv("MONGODB_URI", URI_TESTE)
    database.connect_to_mongodb()
    assert sem_configuracao_externa.call_args.args == (URI_TESTE,)


def test_dotenv_real_sem_sobrescrever_variavel_do_ambiente(
    tmp_path, monkeypatch, sem_configuracao_externa
):
    from dotenv import load_dotenv

    caminho = tmp_path / ".env"
    caminho.write_text(f"MONGODB_URI={URI_TESTE}\n", encoding="utf-8")
    monkeypatch.setattr(database, "load_dotenv", lambda: load_dotenv(caminho))
    database.connect_to_mongodb()
    assert sem_configuracao_externa.call_args.args == (URI_TESTE,)
    monkeypatch.setenv("MONGODB_URI", "mongodb://127.0.0.1:27017/outro_teste")
    database.connect_to_mongodb()
    assert sem_configuracao_externa.call_args.args == (
        "mongodb://127.0.0.1:27017/outro_teste",
    )


@pytest.mark.parametrize("timeout", [0, -1, True, "5", 0.5, float("inf"), float("nan")])
def test_timeout_invalido_nao_cria_cliente(timeout, sem_configuracao_externa):
    with pytest.raises(database.ErroConfiguracaoMongoDB, match="timeout"):
        database.connect_to_mongodb(URI_TESTE, timeout_ms=timeout)
    sem_configuracao_externa.assert_not_called()


@pytest.mark.parametrize("erro", [ConfigurationError, ValueError, RuntimeError])
def test_falha_no_construtor_e_sanitizada(erro, sem_configuracao_externa, capsys):
    sem_configuracao_externa.side_effect = erro(URI_SIGILOSA)
    with pytest.raises(
        (database.ErroConfiguracaoMongoDB, database.ErroConexaoMongoDB)
    ) as capturada:
        database.connect_to_mongodb(URI_SIGILOSA)
    assert SEGREDO_SINTETICO not in str(capturada.value)
    saida = "".join(traceback.format_exception(capturada.value))
    assert SEGREDO_SINTETICO not in saida
    assert URI_SIGILOSA not in saida
    assert capsys.readouterr() == ("", "")


@pytest.mark.parametrize(
    "erro",
    [ConnectionFailure, ServerSelectionTimeoutError, OperationFailure, RuntimeError],
)
def test_ping_falha_fecha_cliente_e_nao_expoe_segredo(erro, sem_configuracao_externa):
    cliente = sem_configuracao_externa.return_value
    cliente.admin.command.side_effect = erro(URI_SIGILOSA)
    with pytest.raises(database.ErroConexaoMongoDB) as capturada:
        database.connect_to_mongodb(URI_TESTE)
    cliente.close.assert_called_once()
    assert SEGREDO_SINTETICO not in str(capturada.value)
    assert URI_SIGILOSA not in str(capturada.value)


def test_falha_no_close_nao_mascara_erro_do_ping(sem_configuracao_externa):
    cliente = sem_configuracao_externa.return_value
    cliente.admin.command.side_effect = ConnectionFailure(SEGREDO_SINTETICO)
    cliente.close.side_effect = RuntimeError(SEGREDO_SINTETICO)
    with pytest.raises(database.ErroConexaoMongoDB, match="rede e timeout"):
        database.connect_to_mongodb(URI_TESTE)
    cliente.close.assert_called_once()


def test_chamadas_independentes_nao_reutilizam_cliente_fechado(
    sem_configuracao_externa,
):
    primeiro, segundo = Mock(), Mock()
    sem_configuracao_externa.side_effect = [primeiro, segundo]
    assert database.connect_to_mongodb(URI_TESTE) is primeiro
    database.disconnect_from_mongodb(primeiro)
    assert database.connect_to_mongodb(URI_TESTE) is segundo
    segundo.admin.command.assert_called_once_with("ping")


def test_script_sucesso_retorna_zero_e_fecha(
    monkeypatch, sem_configuracao_externa, capsys
):
    monkeypatch.setenv("MONGODB_URI", URI_TESTE)
    assert script.main() == 0
    sem_configuracao_externa.return_value.close.assert_called_once()
    saida = capsys.readouterr()
    assert "Sucesso" in saida.out
    assert saida.err == ""


def test_script_sem_uri_retorna_erro_sem_criar_cliente(
    sem_configuracao_externa, capsys
):
    assert script.main() != 0
    sem_configuracao_externa.assert_not_called()
    assert "MONGODB_URI" in capsys.readouterr().err


@pytest.mark.parametrize(
    "erro",
    [
        ConfigurationError,
        ConnectionFailure,
        OperationFailure,
        ServerSelectionTimeoutError,
    ],
)
def test_script_falha_no_ping_retorna_erro_e_fecha(
    erro, monkeypatch, sem_configuracao_externa, capsys
):
    monkeypatch.setenv("MONGODB_URI", URI_TESTE)
    cliente = sem_configuracao_externa.return_value
    cliente.admin.command.side_effect = erro(SEGREDO_SINTETICO)
    assert script.main() != 0
    cliente.close.assert_called_once()
    saida = capsys.readouterr()
    assert "Teste falhou" in saida.err
    assert SEGREDO_SINTETICO not in saida.err + saida.out
    assert "Sucesso" not in saida.out


def test_script_falha_no_close_retorna_erro_seguro(
    monkeypatch, sem_configuracao_externa, capsys
):
    monkeypatch.setenv("MONGODB_URI", URI_TESTE)
    sem_configuracao_externa.return_value.close.side_effect = RuntimeError(
        SEGREDO_SINTETICO
    )
    assert script.main() != 0
    sem_configuracao_externa.return_value.close.assert_called_once()
    saida = capsys.readouterr()
    assert SEGREDO_SINTETICO not in saida.err
    assert "Sucesso" not in saida.out


def test_script_excecao_inesperada_tem_exit_code_e_mensagem_segura(monkeypatch, capsys):
    monkeypatch.setattr(
        script, "connect_to_mongodb", Mock(side_effect=RuntimeError(SEGREDO_SINTETICO))
    )
    assert script.main() != 0
    assert SEGREDO_SINTETICO not in capsys.readouterr().err


@pytest.mark.parametrize("falha", [False, True])
def test_entrypoint_real_em_subprocesso_tem_codigo_correto_e_fecha(falha):
    codigo = """
import os, runpy, sys
from unittest.mock import Mock, patch
from pymongo.errors import ConnectionFailure
os.environ['MONGODB_URI'] = 'mongodb://127.0.0.1:27017/sentia_teste'
cliente = Mock()
cliente.close.side_effect = lambda: print('CLIENTE_FECHADO')
if sys.argv[1] == 'falha':
    cliente.admin.command.side_effect = ConnectionFailure('CREDENCIAL_FICTICIA_NAO_PUBLICAR_NA_SAIDA')
with patch('dotenv.load_dotenv'), patch('src.dados.database.MongoClient', return_value=cliente):
    runpy.run_path('test_mongo.py', run_name='__main__')
"""
    resultado = subprocess.run(
        [sys.executable, "-c", codigo, "falha" if falha else "sucesso"],
        cwd=RAIZ,
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    assert resultado.returncode == (1 if falha else 0)
    assert resultado.stdout.count("CLIENTE_FECHADO") == 1
    assert SEGREDO_SINTETICO not in resultado.stdout + resultado.stderr
