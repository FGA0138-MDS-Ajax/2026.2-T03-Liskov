from fastapi import FastAPI

from .administracao import NaoAutenticado, responder_nao_autenticado, roteador

app = FastAPI(title="SentIA API")
app.add_exception_handler(NaoAutenticado, responder_nao_autenticado)
app.include_router(roteador)


@app.get("/health")
def health():
    return {"status": "ok"}
