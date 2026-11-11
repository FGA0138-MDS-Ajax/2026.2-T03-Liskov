from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class RegistroEntrada(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id_origem: str = Field(min_length=1, pattern=r"\S")
    fonte: str = Field(min_length=1, pattern=r"\S")
    texto_original: str = Field(min_length=1, pattern=r"\S")
    rotulo_original: str | None = None
    rotulo_padronizado: str | None = None
    data_publicacao: str | None = None
    metadados: dict[str, Any] | None = None


class LoteEntrada(BaseModel):
    registros: list[RegistroEntrada] = Field(min_length=1, max_length=1000)


class ResultadoProcessamento(BaseModel):
    recebidos: int
    inseridos: int
    duplicados: int


class Erro(BaseModel):
    detail: str
