import pytest

from src.processamento.aquisicao.csv_importer import (
    normalizar_rotulo,
    importar_dataset_csv
)


@pytest.mark.parametrize(
    "entrada, esperado",
    [
        ("1", "NEG"),
        ("2", "NEG"),
        ("3", "NEU"),
        ("4", "POS"),
        ("5", "POS"),
        ("2.3", "NEG"),
        ("2.5", "NEU"),
        ("3.2", "NEU"),
        ("3.5", "POS"),
        ("4.8", "POS"),
        ("negativo", "NEG"),
        ("neutro", "NEU"),
        ("positivo", "POS"),
        ("negative", "NEG"),
        ("neutral", "NEU"),
        ("positive", "POS"),
    ]
)
def test_normalizar_rotulo(entrada, esperado):
    assert normalizar_rotulo(entrada) == esperado


def test_rotulo_invalido():
    with pytest.raises(ValueError):
        normalizar_rotulo("excelente")


def test_importar_csv_valido(tmp_path):
    arquivo = tmp_path / "dataset.csv"

    arquivo.write_text(
        'id,texto,rotulo,fonte\n'
        '123,"Produto horrível",1,BPSAD\n'
        '456,"Produto razoável",3,BPSAD\n'
        '789,"Produto excelente",5,BPSAD\n',
        encoding="utf-8"
    )

    registros = importar_dataset_csv(arquivo)

    assert len(registros) == 3

    assert registros[0]["rotulo_padronizado"] == "NEG"
    assert registros[1]["rotulo_padronizado"] == "NEU"
    assert registros[2]["rotulo_padronizado"] == "POS"

    assert registros[0]["texto_original"] == "Produto horrível"
    assert registros[0]["rotulo_original"] == "1"
    assert registros[0]["fonte"] == "BPSAD"

    # O ID original não deve ser utilizado.
    assert registros[0]["id"] != "123"
    assert registros[0]["id"].startswith("BPSAD_")


def test_ids_diferentes_em_importacoes_separadas(tmp_path):
    arquivo = tmp_path / "dataset.csv"

    arquivo.write_text(
        "texto,rotulo,fonte\n"
        "Muito bom,5,TweetSentBR\n",
        encoding="utf-8"
    )

    primeira_importacao = importar_dataset_csv(arquivo)
    segunda_importacao = importar_dataset_csv(arquivo)

    assert (
        primeira_importacao[0]["id"]
        != segunda_importacao[0]["id"]
    )


def test_coluna_obrigatoria_ausente(tmp_path):
    arquivo = tmp_path / "dataset.csv"

    arquivo.write_text(
        "texto,rotulo\n"
        "Muito bom,5\n",
        encoding="utf-8"
    )

    with pytest.raises(ValueError, match="Colunas obrigatórias ausentes"):
        importar_dataset_csv(arquivo)


def test_campo_obrigatorio_vazio(tmp_path):
    arquivo = tmp_path / "dataset.csv"

    arquivo.write_text(
        "texto,rotulo,fonte\n"
        ",5,BPSAD\n",
        encoding="utf-8"
    )

    with pytest.raises(ValueError, match="não podem estar vazios"):
        importar_dataset_csv(arquivo)


def test_rotulo_invalido_no_csv(tmp_path):
    arquivo = tmp_path / "dataset.csv"

    arquivo.write_text(
        "texto,rotulo,fonte\n"
        "Texto de teste,excelente,BPSAD\n",
        encoding="utf-8"
    )

    with pytest.raises(ValueError, match="Rótulo inválido"):
        importar_dataset_csv(arquivo)


def test_csv_com_ponto_e_virgula(tmp_path):
    arquivo = tmp_path / "dataset.csv"

    arquivo.write_text(
        "texto;rotulo;fonte\n"
        "Muito bom;5;BPSAD\n",
        encoding="utf-8"
    )

    registros = importar_dataset_csv(
        arquivo,
        delimitador=";"
    )

    assert len(registros) == 1
    assert registros[0]["rotulo_padronizado"] == "POS"


def test_csv_sem_registros(tmp_path):
    arquivo = tmp_path / "dataset.csv"

    arquivo.write_text(
        "texto,rotulo,fonte\n",
        encoding="utf-8"
    )

    with pytest.raises(ValueError, match="não possui registros"):
        importar_dataset_csv(arquivo)
        
def test_nota_fora_do_intervalo():
    with pytest.raises(ValueError):
        normalizar_rotulo("5.5")

    with pytest.raises(ValueError):
        normalizar_rotulo("0.5")