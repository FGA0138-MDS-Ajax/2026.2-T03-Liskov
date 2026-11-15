"""Fixtures sintéticas: não acessa BPSAD completo, rede ou pesos de modelos."""
import csv
import json
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory as DiretorioTemporario

import pandas as pd
import pytest

from scripts.experimentos import amostrar_bpsad as amostragem
from scripts.experimentos.validar_bpsad import ler_amostra


@pytest.fixture
def corpus(tmp_path):
    caminho = tmp_path / "origem.csv"
    with caminho.open("w", encoding="utf-8", newline="") as arquivo:
        escritor = csv.writer(arquivo)
        # Ordem inversa à esperada pelo script original é intencional.
        escritor.writerow(["rating", "review_text"])
        for nota in (1, 3, 5):
            for i in range(20):
                escritor.writerow([nota, f"  Texto classe {nota} item {i}! 😊  "])
        escritor.writerow([1, "TEXTO CLASSE 1 ITEM 0! 😊"])
        escritor.writerow([1, "Conflitante"])
        escritor.writerow([5, "CONFLITANTE"])
        escritor.writerow([1, "conflitante"])
        escritor.writerow(["inválida", "Descartar"])
        escritor.writerow([3, "   "])
    return caminho


def test_exata_deterministica_sem_vazamento(corpus):
    a, relatorio = amostragem.amostrar(corpus, tamanho=31, tamanho_bloco=7)
    b, _ = amostragem.amostrar(corpus, tamanho=31, tamanho_bloco=19)
    pd.testing.assert_frame_equal(a, b)
    assert len(a) == 31 and a.review_text.map(amostragem.normalizar).is_unique
    assert relatorio["grupos_com_rotulos_conflitantes"] == 1
    assert relatorio["duplicatas_agrupadas"] == 3
    assert relatorio["linhas_descartadas"] == 2
    assert all("conflitante" != amostragem.normalizar(t) for t in a.review_text)
    assert all(t.startswith("  ") and t.endswith("  ") for t in a.review_text)
    treino = set(a.loc[a.divisao == "treino", "review_text"].map(amostragem.normalizar))
    teste = set(a.loc[a.divisao == "teste", "review_text"].map(amostragem.normalizar))
    assert not treino & teste
    c, _ = amostragem.amostrar(corpus, tamanho=31, semente=17)
    assert not a.equals(c)


def test_cotas_desbalanceadas_e_arredondamento():
    for tamanho in (6, 7, 11, 53):
        cotas = amostragem._cotas({"positivo": 90, "negativo": 10, "neutro": 2}, tamanho)
        assert sum(cotas.values()) == tamanho
        assert cotas["neutro"] == 2
    with pytest.raises(ValueError, match="três classes"):
        amostragem._cotas({"positivo": 99, "neutro": 1, "negativo": 2}, 30)


@pytest.mark.parametrize("tamanho", [0, 5, 1000])
def test_rejeita_tamanho_impossivel(corpus, tamanho):
    with pytest.raises(ValueError):
        amostragem.amostrar(corpus, tamanho=tamanho)


def test_arquivo_inexistente(tmp_path):
    with pytest.raises(FileNotFoundError):
        amostragem.amostrar(tmp_path / "ausente.csv")


@pytest.mark.parametrize("falha", [False, True])
def test_limpeza_e_preservacao_sqlite_preexistente(corpus, monkeypatch, falha):
    preexistente = corpus.parent / "bpsad_grupos_temp.sqlite"
    preexistente.write_bytes(b"NAO APAGAR")
    pastas = []

    def temporario(**kwargs):
        diretorio = DiretorioTemporario(dir=corpus.parent, **kwargs)
        pastas.append(Path(diretorio.name))
        return diretorio

    monkeypatch.setattr(amostragem, "TemporaryDirectory", temporario)
    if falha:
        def erro(*args, **kwargs):
            raise ValueError("Falha sintética durante leitura")
        monkeypatch.setattr(amostragem.pd, "read_csv", erro)
        with pytest.raises(ValueError, match="sintética"):
            amostragem.amostrar(corpus, tamanho=30)
    else:
        amostragem.amostrar(corpus, tamanho=30)
    assert pastas and all(not p.exists() for p in pastas)
    assert preexistente.read_bytes() == b"NAO APAGAR"


def test_cli_e_protecao_contra_sobrescrita(corpus):
    saida = corpus.parent / "amostra.csv"
    comando = [sys.executable, "-m", "scripts.experimentos.amostrar_bpsad", "--entrada",
               str(corpus), "--saida", str(saida), "--tamanho", "30"]
    sucesso = subprocess.run(comando, capture_output=True, text=True)
    assert sucesso.returncode == 0, sucesso.stderr
    assert json.loads(saida.with_suffix(".json").read_text())["amostra_total"] == 30
    original = saida.read_bytes()
    repetido = subprocess.run(comando, capture_output=True, text=True)
    assert repetido.returncode == 2 and "já existe" in repetido.stderr
    assert saida.read_bytes() == original
    treino, teste = ler_amostra(saida)
    assert len(treino) == 24 and len(teste) == 6


@pytest.mark.parametrize("campo,valor", [("rotulo", "desconhecido"), ("divisao", "validacao"),
                                          ("review_text", "")])
def test_avaliacao_rejeita_amostra_invalida(corpus, campo, valor):
    df, _ = amostragem.amostrar(corpus, tamanho=30)
    df.loc[0, campo] = valor
    saida = corpus.parent / "invalida.csv"
    df.to_csv(saida, index=False)
    with pytest.raises(ValueError):
        ler_amostra(saida)


def test_avaliacao_rejeita_duplicata_entre_particoes(corpus):
    df, _ = amostragem.amostrar(corpus, tamanho=30)
    df.loc[1, "review_text"] = df.loc[0, "review_text"].upper()
    saida = corpus.parent / "vazamento.csv"
    df.to_csv(saida, index=False)
    with pytest.raises(ValueError, match="duplicados"):
        ler_amostra(saida)


def test_avaliacao_baseline_sem_modelo_real(corpus, monkeypatch):
    from types import SimpleNamespace
    from scripts.experimentos import validar_bpsad
    executar = validar_bpsad.executar
    versao_real = validar_bpsad.version
    monkeypatch.setattr(validar_bpsad, "version", lambda nome: "simulada" if nome == "psutil" else versao_real(nome))

    # O teste obrigatório não depende do grupo opcional psutil.
    monkeypatch.setitem(sys.modules, "psutil", SimpleNamespace(
        Process=lambda: SimpleNamespace(memory_info=lambda: SimpleNamespace(rss=1024))))
    df, _ = amostragem.amostrar(corpus, tamanho=30)
    saida = corpus.parent / "validacao.csv"
    df.to_csv(saida, index=False)
    resultado = executar(saida)
    assert set(resultado["modelos"]) == {"baseline"}
    assert 0 <= resultado["modelos"]["baseline"]["acuracia"] <= 1
    assert len(resultado["sha256_amostra"]) == 64
    json.dumps(resultado)


def test_metricas_por_classe_com_ordem_padronizada():
    from src.processamento.classificacao.avaliacao import avaliar

    resultado = avaliar(
        ["positivo", "positivo", "negativo", "neutro"],
        ["positivo", "negativo", "negativo", "positivo"],
    )

    metricas = resultado["metricas_por_classe"]

    assert list(metricas) == ["positivo", "negativo", "neutro"]

    assert metricas["positivo"]["precision"] == pytest.approx(0.5)
    assert metricas["positivo"]["recall"] == pytest.approx(0.5)
    assert metricas["positivo"]["f1-score"] == pytest.approx(0.5)
    assert metricas["positivo"]["support"] == 2

    assert metricas["negativo"]["precision"] == pytest.approx(0.5)
    assert metricas["negativo"]["recall"] == pytest.approx(1.0)
    assert metricas["negativo"]["f1-score"] == pytest.approx(2 / 3)
    assert metricas["negativo"]["support"] == 1

    assert metricas["neutro"]["precision"] == pytest.approx(0.0)
    assert metricas["neutro"]["recall"] == pytest.approx(0.0)
    assert metricas["neutro"]["f1-score"] == pytest.approx(0.0)
    assert metricas["neutro"]["support"] == 1