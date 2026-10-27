from types import SimpleNamespace

import pytest

from classificacao import baseline
from classificacao.bertweet import ClassificadorBertweet
from classificacao.rotulos import normalizar_rotulo


class AnalisadorFalso:
    """Imita o analisador do pysentimiento sem baixar o modelo."""

    def predict(self, textos):
        saida = []
        for t in textos:
            if "bom" in t:
                saida.append(SimpleNamespace(output="POS", probas={"POS": 0.9, "NEG": 0.05, "NEU": 0.05}))
            elif "ruim" in t:
                saida.append(SimpleNamespace(output="NEG", probas={"POS": 0.05, "NEG": 0.9, "NEU": 0.05}))
            else:
                saida.append(SimpleNamespace(output="NEU", probas={"POS": 0.1, "NEG": 0.1, "NEU": 0.8}))
        return saida


def test_normalizar_rotulo():
    assert normalizar_rotulo("POS") == "positivo"
    assert normalizar_rotulo("Negativo") == "negativo"
    with pytest.raises(ValueError):
        normalizar_rotulo("talvez")


def test_bertweet_mapeia_rotulos_e_respeita_lotes():
    clf = ClassificadorBertweet(analisador=AnalisadorFalso(), tamanho_lote=2)
    textos = ["muito bom", "muito ruim", "ok", "bom demais", "ruim demais"]
    assert clf.prever(textos) == ["positivo", "negativo", "neutro", "positivo", "negativo"]
    r = clf.prever_com_probabilidades(["muito bom"])[0]
    assert set(r["probabilidades"]) == {"positivo", "negativo", "neutro"}


def test_bertweet_aceita_texto_unico_e_lista_vazia():
    clf = ClassificadorBertweet(analisador=AnalisadorFalso())
    assert clf.prever("muito bom") == ["positivo"]
    assert clf.prever([]) == []


@pytest.mark.parametrize("tamanho_lote", [0, -1])
def test_bertweet_rejeita_lote_invalido(tamanho_lote):
    with pytest.raises(ValueError, match="maior que zero"):
        ClassificadorBertweet(analisador=AnalisadorFalso(), tamanho_lote=tamanho_lote)


@pytest.mark.parametrize("texto", ["", "   "])
def test_bertweet_rejeita_texto_vazio(texto):
    clf = ClassificadorBertweet(analisador=AnalisadorFalso())
    with pytest.raises(ValueError, match="não pode ser vazio"):
        clf.prever(texto)


def test_bertweet_rejeita_entrada_que_nao_seja_texto():
    clf = ClassificadorBertweet(analisador=AnalisadorFalso())
    with pytest.raises(TypeError, match="deve ser uma string"):
        clf.prever(["texto", None])


def test_baseline_treina_e_preve_somente_rotulos_validos(tmp_path):
    x = ["otimo produto", "adorei o produto", "pessimo produto", "odiei o produto", "produto comum", "produto normal"] * 3
    y = ["positivo", "positivo", "negativo", "negativo", "neutro", "neutro"] * 3
    modelo = baseline.criar_baseline().fit(x, y)
    pred = modelo.predict(["adorei", "pessimo"])
    assert set(pred) <= {"positivo", "negativo", "neutro"}
    baseline.salvar(modelo, tmp_path / "m.pkl")
    assert baseline.carregar(tmp_path / "m.pkl").predict(["otimo"]).shape == (1,)
