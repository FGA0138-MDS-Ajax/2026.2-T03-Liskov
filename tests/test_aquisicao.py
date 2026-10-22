"""Testes automatizados para o módulo de aquisição de dados (RF02 / US02 — Issue #1).

Cobre os cenários obrigatórios definidos na Issue #4:
- Leitura bem-sucedida da fonte inicial (TweetSentBR controlado).
- Fonte ou arquivo inexistente.
- Fonte indisponível (simulada localmente sem dependência de rede).
- Entrada sem registros válidos (arquivo vazio, apenas cabeçalho, textos em branco).
- Preservação dos textos originais em português brasileiro e metadados necessários.
- Tratamento de erros previsíveis para entradas ou formatos inválidos.

Nota de escopo:
Estes testes validam a camada de aquisição de dados (unidade/contrato).
Não substituem os testes integrados de ponta a ponta T01/T02 da interface administrativa.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

import pytest

CARACTERES_PT_BR_OBRIGATORIOS: tuple[str, ...] = ("ç", "ã", "é", "í")


def _extrair_identificador(registro: dict[str, Any]) -> Any:
    """Extrai o identificador de um registro aceitando 'id' ou 'identificador'."""
    if "id" in registro:
        return registro["id"]
    if "identificador" in registro:
        return registro["identificador"]
    return None


def test_aquisicao_leitura_fonte_inicial_sucesso(
    arquivo_csv_valido: Path,
    registros_esperados_valido: list[dict[str, Any]],
    adquirir_dados: Callable[..., list[dict[str, Any]]],
) -> None:
    """Verifica se a leitura da fonte inicial retorna os registros válidos esperados."""
    resultado = adquirir_dados(arquivo_csv_valido)

    assert isinstance(resultado, list), (
        f"A função de aquisição deve retornar uma lista, mas retornou {type(resultado).__name__}."
    )
    assert len(resultado) == len(registros_esperados_valido), (
        f"Esperava {len(registros_esperados_valido)} registros da fonte inicial, "
        f"mas foram retornados {len(resultado)}."
    )
    for indice, registro in enumerate(resultado):
        assert isinstance(registro, dict), (
            f"O registro na posição {indice} deve ser um dict, mas é {type(registro).__name__}."
        )
        assert isinstance(registro.get("texto"), str) and registro["texto"].strip(), (
            f"O registro na posição {indice} deve conter o campo 'texto' preenchido."
        )


def test_aquisicao_preservacao_textos_e_metadados(
    arquivo_csv_valido: Path,
    registros_esperados_valido: list[dict[str, Any]],
    adquirir_dados: Callable[..., list[dict[str, Any]]],
) -> None:
    """Verifica a preservação integral dos textos em PT-BR e dos metadados da fonte inicial."""
    resultado = adquirir_dados(arquivo_csv_valido)

    assert len(resultado) == len(registros_esperados_valido), (
        "Quantidade de registros adquiridos diverge da fixture de referência."
    )

    textos_concatenados = " ".join(str(r.get("texto", "")) for r in resultado)
    for caractere in CARACTERES_PT_BR_OBRIGATORIOS:
        assert caractere in textos_concatenados, (
            f"Caractere brasileiro '{caractere}' não foi preservado na aquisição dos textos."
        )

    for esperado, obtido in zip(registros_esperados_valido, resultado):
        id_obtido = _extrair_identificador(obtido)
        assert id_obtido == esperado["id"], (
            f"Identificador do registro foi alterado: esperado '{esperado['id']}', obtido '{id_obtido}'."
        )
        assert obtido.get("texto") == esperado["texto"], (
            f"Texto original do registro '{esperado['id']}' não foi preservado integralmente."
        )
        assert obtido.get("fonte") == esperado["fonte"], (
            f"Metadado 'fonte' ausente ou incorreto no registro '{esperado['id']}': "
            f"esperado '{esperado['fonte']}', obtido '{obtido.get('fonte')}'."
        )
        if esperado["sentimento"] is not None:
            assert obtido.get("sentimento") == esperado["sentimento"], (
                f"Metadado 'sentimento' divergente no registro '{esperado['id']}'."
            )
        if esperado["data"] is not None:
            assert obtido.get("data") == esperado["data"], (
                f"Metadado 'data' divergente no registro '{esperado['id']}': "
                f"esperado '{esperado['data']}', obtido '{obtido.get('data')}'."
            )
        else:
            assert obtido.get("data") in (None, ""), (
                f"Registro '{esperado['id']}' sem data na origem deve manter 'data' vazia ou None."
            )


@pytest.mark.parametrize(
    "caminho_inexistente",
    [
        "arquivo_que_nao_existe.csv",
        "subpasta_inexistente/tweetsentbr.csv",
        "dados/fonte_ausente.tsv",
    ],
    ids=[
        "arquivo_local_inexistente",
        "subdiretorio_inexistente",
        "caminho_relativo_ausente",
    ],
)
def test_aquisicao_fonte_ou_arquivo_inexistente(
    tmp_path: Path,
    caminho_inexistente: str,
    adquirir_dados: Callable[..., list[dict[str, Any]]],
) -> None:
    """Verifica que caminho ou fonte inexistente levanta erro claro e previsível."""
    alvo = tmp_path / caminho_inexistente

    with pytest.raises((FileNotFoundError, ValueError)) as exc_info:
        adquirir_dados(alvo)

    mensagem = str(exc_info.value).strip()
    assert len(mensagem) > 0, (
        "A exceção para fonte ou arquivo inexistente deve conter uma mensagem explicativa."
    )


def test_aquisicao_fonte_indisponivel_diretorio_no_lugar_de_arquivo(
    tmp_path: Path,
    adquirir_dados: Callable[..., list[dict[str, Any]]],
) -> None:
    """Verifica falha controlada quando a origem aponta para um diretório e não um arquivo."""
    diretorio_origem = tmp_path / "diretorio_sem_arquivo"
    diretorio_origem.mkdir()

    with pytest.raises((OSError, ValueError, RuntimeError)) as exc_info:
        adquirir_dados(diretorio_origem)

    assert str(exc_info.value).strip(), (
        "A falha por fonte indisponível (diretório inválido) deve fornecer mensagem clara."
    )


def test_aquisicao_fonte_indisponivel_erro_permissao_leitura(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    adquirir_dados: Callable[..., list[dict[str, Any]]],
) -> None:
    """Verifica o tratamento quando a fonte está indisponível por falha de permissão/IO local."""
    arquivo_bloqueado = tmp_path / "fonte_indisponivel.csv"
    arquivo_bloqueado.write_text(
        "id,texto,sentimento,fonte,data\ntw_001,Texto de teste,positivo,TweetSentBR,2026-10-01\n",
        encoding="utf-8",
    )

    def _simular_falha_abertura(*args: Any, **kwargs: Any) -> Any:
        raise PermissionError("Fonte temporariamente indisponível: permissão negada.")

    monkeypatch.setattr(Path, "open", _simular_falha_abertura)
    monkeypatch.setattr("builtins.open", _simular_falha_abertura)

    with pytest.raises((PermissionError, OSError, ConnectionError, RuntimeError, ValueError)) as exc_info:
        adquirir_dados(arquivo_bloqueado)

    assert str(exc_info.value).strip(), (
        "Erro de indisponibilidade da fonte deve apresentar mensagem compreensível."
    )


@pytest.mark.parametrize(
    "tipo_entrada_vazia",
    [
        "arquivo_zero_bytes",
        "apenas_cabecalho",
        "apenas_textos_em_branco",
    ],
)
def test_aquisicao_entrada_sem_registros_validos(
    tipo_entrada_vazia: str,
    arquivo_csv_vazio: Path,
    arquivo_csv_apenas_cabecalho: Path,
    arquivo_csv_registros_em_branco: Path,
    adquirir_dados: Callable[..., list[dict[str, Any]]],
) -> None:
    """Verifica que entradas vazias ou sem registros textuais válidos são rejeitadas."""
    mapa_arquivos = {
        "arquivo_zero_bytes": arquivo_csv_vazio,
        "apenas_cabecalho": arquivo_csv_apenas_cabecalho,
        "apenas_textos_em_branco": arquivo_csv_registros_em_branco,
    }
    arquivo_alvo = mapa_arquivos[tipo_entrada_vazia]

    with pytest.raises(ValueError) as exc_info:
        adquirir_dados(arquivo_alvo)

    assert str(exc_info.value).strip(), (
        f"Entrada sem registros válidos ({tipo_entrada_vazia}) deve gerar ValueError com mensagem clara."
    )


@pytest.mark.parametrize(
    "origem_invalida,excecoes_esperadas",
    [
        (None, (ValueError, TypeError)),
        ("", (ValueError, FileNotFoundError)),
        ("   ", (ValueError, FileNotFoundError)),
    ],
    ids=[
        "origem_none",
        "origem_string_vazia",
        "origem_apenas_espacos",
    ],
)
def test_aquisicao_tratamento_erros_previsiveis_parametros_invalidos(
    origem_invalida: Any,
    excecoes_esperadas: tuple[type[Exception], ...],
    adquirir_dados: Callable[..., list[dict[str, Any]]],
) -> None:
    """Verifica tratamento de erros previsíveis para parâmetros de origem inválidos."""
    with pytest.raises(excecoes_esperadas) as exc_info:
        adquirir_dados(origem_invalida)

    assert str(exc_info.value).strip(), (
        "Parâmetro de origem inválido deve produzir exceção com mensagem explicativa."
    )


def test_aquisicao_tratamento_erros_previsiveis_esquema_incompativel(
    arquivo_csv_invalido: Path,
    adquirir_dados: Callable[..., list[dict[str, Any]]],
) -> None:
    """Verifica que fonte sem os campos mínimos esperados (ex.: sem 'texto') gera ValueError."""
    with pytest.raises(ValueError) as exc_info:
        adquirir_dados(arquivo_csv_invalido)

    assert str(exc_info.value).strip(), (
        "Fonte com esquema incompatível deve ser rejeitada com mensagem de erro clara."
    )
