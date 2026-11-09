"""Restrição da arquitetura (seção 2.4.2): a interface só acessa o sistema pela API."""

import ast
from pathlib import Path

import pytest

PASTA_PAINEL = Path(__file__).resolve().parents[1] / "src" / "apresentacao"
PROIBIDOS = ("pymongo", "src.dados", "src.processamento", "src.servico")


def _modulos_importados(arquivo: Path) -> set[str]:
    modulos = set()
    for no in ast.walk(ast.parse(arquivo.read_text(encoding="utf-8"))):
        if isinstance(no, ast.Import):
            modulos.update(alias.name for alias in no.names)
        elif isinstance(no, ast.ImportFrom) and no.module:
            modulos.add(no.module)
    return modulos


@pytest.mark.parametrize(
    "arquivo", sorted(PASTA_PAINEL.rglob("*.py")), ids=lambda a: a.name
)
def test_painel_nao_acessa_banco_nem_processamento(arquivo):
    proibidos = [
        modulo
        for modulo in _modulos_importados(arquivo)
        if any(modulo == p or modulo.startswith(f"{p}.") for p in PROIBIDOS)
    ]
    assert proibidos == []
