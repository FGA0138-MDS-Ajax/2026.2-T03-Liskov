"""Verifica a leitura dos datasets usados na comparação de modelos."""

import pytest

from scripts.comparar_modelos import ler


@pytest.mark.parametrize("conteudo", [
    # Formato SentIA com siglas nos rótulos.
    (
        "texto,rotulo,fonte\n"
        "Gostei,POS,teste\n"
        "Não gostei,NEG,teste\n"
        "Chegou hoje,NEU,teste\n"
    ),
    # Formato SentIA com o alias sentimento e nomes em português.
    (
        "texto,sentimento,fonte\n"
        "Gostei,positivo,teste\n"
        "Não gostei,negativo,teste\n"
        "Chegou hoje,neutro,teste\n"
    ),
    # Formato BPSAD: as notas são convertidas pelo importador oficial.
    (
        "review_text,rating,dataset\n"
        "Gostei,5,teste\n"
        "Não gostei,1,teste\n"
        "Chegou hoje,3,teste\n"
    ),
])
def test_leitura_padroniza_formatos(tmp_path, conteudo):
    # Cria um CSV temporário, sem alterar os datasets do projeto.
    caminho = tmp_path / "dados.csv"
    caminho.write_text(conteudo, encoding="utf-8-sig")

    textos, rotulos = ler(str(caminho))

    # Todos os formatos devem produzir os mesmos textos e rótulos,
    # preservando a ordem dos registros.
    assert textos == ["Gostei", "Não gostei", "Chegou hoje"]
    assert rotulos == ["positivo", "negativo", "neutro"]


@pytest.mark.parametrize("conteudo,mensagem", [
    (
        "texto,rotulo,fonte\nGostei,,teste\n",
        "sem rótulo",
    ),
    (
        "review_text,rating,dataset\nGostei,,teste\n",
        "rating.*vazio",
    ),
])
def test_leitura_rejeita_registro_sem_rotulo(
    tmp_path, conteudo, mensagem
):
    caminho = tmp_path / "sem_rotulo.csv"
    caminho.write_text(conteudo, encoding="utf-8")

    # Cada formato rejeita a ausência de rótulo com sua própria mensagem.
    with pytest.raises(ValueError, match=mensagem):
        ler(str(caminho))