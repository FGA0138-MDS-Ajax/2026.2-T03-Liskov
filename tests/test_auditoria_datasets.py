"""Testes da auditoria reprodutível de datasets (Issues #3 e #4)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.processamento.aquisicao.auditoria_datasets import (
    auditar_dataset_csv,
    calcular_sha256_arquivo,
    detectar_codificacao_utf8,
    main,
)


def test_auditoria_tweetsentbr_metricas_reais() -> None:
    """Verifica as métricas reais e o hash SHA-256 do corpus Datasets/tweetsent.csv."""
    relatorio = auditar_dataset_csv()

    assert relatorio.nome_arquivo == "tweetsent.csv"
    assert (
        relatorio.sha256
        == "8b7be5d0a6bb982c99bf0613ac71f9f8eed49849586a5019b2db2094a6136060"
    )
    assert relatorio.tamanho_bytes == 861743
    assert relatorio.codificacao == "UTF-8-SIG"
    assert relatorio.colunas == ["texto", "rotulo", "fonte"]
    assert relatorio.possui_coluna_id_original is False
    assert relatorio.possui_coluna_data is False
    assert relatorio.possui_coluna_split is False

    assert relatorio.total_lidos == 8530
    assert relatorio.total_importados == 8530
    assert relatorio.total_descartados == 0
    assert relatorio.contagem_por_classe == {
        "POS": 3953,
        "NEG": 2403,
        "NEU": 2174,
    }
    assert relatorio.proporcao_por_classe == {
        "POS": 46.34,
        "NEG": 28.17,
        "NEU": 25.49,
    }
    assert relatorio.datas_preenchidas == 0

    assert relatorio.duplicatas_exatas.textos_unicos == 8495
    assert relatorio.duplicatas_exatas.grupos_duplicados == 21
    assert relatorio.duplicatas_exatas.ocorrencias_excedentes == 35
    assert relatorio.duplicatas_exatas.registros_envolvidos == 56
    assert relatorio.duplicatas_exatas.grupos_conflitantes == 5

    assert relatorio.duplicatas_normalizadas.textos_unicos == 8481
    assert relatorio.duplicatas_normalizadas.grupos_duplicados == 30
    assert relatorio.duplicatas_normalizadas.ocorrencias_excedentes == 49
    assert relatorio.duplicatas_normalizadas.registros_envolvidos == 79
    assert relatorio.duplicatas_normalizadas.grupos_conflitantes == 12


def test_auditoria_bpsad_sample_e_cli(
    arquivo_bpsad_sample: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Verifica a auditoria sobre a amostra BPSAD e a saída JSON da CLI."""
    codigo = main([str(arquivo_bpsad_sample)])
    assert codigo == 0

    saida = capsys.readouterr().out
    dados = json.loads(saida)

    assert dados["nome_arquivo"] == "bpsad_sample.csv"
    assert dados["codificacao"] == "UTF-8"
    assert dados["possui_coluna_id_original"] is True
    assert dados["possui_coluna_data"] is True
    assert dados["total_lidos"] == 5
    assert dados["total_importados"] == 5
    assert dados["total_descartados"] == 0
    assert dados["datas_preenchidas"] == 5
    assert dados["contagem_por_classe"] == {"POS": 2, "NEU": 1, "NEG": 2}


def test_auditoria_modo_sem_duplicatas_e_descartes_tolerantes(
    tmp_path: Path,
) -> None:
    """Verifica modo --sem-duplicatas e contabilização de descartes em arquivos grandes."""
    csv_misto = tmp_path / "bpsad_misto.csv"
    csv_misto.write_text(
        "review_text,rating,dataset\n"
        '"Produto excelente",5,b2w\n'
        '"",1,b2w\n'
        '"Produto ruim",1,buscape\n',
        encoding="utf-8",
    )

    relatorio = auditar_dataset_csv(csv_misto, rastrear_duplicatas=False)
    assert relatorio.total_lidos == 3
    assert relatorio.total_importados == 2
    assert relatorio.total_descartados == 1
    assert relatorio.descartes_por_motivo == {"texto_vazio": 1}
    assert relatorio.duplicatas_exatas.textos_unicos == 0
    assert calcular_sha256_arquivo(csv_misto) == relatorio.sha256
    assert detectar_codificacao_utf8(csv_misto) == "UTF-8"
