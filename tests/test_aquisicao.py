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

from src.processamento.aquisicao import (
    CAMINHO_PADRAO_TWEETSENTBR,
    RelatorioImportacao,
    carregar_tweetsentbr,
    converter_rotulo_para_sentia,
    iterar_bpsad,
    iterar_dados_aquisicao,
    iterar_tweetsentbr,
    normalizar_rotulo,
    resolver_caminho_tweetsentbr,
)

CARACTERES_PT_BR_OBRIGATORIOS: tuple[str, ...] = ("ç", "ã", "é", "í")


def _extrair_identificador(registro: dict[str, Any]) -> Any:
    """Extrai o identificador de um registro priorizando 'id_origem'."""
    if "id_origem" in registro:
        return registro["id_origem"]
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
        texto = registro.get("texto_original")
        assert isinstance(texto, str) and texto.strip(), (
            f"O registro na posição {indice} deve conter o campo 'texto_original' preenchido."
        )
        assert "sentimento" not in registro, (
            "O campo 'sentimento' pertence à classificação ML e não deve ser retornado na aquisição."
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

    textos_concatenados = " ".join(str(r.get("texto_original", "")) for r in resultado)
    for caractere in CARACTERES_PT_BR_OBRIGATORIOS:
        assert caractere in textos_concatenados, (
            f"Caractere brasileiro '{caractere}' não foi preservado na aquisição dos textos."
        )

    for esperado, obtido in zip(registros_esperados_valido, resultado):
        id_obtido = _extrair_identificador(obtido)
        assert id_obtido == esperado["id_origem"], (
            f"Identificador do registro foi alterado: esperado '{esperado['id_origem']}', obtido '{id_obtido}'."
        )
        assert obtido.get("texto_original") == esperado["texto_original"], (
            f"Texto original do registro '{esperado['id_origem']}' não foi preservado integralmente."
        )
        assert obtido.get("fonte") == esperado["fonte"], (
            f"Metadado 'fonte' ausente ou incorreto no registro '{esperado['id_origem']}': "
            f"esperado '{esperado['fonte']}', obtido '{obtido.get('fonte')}'."
        )
        if esperado["rotulo_padronizado"] is not None:
            assert obtido.get("rotulo_padronizado") == esperado["rotulo_padronizado"], (
                f"Metadado 'rotulo_padronizado' divergente no registro '{esperado['id_origem']}'."
            )
        if esperado["data_publicacao"] is not None:
            assert obtido.get("data_publicacao") == esperado["data_publicacao"], (
                f"Metadado 'data_publicacao' divergente no registro '{esperado['id_origem']}': "
                f"esperado '{esperado['data_publicacao']}', obtido '{obtido.get('data_publicacao')}'."
            )
        else:
            assert obtido.get("data_publicacao") in (None, ""), (
                f"Registro '{esperado['id_origem']}' sem data na origem deve manter 'data_publicacao' vazia ou None."
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


def test_aquisicao_caminho_padrao_independente_do_diretorio_atual(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    adquirir_dados: Callable[..., list[dict[str, Any]]],
) -> None:
    """Verifica que o carregamento padrão do TweetSentBR funciona fora da raiz do projeto."""
    monkeypatch.chdir(tmp_path)

    caminho_resolvido = resolver_caminho_tweetsentbr()
    assert caminho_resolvido == CAMINHO_PADRAO_TWEETSENTBR.resolve()
    assert caminho_resolvido.is_file()

    amostra_padrao = adquirir_dados(limite=5)
    assert len(amostra_padrao) == 5
    for registro in amostra_padrao:
        assert registro["fonte"] == "TweetSentBR"
        assert registro["rotulo_padronizado"] in ("POS", "NEG", "NEU")
        assert "sentimento" not in registro

    amostra_relativa_canonica = carregar_tweetsentbr(
        "Datasets/tweetsent.csv",
        limite=3,
    )
    amostra_relativa_minuscula = carregar_tweetsentbr(
        "datasets/tweetsent.csv",
        limite=3,
    )
    assert amostra_relativa_canonica == amostra_relativa_minuscula


def test_aquisicao_processamento_iterativo_e_limite(
    arquivo_csv_valido: Path,
) -> None:
    """Verifica o processamento iterativo em fluxo com e sem limite."""
    relatorio = RelatorioImportacao()
    parcial = list(
        iterar_tweetsentbr(
            arquivo_csv_valido,
            relatorio=relatorio,
            limite=2,
        )
    )
    assert len(parcial) == 2
    assert relatorio.total_importados == 2

    completo = list(iterar_dados_aquisicao(arquivo_csv_valido))
    assert len(completo) == 5


@pytest.mark.parametrize(
    "limite_invalido,excecao_esperada",
    [
        (0, ValueError),
        (-3, ValueError),
        (True, TypeError),
        ("10", TypeError),
    ],
)
def test_aquisicao_rejeita_limite_invalido(
    arquivo_csv_valido: Path,
    limite_invalido: Any,
    excecao_esperada: type[Exception],
) -> None:
    """Verifica validação estrita do parâmetro opcional limite."""
    with pytest.raises(excecao_esperada):
        carregar_tweetsentbr(arquivo_csv_valido, limite=limite_invalido)


def test_aquisicao_rejeita_tipo_caminho_invalido(
    adquirir_dados: Callable[..., list[dict[str, Any]]],
) -> None:
    """Verifica que tipos não textuais para caminho levantam TypeError."""
    with pytest.raises(TypeError):
        adquirir_dados(12345)


def test_aquisicao_rejeita_diretorio_relativo_a_raiz(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verifica que caminho relativo apontando para diretório na raiz levanta IsADirectoryError."""
    monkeypatch.chdir(tmp_path)
    with pytest.raises(IsADirectoryError):
        resolver_caminho_tweetsentbr("Datasets")


def test_aquisicao_preserva_acentuacao_emojis_estabilidade_id_e_rotulos(
    tmp_path: Path,
    adquirir_dados: Callable[..., list[dict[str, Any]]],
) -> None:
    """Verifica acentuação, emojis, estabilidade de IDs determinísticos e contrato de rótulos."""
    arquivo_tweets = tmp_path / "tweets_emojis.csv"
    arquivo_tweets.write_text(
        "texto,rotulo,fonte,split\n"
        '"Sensação incrível na estréia do programa! 😍🔥🇧🇷",positivo,TweetSentBR,test\n'
        '"Não gostei da edição de hoje 😡👎",negativo,TweetSentBR,test\n'
        '"O episódio começou às 22h na televisão 📺",neutro,TweetSentBR,test\n',
        encoding="utf-8",
    )

    primeira_leitura = adquirir_dados(arquivo_tweets)
    segunda_leitura = carregar_tweetsentbr(arquivo_tweets)

    assert primeira_leitura == segunda_leitura
    assert [r["rotulo_padronizado"] for r in primeira_leitura] == [
        "POS",
        "NEG",
        "NEU",
    ]
    assert [
        converter_rotulo_para_sentia(r["rotulo_padronizado"])
        for r in primeira_leitura
    ] == ["positivo", "negativo", "neutro"]
    assert "😍🔥🇧🇷" in primeira_leitura[0]["texto_original"]
    assert primeira_leitura[0]["metadados"] == {"split": "test"}
    for registro in primeira_leitura:
        assert normalizar_rotulo(registro["rotulo_original"]) == registro["rotulo_padronizado"]
        assert "sentimento" not in registro


def test_aquisicao_erro_encoding_invalido(
    tmp_path: Path,
    adquirir_dados: Callable[..., list[dict[str, Any]]],
) -> None:
    """Verifica erro compreensível quando o arquivo não está em UTF-8."""
    arquivo_latin1 = tmp_path / "tweets_latin1.csv"
    arquivo_latin1.write_bytes(
        "texto,rotulo,fonte\nAvaliação ótima,positivo,TweetSentBR\n".encode(
            "latin-1"
        )
    )
    with pytest.raises(ValueError, match="UTF-8"):
        adquirir_dados(arquivo_latin1)


def test_aquisicao_amostra_sintetica_bpsad(
    arquivo_bpsad_sample: Path,
    adquirir_dados: Callable[..., list[dict[str, Any]]],
) -> None:
    """Verifica que a fixture sintética do BPSAD é carregada pelo adaptador e pela aquisição."""
    registros = adquirir_dados(arquivo_bpsad_sample)
    registros_bpsad = list(iterar_bpsad(arquivo_bpsad_sample))

    assert len(registros) == 5
    assert registros == registros_bpsad
    assert [r["rotulo_padronizado"] for r in registros] == [
        "POS",
        "POS",
        "NEU",
        "NEG",
        "NEG",
    ]
    assert [r["id_origem"] for r in registros] == [
        "bpsad_syn_001",
        "bpsad_syn_002",
        "bpsad_syn_003",
        "bpsad_syn_004",
        "bpsad_syn_005",
    ]
