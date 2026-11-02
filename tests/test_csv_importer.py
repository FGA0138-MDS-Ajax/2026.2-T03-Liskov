from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest

from src.processamento.aquisicao import (
    ROTULOS_PADRONIZADOS,
    RelatorioImportacao,
    adquirir_dados,
    importar_csv,
    importar_dataset_csv,
    iterar_bpsad,
    iterar_dataset_csv,
    normalizar_rotulo,
)

CAMPOS_OBRIGATORIOS_CONTRATO = {
    "id_origem",
    "texto_original",
    "fonte",
    "rotulo_original",
    "data_publicacao",
}


# ============================================================================
# 1 a 4. Rótulos numéricos (1 a 5), rótulos textuais e CSV padrão válido
# ============================================================================


@pytest.mark.parametrize(
    "entrada, esperado",
    [
        ("1", "negativo"),
        ("2", "negativo"),
        ("3", "neutro"),
        ("4", "positivo"),
        ("5", "positivo"),
        ("2.3", "negativo"),
        ("2.5", "neutro"),
        ("3.2", "neutro"),
        ("3.5", "positivo"),
        ("4.8", "positivo"),
        (1, "negativo"),
        (3, "neutro"),
        (5, "positivo"),
        ("negativo", "negativo"),
        ("neutro", "neutro"),
        ("positivo", "positivo"),
        ("negative", "negativo"),
        ("neutral", "neutro"),
        ("positive", "positivo"),
        ("NEG", "negativo"),
        ("NEU", "neutro"),
        ("POS", "positivo"),
        ("  Positivo  ", "positivo"),
    ],
)
def test_normalizar_rotulo(entrada, esperado):
    assert normalizar_rotulo(entrada) == esperado


@pytest.mark.parametrize("entrada_invalida", ["excelente", "", "   ", None, True, False])
def test_rotulo_invalido(entrada_invalida):
    with pytest.raises(ValueError, match="Rótulo inválido"):
        normalizar_rotulo(entrada_invalida)


@pytest.mark.parametrize("nota_invalida", ["5.5", "0.5", "0", "-1", "NaN", "Infinity"])
def test_nota_fora_do_intervalo(nota_invalida):
    with pytest.raises(ValueError):
        normalizar_rotulo(nota_invalida)


def test_importar_csv_valido(tmp_path: Path):
    arquivo = tmp_path / "dataset.csv"

    arquivo.write_text(
        "id,texto,rotulo,fonte\n"
        '123,"Produto horrível",1,BPSAD\n'
        '456,"Produto razoável",3,BPSAD\n'
        '789,"Produto excelente",5,BPSAD\n',
        encoding="utf-8",
    )

    registros = importar_dataset_csv(arquivo)

    assert len(registros) == 3

    assert registros[0]["rotulo_original"] == "negativo"
    assert registros[1]["rotulo_original"] == "neutro"
    assert registros[2]["rotulo_original"] == "positivo"

    assert registros[0]["texto_original"] == "Produto horrível"
    assert registros[0]["fonte"] == "BPSAD"
    assert registros[0]["data_publicacao"] is None

    # IDs originais fornecidos no CSV devem ser preservados em id_origem
    assert registros[0]["id_origem"] == "123"
    assert registros[1]["id_origem"] == "456"
    assert registros[2]["id_origem"] == "789"
    assert "sentimento" not in registros[0]
    assert "rotulo_padronizado" not in registros[0]


# ============================================================================
# 2. CSV BPSAD válido
# ============================================================================


def test_importar_bpsad_valido(tmp_path: Path):
    arquivo = tmp_path / "bpsad.csv"
    arquivo.write_text(
        "review_text,rating,dataset\n"
        '"Entrega rápida e produto ótimo!",5,olist\n'
        '"Atendeu o básico esperado.",3,olist\n'
        '"Veio com defeito e atrasou.",1,b2w\n',
        encoding="utf-8",
    )

    registros = importar_dataset_csv(arquivo)

    assert len(registros) == 3
    assert registros[0]["texto_original"] == "Entrega rápida e produto ótimo!"
    assert registros[0]["rotulo_original"] == "positivo"
    assert registros[0]["fonte"] == "olist"
    assert registros[0]["id_origem"].startswith("olist_000001_")
    assert registros[1]["rotulo_original"] == "neutro"
    assert registros[2]["rotulo_original"] == "negativo"
    assert registros[2]["fonte"] == "b2w"
    assert registros[2]["id_origem"].startswith("b2w_000001_")
    assert all("sentimento" not in r for r in registros)


def test_iterar_bpsad_direto_com_id_data_e_metadados(tmp_path: Path):
    arquivo = tmp_path / "bpsad_completo.csv"
    arquivo.write_text(
        "review_id,review_text,rating,dataset,review_date,polarity\n"
        'rev_10,"Excelente qualidade",5,olist,2026-10-01,1\n',
        encoding="utf-8",
    )

    registros = list(iterar_bpsad(arquivo))
    assert len(registros) == 1
    assert registros[0] == {
        "id_origem": "rev_10",
        "texto_original": "Excelente qualidade",
        "fonte": "olist",
        "rotulo_original": "positivo",
        "data_publicacao": "2026-10-01",
        "metadados": {"polarity": "1"},
    }


# ============================================================================
# 5. Entradas sem rótulos (datasets não rotulados para inferência)
# ============================================================================


def test_importar_csv_sem_coluna_rotulo(tmp_path: Path):
    arquivo = tmp_path / "sem_rotulo.csv"
    arquivo.write_text(
        "id_origem,texto,fonte\n"
        'coleta_01,"Adorei o novo sistema da universidade!",ColetaWeb\n'
        'coleta_02,"O servidor caiu novamente hoje cedo.",ColetaWeb\n',
        encoding="utf-8",
    )

    registros = importar_dataset_csv(arquivo)

    assert len(registros) == 2
    assert registros[0]["id_origem"] == "coleta_01"
    assert registros[0]["rotulo_original"] is None
    assert registros[1]["rotulo_original"] is None
    assert "sentimento" not in registros[0]
    assert "sentimento" not in registros[1]


def test_importar_csv_com_celula_rotulo_vazia(tmp_path: Path):
    arquivo = tmp_path / "rotulo_parcial.csv"
    arquivo.write_text(
        "id,texto,rotulo,fonte\n"
        '1,"Texto já anotado",positivo,TweetSentBR\n'
        '2,"Texto aguardando inferência",,TweetSentBR\n'
        '3,"Outro texto sem anotação",   ,TweetSentBR\n',
        encoding="utf-8",
    )

    registros = importar_dataset_csv(arquivo)

    assert len(registros) == 3
    assert registros[0]["rotulo_original"] == "positivo"
    assert registros[1]["rotulo_original"] is None
    assert registros[2]["rotulo_original"] is None


def test_importar_bpsad_sem_coluna_rating(tmp_path: Path):
    arquivo = tmp_path / "bpsad_sem_rating.csv"
    arquivo.write_text(
        "review_text,dataset\n"
        '"Avaliação sem nota atribuída",olist\n',
        encoding="utf-8",
    )

    registros = importar_dataset_csv(arquivo)
    assert len(registros) == 1
    assert registros[0]["rotulo_original"] is None
    assert "sentimento" not in registros[0]


# ============================================================================
# 6 e 7. IDs preservados e IDs estáveis entre importações repetidas
# ============================================================================


@pytest.mark.parametrize("coluna_id", ["id_origem", "id", "identificador"])
def test_ids_preservados_quando_fornecidos(tmp_path: Path, coluna_id: str):
    arquivo = tmp_path / f"dataset_{coluna_id}.csv"
    arquivo.write_text(
        f"{coluna_id},texto,rotulo,fonte\n"
        'tw_abc_99,"Texto com identificador próprio",positivo,TweetSentBR\n',
        encoding="utf-8",
    )

    registros = importar_dataset_csv(arquivo)
    assert registros[0]["id_origem"] == "tw_abc_99"


def test_ids_diferentes_em_importacoes_separadas_corrigido_para_estaveis(tmp_path: Path):
    """Verifica que importações repetidas do mesmo arquivo geram o mesmo id_origem determinístico."""
    arquivo = tmp_path / "dataset.csv"

    arquivo.write_text(
        "texto,rotulo,fonte\n"
        "Muito bom,5,TweetSentBR\n",
        encoding="utf-8",
    )

    primeira_importacao = importar_dataset_csv(arquivo)
    segunda_importacao = importar_dataset_csv(arquivo)

    assert primeira_importacao[0]["id_origem"] == segunda_importacao[0]["id_origem"]
    assert primeira_importacao == segunda_importacao


def test_bpsad_ids_estaveis_entre_importacoes_repetidas(tmp_path: Path):
    arquivo = tmp_path / "bpsad.csv"
    arquivo.write_text(
        "review_text,rating,dataset\n"
        '"Produto excelente",5,olist\n'
        '"Entrega demorou",2,olist\n',
        encoding="utf-8",
    )

    primeira = importar_dataset_csv(arquivo)
    segunda = importar_dataset_csv(arquivo)

    assert [r["id_origem"] for r in primeira] == [r["id_origem"] for r in segunda]


# ============================================================================
# 8, 9, 10 e 11. Arquivos vazios, colunas ausentes, encoding e campos vazios
# ============================================================================


def test_csv_arquivo_vazio_zero_bytes(tmp_path: Path):
    arquivo = tmp_path / "vazio.csv"
    arquivo.write_text("", encoding="utf-8")

    with pytest.raises(ValueError, match="O arquivo CSV está vazio"):
        importar_dataset_csv(arquivo)


def test_csv_sem_registros(tmp_path: Path):
    arquivo = tmp_path / "dataset.csv"

    arquivo.write_text(
        "texto,rotulo,fonte\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="não possui registros"):
        importar_dataset_csv(arquivo)


def test_bpsad_arquivo_vazio_e_sem_registros(tmp_path: Path):
    vazio = tmp_path / "bpsad_vazio.csv"
    vazio.write_text("", encoding="utf-8")
    with pytest.raises(ValueError, match="O arquivo CSV está vazio"):
        list(iterar_bpsad(vazio))

    apenas_cabecalho = tmp_path / "bpsad_cabecalho.csv"
    apenas_cabecalho.write_text("review_text,rating,dataset\n", encoding="utf-8")
    with pytest.raises(ValueError, match="não possui registros"):
        list(iterar_bpsad(apenas_cabecalho))


def test_coluna_obrigatoria_ausente(tmp_path: Path):
    arquivo = tmp_path / "dataset.csv"

    arquivo.write_text(
        "texto,rotulo\n"
        "Muito bom,5\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Colunas obrigatórias ausentes"):
        importar_dataset_csv(arquivo)


def test_coluna_texto_obrigatoria_ausente(tmp_path: Path):
    arquivo = tmp_path / "sem_texto.csv"
    arquivo.write_text(
        "id,rotulo,fonte\n"
        "1,positivo,TweetSentBR\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Colunas obrigatórias ausentes: texto"):
        importar_dataset_csv(arquivo)


def test_bpsad_coluna_obrigatoria_ausente(tmp_path: Path):
    arquivo = tmp_path / "bpsad_incompleto.csv"
    arquivo.write_text(
        "review_text,rating\n"
        '"Bom produto",5\n',
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Colunas obrigatórias ausentes no BPSAD: dataset"):
        importar_dataset_csv(arquivo)


def test_csv_coluna_sem_nome_e_colunas_duplicadas(tmp_path: Path):
    sem_nome = tmp_path / "sem_nome.csv"
    sem_nome.write_text("texto,fonte,\nOi,Teste,1\n", encoding="utf-8")
    with pytest.raises(ValueError, match="coluna sem nome"):
        importar_dataset_csv(sem_nome)

    duplicada = tmp_path / "duplicada.csv"
    duplicada.write_text("texto,fonte,TEXTO\nOi,Teste,Oi\n", encoding="utf-8")
    with pytest.raises(ValueError, match="colunas duplicados"):
        importar_dataset_csv(duplicada)


def test_csv_encoding_invalido(tmp_path: Path):
    arquivo_latin1 = tmp_path / "latin1.csv"
    arquivo_latin1.write_bytes(
        "texto,rotulo,fonte\nNão gostei da programação,negativo,Teste\n".encode("iso-8859-1")
    )

    with pytest.raises(ValueError, match="UTF-8"):
        importar_dataset_csv(arquivo_latin1)

    arquivo_binario = tmp_path / "binario.csv"
    arquivo_binario.write_bytes(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\xff\xfe\xfd")

    with pytest.raises(ValueError, match="UTF-8"):
        importar_dataset_csv(arquivo_binario)


def test_csv_estrutura_aspas_quebradas(tmp_path: Path):
    arquivo = tmp_path / "aspas_quebradas.csv"
    arquivo.write_text(
        "id,texto,rotulo,fonte\n"
        '1,"Texto com aspas abertas sem fechar,positivo,TweetSentBR\n',
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Erro na estrutura do CSV"):
        importar_dataset_csv(arquivo)


def test_campo_obrigatorio_vazio(tmp_path: Path):
    arquivo = tmp_path / "dataset.csv"

    arquivo.write_text(
        "texto,rotulo,fonte\n"
        ",5,BPSAD\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="não podem estar vazios"):
        importar_dataset_csv(arquivo)


def test_campo_fonte_obrigatorio_vazio(tmp_path: Path):
    arquivo = tmp_path / "fonte_vazia.csv"
    arquivo.write_text(
        "texto,rotulo,fonte\n"
        '"Texto válido",5,   \n',
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="não podem estar vazios"):
        importar_dataset_csv(arquivo)


def test_rotulo_invalido_no_csv(tmp_path: Path):
    arquivo = tmp_path / "dataset.csv"

    arquivo.write_text(
        "texto,rotulo,fonte\n"
        "Texto de teste,excelente,BPSAD\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Rótulo inválido"):
        importar_dataset_csv(arquivo)


# ============================================================================
# 12. Registros duplicados e textos iguais de registros distintos
# ============================================================================


def test_textos_iguais_sem_id_nao_sao_confundidos(tmp_path: Path):
    """Registros distintos sem ID que possuem textos idênticos recebem IDs diferentes."""
    arquivo = tmp_path / "textos_repetidos.csv"
    arquivo.write_text(
        "texto,rotulo,fonte\n"
        '"Muito bom!",5,BPSAD\n'
        '"Muito bom!",5,BPSAD\n',
        encoding="utf-8",
    )

    registros = importar_dataset_csv(arquivo)

    assert len(registros) == 2
    assert registros[0]["id_origem"] != registros[1]["id_origem"]


def test_id_origem_duplicado_rejeitado_em_modo_estrito(tmp_path: Path):
    arquivo = tmp_path / "duplicados.csv"
    arquivo.write_text(
        "id_origem,texto,rotulo,fonte\n"
        'tw_100,"Primeiro texto",positivo,TweetSentBR\n'
        'tw_100,"Segundo texto com mesmo ID",negativo,TweetSentBR\n',
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="identificador duplicado 'tw_100'"):
        importar_dataset_csv(arquivo, modo_estrito=True)


def test_id_origem_duplicado_descartado_em_modo_tolerante(tmp_path: Path):
    arquivo = tmp_path / "duplicados_tolerante.csv"
    arquivo.write_text(
        "id_origem,texto,rotulo,fonte\n"
        'tw_100,"Primeiro texto mantido",positivo,TweetSentBR\n'
        'tw_100,"Duplicata descartada",negativo,TweetSentBR\n'
        'tw_101,"Terceiro texto mantido",neutro,TweetSentBR\n',
        encoding="utf-8",
    )

    relatorio = RelatorioImportacao()
    registros = importar_dataset_csv(arquivo, modo_estrito=False, relatorio=relatorio)

    assert len(registros) == 2
    assert [r["id_origem"] for r in registros] == ["tw_100", "tw_101"]
    assert registros[0]["texto_original"] == "Primeiro texto mantido"
    assert relatorio.total_lidos == 3
    assert relatorio.total_importados == 2
    assert relatorio.total_descartados == 1
    assert relatorio.descartes_por_motivo == {"id_origem_duplicado": 1}


# ============================================================================
# 13 e 14. Delimitadores diferentes, acentuação PT-BR e emojis
# ============================================================================


def test_csv_com_ponto_e_virgula(tmp_path: Path):
    arquivo = tmp_path / "dataset.csv"

    arquivo.write_text(
        "texto;rotulo;fonte\n"
        "Muito bom;5;BPSAD\n",
        encoding="utf-8",
    )

    registros = importar_dataset_csv(
        arquivo,
        delimitador=";",
    )

    assert len(registros) == 1
    assert registros[0]["rotulo_original"] == "positivo"


@pytest.mark.parametrize("delimitador", ["\t", "|"])
def test_csv_com_outros_delimitadores(tmp_path: Path, delimitador: str):
    arquivo = tmp_path / "delim.csv"
    arquivo.write_text(
        f"id{delimitador}texto{delimitador}rotulo{delimitador}fonte\n"
        f"10{delimitador}Serviço ótimo{delimitador}positivo{delimitador}Coleta\n",
        encoding="utf-8",
    )

    registros = importar_dataset_csv(arquivo, delimitador=delimitador)
    assert len(registros) == 1
    assert registros[0]["id_origem"] == "10"
    assert registros[0]["rotulo_original"] == "positivo"


@pytest.mark.parametrize("delimitador_invalido", ["", ";;", "::"])
def test_delimitador_invalido(tmp_path: Path, delimitador_invalido: str):
    arquivo = tmp_path / "valido.csv"
    arquivo.write_text("texto,fonte\nOi,Teste\n", encoding="utf-8")

    with pytest.raises(ValueError, match="apenas um caractere"):
        importar_dataset_csv(arquivo, delimitador=delimitador_invalido)


def test_csv_acentuacao_brasileira_e_emojis(tmp_path: Path):
    arquivo = tmp_path / "pt_br_emojis.csv"
    texto_rico = (
        "Avaliação excelente: ç, ã, é, í, õ, ê, á, ú, ô e à! "
        "Adorei demais 😍🔥🚀👏❤️!"
    )
    arquivo.write_text(
        "id_origem,texto,rotulo,fonte\n"
        f'emo_01,"{texto_rico}",positivo,TweetSentBR\n',
        encoding="utf-8",
    )

    registros = importar_dataset_csv(arquivo)
    assert len(registros) == 1
    assert registros[0]["texto_original"] == texto_rico
    for caractere in ("ç", "ã", "é", "í", "😍", "🔥", "🚀"):
        assert caractere in registros[0]["texto_original"]


# ============================================================================
# 15 e 16. Modo estrito e modo tolerante com contabilização de descartes
# ============================================================================


@pytest.mark.parametrize(
    "linha_invalida, match_esperado",
    [
        (",5,olist", "review_text"),
        ('"   ",5,olist', "review_text"),
        ('"Produto bom",,olist', "rating"),
        ('"Produto bom",9,olist', "Nota fora do intervalo"),
        ('"Produto bom",5,', "dataset"),
        ('"Produto bom",5,olist,extra', "maior que a de colunas"),
    ],
)
def test_bpsad_modo_estrito_rejeita_registros_invalidos(
    tmp_path: Path,
    linha_invalida: str,
    match_esperado: str,
):
    arquivo = tmp_path / "bpsad_invalido.csv"
    arquivo.write_text(
        "review_text,rating,dataset\n"
        f"{linha_invalida}\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match=match_esperado):
        importar_dataset_csv(arquivo, modo_estrito=True)


def test_bpsad_modo_tolerante_contabiliza_descartes_e_motivos(tmp_path: Path):
    arquivo = tmp_path / "bpsad_misto.csv"
    arquivo.write_text(
        "review_id,review_text,rating,dataset\n"
        'r1,"Produto excelente!",5,olist\n'
        'r2,"   ",4,olist\n'
        'r3,"Sem nota informada",,olist\n'
        'r4,"Nota fora da escala",9,olist\n'
        'r5,"Sem dataset informado",2,\n'
        'r1,"ID duplicado na mesma fonte",1,olist\n'
        'r6,"Entrega atrasou bastante",1,olist\n',
        encoding="utf-8",
    )

    relatorio = RelatorioImportacao()
    registros = importar_dataset_csv(
        arquivo,
        modo_estrito=False,
        relatorio=relatorio,
    )

    assert len(registros) == 2
    assert [r["id_origem"] for r in registros] == ["r1", "r6"]
    assert [r["rotulo_original"] for r in registros] == ["positivo", "negativo"]

    assert relatorio.total_lidos == 7
    assert relatorio.total_importados == 2
    assert relatorio.total_descartados == 5
    assert relatorio.descartes_por_motivo == {
        "texto_vazio": 1,
        "rotulo_vazio": 1,
        "rotulo_invalido": 1,
        "fonte_vazia": 1,
        "id_origem_duplicado": 1,
    }
    assert len(relatorio.detalhes_descartes) == 5


def test_csv_padrao_modo_tolerante_contabiliza_descartes(tmp_path: Path):
    arquivo = tmp_path / "padrao_misto.csv"
    arquivo.write_text(
        "id,texto,rotulo,fonte\n"
        '1,"Texto válido positivo",positivo,TweetSentBR\n'
        '2,"",positivo,TweetSentBR\n'
        '3,"Rótulo desconhecido",talvez,TweetSentBR\n'
        '4,"Fonte ausente",neutro,\n'
        '5,"Coluna excedente",neutro,TweetSentBR,extra\n'
        '6,"Texto sem rótulo mas válido",,TweetSentBR\n',
        encoding="utf-8",
    )

    relatorio = RelatorioImportacao()
    registros = importar_dataset_csv(
        arquivo,
        modo_estrito=False,
        relatorio=relatorio,
    )

    assert len(registros) == 2
    assert [r["id_origem"] for r in registros] == ["1", "6"]
    assert registros[0]["rotulo_original"] == "positivo"
    assert registros[1]["rotulo_original"] is None

    assert relatorio.total_lidos == 6
    assert relatorio.total_importados == 2
    assert relatorio.total_descartados == 4
    assert relatorio.descartes_por_motivo == {
        "texto_vazio": 1,
        "rotulo_invalido": 1,
        "fonte_vazia": 1,
        "colunas_excedentes": 1,
    }


# ============================================================================
# 17, 18, 19 e 20. Contrato Issue #11, datas/metadados, streaming e sem 'sentimento'
# ============================================================================


def test_compatibilidade_contrato_issue_11_e_preservacao_datas_metadados(tmp_path: Path):
    arquivo = tmp_path / "contrato_issue_11.csv"
    arquivo.write_text(
        "id,texto,sentimento,fonte,data,categoria,idioma\n"
        'tw_001,"A programação da conferência foi ótima e trouxe inovação ao país!",positivo,TweetSentBR,2026-10-01,eventos,pt-br\n'
        'tw_002,"Péssimo serviço de atenção ao usuário, não recomendo de jeito nenhum.",negativo,TweetSentBR,2026-10-02,atendimento,pt-br\n'
        'tw_005,"O sistema permaneceu indisponível durante a manutenção programada.",negativo,TweetSentBR,,,\n',
        encoding="utf-8",
    )

    registros = importar_csv(arquivo)
    assert adquirir_dados(arquivo) == registros
    assert len(registros) == 3

    for r in registros:
        assert CAMPOS_OBRIGATORIOS_CONTRATO.issubset(r.keys())
        assert "sentimento" not in r
        assert "rotulo_padronizado" not in r
        assert isinstance(r["id_origem"], str) and r["id_origem"]
        assert isinstance(r["texto_original"], str) and r["texto_original"].strip()
        assert isinstance(r["fonte"], str) and r["fonte"]
        assert r["rotulo_original"] in ROTULOS_PADRONIZADOS

    assert registros[0]["id_origem"] == "tw_001"
    assert registros[0]["rotulo_original"] == "positivo"
    assert registros[0]["data_publicacao"] == "2026-10-01"
    assert registros[0]["metadados"] == {"categoria": "eventos", "idioma": "pt-br"}

    # Registro sem data e sem metadados preenchidos mantém data_publicacao = None e omite metadados vazios
    assert registros[2]["id_origem"] == "tw_005"
    assert registros[2]["data_publicacao"] is None
    assert "metadados" not in registros[2]


def test_comportamento_iterativo_streaming_sem_carregar_tudo_em_memoria(tmp_path: Path):
    """Garante que iterar_dataset_csv é um gerador lazy que processa linha a linha."""
    arquivo = tmp_path / "grande_com_erro_no_final.csv"
    arquivo.write_text(
        "id,texto,rotulo,fonte\n"
        '1,"Primeiro registro lido em streaming",positivo,TweetSentBR\n'
        '2,"Segundo registro lido em streaming",neutro,TweetSentBR\n'
        '3,"Terceiro registro inválido que só falharia se lido",rotulo_invalido,TweetSentBR\n',
        encoding="utf-8",
    )

    fluxo = iterar_dataset_csv(arquivo, modo_estrito=True)
    assert isinstance(fluxo, Iterator)

    primeiro = next(fluxo)
    segundo = next(fluxo)
    assert primeiro["id_origem"] == "1"
    assert segundo["id_origem"] == "2"

    # A linha 3 só é avaliada quando o iterador avança até ela
    with pytest.raises(ValueError, match="Registro 4: Rótulo inválido"):
        next(fluxo)


def test_ausencia_criacao_indevida_campo_sentimento(tmp_path: Path):
    arquivo = tmp_path / "entrada_com_coluna_sentimento.csv"
    arquivo.write_text(
        "id_origem,texto_original,sentimento,fonte,data_publicacao\n"
        'a_001,"Texto com rótulo humano",POS,DatasetTeste,2026-10-01\n'
        'a_002,"Texto sem rótulo humano",,DatasetTeste,\n',
        encoding="utf-8",
    )

    registros = importar_dataset_csv(arquivo)
    for r in registros:
        assert "sentimento" not in r
    assert registros[0]["rotulo_original"] == "positivo"
    assert registros[1]["rotulo_original"] is None


@pytest.mark.parametrize("caminho_invalido", [None, "", "   "])
def test_caminho_arquivo_vazio_ou_none(caminho_invalido):
    with pytest.raises(ValueError, match="caminho do arquivo CSV não pode ser vazio"):
        importar_dataset_csv(caminho_invalido)


def test_arquivo_inexistente_ou_diretorio(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        importar_dataset_csv(tmp_path / "nao_existe.csv")

    with pytest.raises(FileNotFoundError):
        importar_dataset_csv(tmp_path)
