"""Verificação automatizável: uv run python test_mongo.py (após migração uv)."""

import sys

from src.dados.database import (
    ErroConexaoMongoDB,
    ErroConfiguracaoMongoDB,
    connect_to_mongodb,
    disconnect_from_mongodb,
)


def main() -> int:
    client = None
    status = 1
    try:
        client = connect_to_mongodb()
        status = 0
    except (ErroConfiguracaoMongoDB, ErroConexaoMongoDB) as erro:
        print(f"Teste falhou: {erro}", file=sys.stderr)
    except Exception:  # noqa: BLE001 - Fronteira da CLI: mensagem segura e saída não zero.
        # Não reproduzir exceções inesperadas que possam conter credenciais.
        print(
            "Teste falhou: erro inesperado na verificação do MongoDB.", file=sys.stderr
        )
    finally:
        if client is not None:
            try:
                disconnect_from_mongodb(client)
            except ErroConexaoMongoDB:
                print(
                    "Teste falhou: não foi possível encerrar o cliente MongoDB.",
                    file=sys.stderr,
                )
                status = 1
    if status == 0:
        print("Sucesso: conexão e ping do MongoDB validados; cliente encerrado.")
    return status


if __name__ == "__main__":
    raise SystemExit(main())
