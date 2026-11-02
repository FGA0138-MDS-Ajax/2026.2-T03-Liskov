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

__all__ = [
    "MAPA_ROTULO_SENTIA",
    "ROTULOS_PADRONIZADOS",
    "RelatorioImportacao",
    "converter_rotulo_para_sentia",
    "importar_csv",
    "importar_dataset_csv",
    "iterar_bpsad",
    "iterar_csv",
    "iterar_dataset_csv",
    "normalizar_rotulo",
]

