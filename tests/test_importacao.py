"""Testes automatizados para o módulo de importação de datasets CSV (RF01 / US01 — Issue #2).

Cobre os cenários obrigatórios definidos na Issue #4:
- Importação de um CSV válido.
- CSV vazio ou sem registros.
- CSV com colunas obrigatórias ausentes.
- CSV com caracteres brasileiros, como ``ç``, ``ã``, ``é`` e ``í``.
- Preservação dos campos mínimos e dos metadados.
- Arquivo com estrutura ou formato inválido.

Nota de escopo:
Estes testes validam a rotina de importação CSV consumível pelo pipeline (Sprint 1).
Não correspondem aos testes de aceitação T01/T02 completos da interface administrativa.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

import pytest

from src.processamento.aquisicao import converter_rotulo_para_sentia

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


def test_importacao_csv_valido_sucesso(
    arquivo_csv_valido: Path,
    registros_esperados_valido: list[dict[str, Any]],
    importar_csv: Callable[..., list[dict[str, Any]]],
) -> None:
    """Verifica que um CSV válido é importado com sucesso para uma lista padronizada de registros."""
    registros = importar_csv(arquivo_csv_valido)

    assert isinstance(registros, list), (
        f"A importação de CSV deve retornar uma lista, mas retornou {type(registros).__name__}."
    )
    assert len(registros) == len(registros_esperados_valido), (
        f"Esperava importar {len(registros_esperados_valido)} registros, "
        f"mas foram retornados {len(registros)}."
    )
    for indice, item in enumerate(registros):
        assert isinstance(item, dict), (
            f"Cada registro importado deve ser um dicionário (índice {indice}: {type(item).__name__})."
        )
        assert "sentimento" not in item, (
            "O campo 'sentimento' é reservado à classificação do modelo e não deve ser gerado na importação."
        )


def test_importacao_csv_preservacao_campos_minimos_e_metadados(
    arquivo_csv_valido: Path,
    registros_esperados_valido: list[dict[str, Any]],
    importar_csv: Callable[..., list[dict[str, Any]]],
) -> None:
    """Verifica a preservação dos campos do contrato (id_origem, texto_original, fonte, rotulo_original, rotulo_padronizado, data_publicacao)."""
    registros = importar_csv(arquivo_csv_valido)

    assert len(registros) == len(registros_esperados_valido), (
        "Total de registros importados diverge do esperado para dataset_valido.csv."
    )

    for esperado, obtido in zip(registros_esperados_valido, registros):
        id_obtido = _extrair_identificador(obtido)
        assert id_obtido == esperado["id_origem"], (
            f"Campo identificador não preservado: esperado '{esperado['id_origem']}', obtido '{id_obtido}'."
        )
        assert obtido.get("texto_original") == esperado["texto_original"], (
            f"Campo 'texto_original' do registro '{esperado['id_origem']}' foi alterado na importação."
        )
        assert obtido.get("fonte") == esperado["fonte"], (
            f"Metadado 'fonte' do registro '{esperado['id_origem']}' não foi preservado: "
            f"esperado '{esperado['fonte']}', obtido '{obtido.get('fonte')}'."
        )
        assert obtido.get("rotulo_original") == esperado["rotulo_original"], (
            f"Campo 'rotulo_original' do registro '{esperado['id_origem']}' não foi preservado: "
            f"esperado '{esperado['rotulo_original']}', obtido '{obtido.get('rotulo_original')}'."
        )
        assert obtido.get("rotulo_padronizado") == esperado["rotulo_padronizado"], (
            f"Campo 'rotulo_padronizado' do registro '{esperado['id_origem']}' diverge do padrão POS/NEG/NEU: "
            f"esperado '{esperado['rotulo_padronizado']}', obtido '{obtido.get('rotulo_padronizado')}'."
        )
        assert "sentimento" not in obtido, (
            f"Registro '{esperado['id_origem']}' não deve conter chave 'sentimento' na etapa de importação."
        )
        if esperado["data_publicacao"] is not None:
            assert obtido.get("data_publicacao") == esperado["data_publicacao"], (
                f"Metadado 'data_publicacao' do registro '{esperado['id_origem']}' não foi preservado: "
                f"esperado '{esperado['data_publicacao']}', obtido '{obtido.get('data_publicacao')}'."
            )
        else:
            assert obtido.get("data_publicacao") is None, (
                f"Registro '{esperado['id_origem']}' sem data no CSV deve resultar em None."
            )


def test_importacao_csv_campos_id_rotulo_e_data_opcionais(
    tmp_path: Path,
    importar_csv: Callable[..., list[dict[str, Any]]],
) -> None:
    """Verifica que apenas texto e fonte são obrigatórios; id, rótulo e data são opcionais."""
    arquivo_minimo = tmp_path / "dataset_minimo_sem_opcionais.csv"
    arquivo_minimo.write_text(
        "texto,fonte\n"
        '"Comentário real ainda sem rótulo e sem ID explícito",ColetaExterna\n',
        encoding="utf-8",
    )

    registros = importar_csv(arquivo_minimo)
    assert len(registros) == 1
    registro = registros[0]
    assert registro["id_origem"].startswith("ColetaExterna_000001_")
    assert registro["texto_original"] == "Comentário real ainda sem rótulo e sem ID explícito"
    assert registro["fonte"] == "ColetaExterna"
    assert registro["rotulo_original"] is None
    assert registro["rotulo_padronizado"] is None
    assert registro["data_publicacao"] is None
    assert "sentimento" not in registro


def test_importacao_conversao_fronteira_rotulo_para_avaliacao_e_mongodb(
    arquivo_csv_valido: Path,
    registros_esperados_valido: list[dict[str, Any]],
    importar_csv: Callable[..., list[dict[str, Any]]],
) -> None:
    """Verifica a conversão explícita de POS/NEG/NEU para positivo/negativo/neutro na fronteira."""
    registros = importar_csv(arquivo_csv_valido)
    rotulos_convertidos = [
        converter_rotulo_para_sentia(r["rotulo_padronizado"]) for r in registros
    ]
    assert rotulos_convertidos == [
        esperado["rotulo_original"] for esperado in registros_esperados_valido
    ]


@pytest.mark.parametrize(
    "id_registro,texto_pt_br,caractere_foco",
    [
        (
            "br_01",
            "A solução apresentada pela equipe de programação superou a expectativa.",
            "ç",
        ),
        (
            "br_02",
            "A opinião dos cidadãos sobre a aplicação não sofreu alteração.",
            "ã",
        ),
        (
            "br_03",
            "O método de análise léxica é útil, mas o modelo estatístico é superior.",
            "é",
        ),
        (
            "br_04",
            "O índice de ruído nos textos extraídos do sítio foi baixíssimo.",
            "í",
        ),
        (
            "br_05",
            "Avaliação conjunta: ç, ã, é, í, õ, ê, á, ú, ô e à preservados sem corrupção!",
            "ç",
        ),
    ],
    ids=[
        "cedilha_c",
        "til_a",
        "acento_agudo_e",
        "acento_agudo_i",
        "combinacao_acentuacao_pt_br",
    ],
)
def test_importacao_csv_caracteres_brasileiros(
    tmp_path: Path,
    id_registro: str,
    texto_pt_br: str,
    caractere_foco: str,
    importar_csv: Callable[..., list[dict[str, Any]]],
) -> None:
    """Verifica que caracteres do português brasileiro (ç, ã, é, í) são importados sem corrupção."""
    arquivo_pt_br = tmp_path / f"dataset_{id_registro}.csv"
    conteudo = (
        "id,texto,sentimento,fonte,data\n"
        f'{id_registro},"{texto_pt_br}",positivo,TweetSentBR,2026-10-10\n'
    )
    arquivo_pt_br.write_text(conteudo, encoding="utf-8")

    registros = importar_csv(arquivo_pt_br)

    assert len(registros) == 1, "Deveria importar exatamente 1 registro do CSV de teste em PT-BR."
    texto_importado = registros[0].get("texto_original", "")
    assert texto_importado == texto_pt_br, (
        f"Texto com acentuação brasileira foi corrompido: esperado '{texto_pt_br}', "
        f"obtido '{texto_importado}'."
    )
    assert caractere_foco in texto_importado, (
        f"O caractere obrigatório '{caractere_foco}' não foi encontrado no texto importado."
    )
    assert registros[0]["rotulo_padronizado"] == "POS"


def test_importacao_fixture_valida_contem_todos_caracteres_brasileiros_obrigatorios(
    arquivo_csv_valido: Path,
    importar_csv: Callable[..., list[dict[str, Any]]],
) -> None:
    """Verifica que a importação de dataset_valido.csv preserva simultaneamente ç, ã, é e í."""
    registros = importar_csv(arquivo_csv_valido)
    todos_os_textos = " ".join(str(r.get("texto_original", "")) for r in registros)

    for caractere in CARACTERES_PT_BR_OBRIGATORIOS:
        assert caractere in todos_os_textos, (
            f"O caractere brasileiro obrigatório '{caractere}' foi perdido ao importar dataset_valido.csv."
        )


@pytest.mark.parametrize(
    "cenario_vazio",
    [
        "csv_zero_bytes",
        "csv_apenas_cabecalho",
        "csv_apenas_linhas_em_branco",
    ],
)
def test_importacao_csv_vazio_ou_sem_registros(
    cenario_vazio: str,
    arquivo_csv_vazio: Path,
    arquivo_csv_apenas_cabecalho: Path,
    arquivo_csv_registros_em_branco: Path,
    importar_csv: Callable[..., list[dict[str, Any]]],
) -> None:
    """Verifica que CSV vazio (0 bytes), só com cabeçalho ou sem textos válidos é rejeitado."""
    arquivos = {
        "csv_zero_bytes": arquivo_csv_vazio,
        "csv_apenas_cabecalho": arquivo_csv_apenas_cabecalho,
        "csv_apenas_linhas_em_branco": arquivo_csv_registros_em_branco,
    }
    alvo = arquivos[cenario_vazio]

    with pytest.raises(ValueError) as exc_info:
        importar_csv(alvo)

    assert str(exc_info.value).strip(), (
        f"A rejeição de '{cenario_vazio}' deve lançar ValueError com mensagem descritiva."
    )


@pytest.mark.parametrize(
    "cabecalho_invalido,linha_exemplo",
    [
        ("codigo,autor,categoria", "101,usuario_a,esporte"),
        ("id,sentimento,fonte,data", "tw_001,positivo,TweetSentBR,2026-10-01"),
        ("comentario,polaridade", '"Texto sem coluna padrao",positivo'),
    ],
    ids=[
        "colunas_totalmente_desconhecidas",
        "ausencia_coluna_obrigatoria_texto",
        "nomes_colunas_fora_do_contrato",
    ],
)
def test_importacao_csv_colunas_obrigatorias_ausentes(
    tmp_path: Path,
    cabecalho_invalido: str,
    linha_exemplo: str,
    importar_csv: Callable[..., list[dict[str, Any]]],
) -> None:
    """Verifica que arquivos CSV sem as colunas obrigatórias do esquema são rejeitados."""
    arquivo_sem_colunas = tmp_path / "sem_colunas_obrigatorias.csv"
    arquivo_sem_colunas.write_text(
        f"{cabecalho_invalido}\n{linha_exemplo}\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError) as exc_info:
        importar_csv(arquivo_sem_colunas)

    assert str(exc_info.value).strip(), (
        "CSV com colunas obrigatórias ausentes deve ser rejeitado com mensagem clara."
    )


def test_importacao_fixture_dataset_invalido_rejeitado(
    arquivo_csv_invalido: Path,
    importar_csv: Callable[..., list[dict[str, Any]]],
) -> None:
    """Verifica que a fixture controlada dataset_invalido.csv é rejeitada pela importação."""
    with pytest.raises(ValueError) as exc_info:
        importar_csv(arquivo_csv_invalido)

    assert str(exc_info.value).strip(), (
        "A fixture dataset_invalido.csv deve ser rejeitada com ValueError e mensagem clara."
    )


@pytest.mark.parametrize(
    "nome_arquivo,conteudo_bytes,excecoes_aceitas",
    [
        (
            "estrutura_json_nao_csv.csv",
            b'{"registros": [{"id": 1, "texto": "Isto e JSON, nao CSV"}]}',
            (ValueError,),
        ),
        (
            "binario_invalido.csv",
            b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\xff\xfe\xfd",
            (ValueError, UnicodeDecodeError),
        ),
        (
            "colunas_desalinhadas.csv",
            (
                "id,texto,sentimento,fonte,data\n"
                'tw_001,"Aspas abertas sem fechamento,positivo,TweetSentBR,2026-10-01\n'
            ).encode("utf-8"),
            (ValueError,),
        ),
    ],
    ids=[
        "conteudo_json_em_vez_de_csv",
        "arquivo_binario_corrompido",
        "csv_com_aspas_e_estrutura_quebrada",
    ],
)
def test_importacao_csv_estrutura_ou_formato_invalido(
    tmp_path: Path,
    nome_arquivo: str,
    conteudo_bytes: bytes,
    excecoes_aceitas: tuple[type[Exception], ...],
    importar_csv: Callable[..., list[dict[str, Any]]],
) -> None:
    """Verifica a rejeição de arquivos com estrutura corrompida, binária ou formato inválido."""
    arquivo_invalido = tmp_path / nome_arquivo
    arquivo_invalido.write_bytes(conteudo_bytes)

    with pytest.raises(excecoes_aceitas) as exc_info:
        importar_csv(arquivo_invalido)

    assert str(exc_info.value).strip(), (
        f"Arquivo com estrutura/formato inválido ({nome_arquivo}) deve produzir erro com mensagem clara."
    )
