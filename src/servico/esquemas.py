import re
from datetime import UTC, date, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


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


class FiltrosConsulta(BaseModel):
    inicio: date | None = None
    fim: date | None = None
    sentimento: Literal["positivo", "negativo", "neutro"] | None = None

    @field_validator("inicio", "fim", mode="before")
    @classmethod
    def validar_data(cls, valor):
        if valor is not None and (
            not isinstance(valor, str) or re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", valor) is None
        ):
            raise ValueError("Informe a data no formato AAAA-MM-DD.")
        return valor

    @model_validator(mode="after")
    def validar_intervalo(self):
        if self.inicio is not None and self.fim is not None and self.inicio > self.fim:
            raise ValueError("inicio não pode ser posterior a fim.")
        return self


class ConsultaAnalises(FiltrosConsulta):
    pagina: int = Field(default=1, ge=1)
    tamanho: int = Field(default=20, ge=1, le=100)

    @field_validator("pagina", "tamanho", mode="before")
    @classmethod
    def validar_inteiro_query(cls, valor):
        if isinstance(valor, str) and re.fullmatch(r"[0-9]+", valor) is None:
            raise ValueError("Informe um inteiro positivo.")
        return valor


class AnaliseSaida(BaseModel):
    id_origem: str
    fonte: str
    texto_original: str
    sentimento: Literal["positivo", "negativo", "neutro"]
    modelo: dict[str, Any]
    data_processamento: datetime
    data_publicacao: datetime | None = None
    probabilidades: dict[str, float] | None = None
    rotulo_original: str | None = None
    rotulo_padronizado: str | None = None
    metadados: dict[str, Any] | None = None

    @field_validator("data_processamento", "data_publicacao", mode="before")
    @classmethod
    def normalizar_data_mongodb(cls, valor):
        # O driver retorna BSON Date como datetime sem tzinfo por padrão, em UTC.
        if isinstance(valor, datetime):
            return valor.replace(tzinfo=UTC) if valor.tzinfo is None else valor.astimezone(UTC)
        return valor


class PaginaAnalisesSaida(BaseModel):
    itens: list[AnaliseSaida]
    pagina: int
    tamanho: int
    total: int


class ResumoAnalisesSaida(BaseModel):
    total: int
    por_sentimento: dict[Literal["positivo", "negativo", "neutro"], int]
    sem_data_publicacao: int
