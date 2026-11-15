#!/usr/bin/env python3
"""Script CLI para auditoria reprodutível de datasets do SentIA (TweetSentBR e BPSAD).

Exemplos de uso:
    python scripts/auditar_datasets.py
    python scripts/auditar_datasets.py Datasets/tweetsent.csv
    python scripts/auditar_datasets.py /caminho/para/concatenated.csv --sem-duplicatas
"""

from __future__ import annotations

import sys
from pathlib import Path

DIRETORIO_RAIZ = Path(__file__).resolve().parents[1]
if str(DIRETORIO_RAIZ) not in sys.path:
    sys.path.insert(0, str(DIRETORIO_RAIZ))

from src.processamento.aquisicao.auditoria_datasets import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
