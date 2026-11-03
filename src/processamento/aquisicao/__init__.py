"""Módulo de aquisição e importação de datasets textuais do SentIA."""

from .bpsad_adapter import iterar_bpsad
from .csv_importer import (
    MAPA_ROTULO_SENTIA,
    ROTULOS_PADRONIZADOS,
    RelatorioImportacao,
    converter_rotulo_para_sentia,
    importar_csv,
    importar_dataset_csv,
    iterar_csv,
    iterar_dataset_csv,
    normalizar_rotulo,
)
from .tweetsentbr import (
    CAMINHO_PADRAO_TWEETSENTBR,
    DIRETORIO_RAIZ_PROJETO,
    FONTE_PADRAO_TWEETSENTBR,
    adquirir_dados,
    carregar_tweetsentbr,
    iterar_dados_aquisicao,
    iterar_tweetsentbr,
    resolver_caminho_tweetsentbr,
)

__all__ = [
    "CAMINHO_PADRAO_TWEETSENTBR",
    "DIRETORIO_RAIZ_PROJETO",
    "FONTE_PADRAO_TWEETSENTBR",
    "MAPA_ROTULO_SENTIA",
    "ROTULOS_PADRONIZADOS",
    "RelatorioImportacao",
    "adquirir_dados",
    "carregar_tweetsentbr",
    "converter_rotulo_para_sentia",
    "importar_csv",
    "importar_dataset_csv",
    "iterar_bpsad",
    "iterar_csv",
    "iterar_dados_aquisicao",
    "iterar_dataset_csv",
    "iterar_tweetsentbr",
    "normalizar_rotulo",
    "resolver_caminho_tweetsentbr",
]

