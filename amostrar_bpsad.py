"""Compatibilidade: prefira python -m scripts.experimentos.amostrar_bpsad."""
from scripts.experimentos.amostrar_bpsad import main

if __name__ == "__main__":
    raise SystemExit(main())
