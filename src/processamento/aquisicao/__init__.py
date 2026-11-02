"""Módulo de aquisição e importação de datasets textuais do SentIA."""

from .bpsad_adapter import iterar_bpsad
from .csv_importer import (
    ROTULOS_PADRONIZADOS,
    RelatorioImportacao,
    adquirir_dados,
    importar_csv,
    importar_dataset_csv,
    iterar_dataset_csv,
    normalizar_rotulo,
)

__all__ = [
    "ROTULOS_PADRONIZADOS",
    "RelatorioImportacao",
    "adquirir_dados",
    "importar_csv",
    "importar_dataset_csv",
    "iterar_bpsad",
    "iterar_dataset_csv",
    "normalizar_rotulo",
]

