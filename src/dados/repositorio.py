import hashlib
import math
import re
import unicodedata
from collections.abc import Iterable, Mapping
from contextlib import suppress
from datetime import UTC, date, datetime, time, timedelta
from typing import Any
from uuid import uuid4

from bson import ObjectId
from bson.errors import InvalidId
from pymongo import ASCENDING, IndexModel, UpdateOne
from pymongo.collection import Collection
from pymongo.errors import BulkWriteError, DuplicateKeyError, PyMongoError
from pymongo.mongo_client import MongoClient

from src.comum.busca_textual import (
    minimo_de_termos,
    padrao_do_termo,
    termos_da_consulta,
)

NOME_BANCO_PADRAO = "sentia"
NOME_COLECAO = "analises"
NOME_COLECAO_REGISTROS = "registros"
NOME_COLECAO_DATASETS = "datasets"
NOME_COLECAO_PESQUISAS = "pesquisas"
# Buscas no X feitas pelo Usuário sem login (#120): uma linha por busca paga.
NOME_COLECAO_BUSCAS_X_PUBLICAS = "buscas_x_publicas"
# Decisão da PO (25 e 26/11): o cache de uma pesquisa vale 30 dias.
VALIDADE_CACHE_PESQUISA = timedelta(days=30)
SENTIMENTOS_VALIDOS = {"positivo", "negativo", "neutro"}
CAMPOS_TEXTO_OBRIGATORIOS = ("id_origem", "fonte", "texto_original")
LIMITE_MAXIMO_PAGINA = 100
LIMITE_CHAVES_EMBEDDED_DATASET = 50_000
TAMANHO_LOTE_CONSULTA_CHAVES = 200
_IDENTIFICADORES_INVALIDOS = frozenset(
    {"none", "null", "nan", "<na>", "n/a", "undefined", "nil"}
)


class ErroAnaliseInvalida(ValueError):
    """Documento fora do esquema da coleção analises."""


class ErroConsultaInvalida(ValueError):
    """Chave natural inválida para a busca de uma análise."""


class ErroLeituraAnalises(RuntimeError):
    """Falha de leitura com mensagem segura, sem URI ou credenciais."""


def _buscar_analise(colecao: Collection, filtro: dict[str, Any]) -> dict[str, Any] | None:
    try:
        return colecao.find_one(filtro)
    except PyMongoError:
        raise ErroLeituraAnalises(
            "Falha ao consultar o MongoDB; verifique a conexão."
        ) from None


def buscar_por_id_origem(
    colecao: Collection, fonte: str, id_origem: str
) -> dict[str, Any] | None:
    """Busca interna pela chave natural exata, sem serializar o documento BSON."""
    for nome, valor in (("fonte", fonte), ("id_origem", id_origem)):
        if not isinstance(valor, str) or not valor.strip():
            raise ErroConsultaInvalida(f"{nome} deve ser texto não vazio.")
    return _buscar_analise(colecao, {"fonte": fonte, "id_origem": id_origem})


def buscar_por_id(
    colecao: Collection, id_documento: str | ObjectId
) -> dict[str, Any] | None:
    """Busca interna por ObjectId ou seu hexadecimal; ID inválido retorna None."""
    if not isinstance(id_documento, (str, ObjectId)):
        return None
    try:
        identificador = ObjectId(id_documento)
    except (InvalidId, TypeError):
        return None
    return _buscar_analise(colecao, {"_id": identificador})


INDICES = [
    IndexModel(
        [("fonte", ASCENDING), ("id_origem", ASCENDING)],
        unique=True,
        name="uq_fonte_id_origem",
    ),
    IndexModel(
        [("sentimento", ASCENDING), ("data_publicacao", ASCENDING)],
        name="idx_sentimento_data_publicacao",
    ),
    IndexModel([("data_publicacao", ASCENDING)], name="idx_data_publicacao"),
    IndexModel([("data_processamento", ASCENDING)], name="idx_data_processamento"),
]


def obter_colecao(client: MongoClient, nome_banco: str | None = None):

    if nome_banco is None:
        banco = client.get_default_database(NOME_BANCO_PADRAO)

    else:
        banco = client[nome_banco]

    return banco[NOME_COLECAO]


def criar_indices(colecao: Collection):

    return colecao.create_indexes(INDICES)


INDICES_REGISTROS = [
    IndexModel(
        [("fonte", ASCENDING), ("id_origem", ASCENDING)],
        unique=True,
        name="uq_registros_fonte_id_origem",
    ),
    IndexModel([("ids_datasets", ASCENDING)], name="idx_registros_ids_datasets"),
    IndexModel([("origem_coleta", ASCENDING)], name="idx_registros_origem_coleta"),
    IndexModel([("data_publicacao", ASCENDING)], name="idx_registros_data_publicacao"),
]

INDICES_DATASETS = [
    IndexModel(
        [("id_dataset", ASCENDING)],
        unique=True,
        name="uq_datasets_id_dataset",
    ),
    IndexModel([("criado_em", ASCENDING)], name="idx_datasets_criado_em"),
]

INDICES_PESQUISAS = [
    IndexModel(
        [("chave_cache", ASCENDING)],
        unique=True,
        name="uq_pesquisas_chave_cache",
    ),
    IndexModel(
        [("consulta_normalizada", ASCENDING), ("complementar_com_x", ASCENDING)],
        name="idx_pesquisas_consulta",
    ),
    IndexModel([("atualizado_em", ASCENDING)], name="idx_pesquisas_atualizado_em"),
]


def _colecao_auxiliar(colecao: Any, nome: str) -> Any:
    """Resolve uma coleção irmã no mesmo banco a partir da coleção `analises`."""
    database = getattr(colecao, "database", None)
    if database is None or not hasattr(database, "__getitem__"):
        raise ErroLeituraAnalises(
            "Banco de dados indisponível para consultar coleções auxiliares."
        )
    return database[nome]


def criar_indices_complementares(colecao: Collection) -> dict[str, Any]:
    """Cria de forma idempotente os índices de `registros`, `datasets` e `pesquisas`."""
    try:
        return {
            NOME_COLECAO_REGISTROS: _colecao_auxiliar(
                colecao, NOME_COLECAO_REGISTROS
            ).create_indexes(INDICES_REGISTROS),
            NOME_COLECAO_DATASETS: _colecao_auxiliar(
                colecao, NOME_COLECAO_DATASETS
            ).create_indexes(INDICES_DATASETS),
            NOME_COLECAO_PESQUISAS: _colecao_auxiliar(
                colecao, NOME_COLECAO_PESQUISAS
            ).create_indexes(INDICES_PESQUISAS),
        }
    except PyMongoError:
        raise ErroLeituraAnalises(
            "Falha ao criar índices auxiliares no MongoDB; verifique a conexão."
        ) from None


def validar_analise(documento: dict[str, Any]):

    for campo in CAMPOS_TEXTO_OBRIGATORIOS:
        valor = documento.get(campo)
        if not isinstance(valor, str) or not valor.strip():
            raise ErroAnaliseInvalida(f"Campo obrigatório ausente ou vazio: {campo}")

    if documento.get("sentimento") not in SENTIMENTOS_VALIDOS:
        raise ErroAnaliseInvalida("Sentimento deve ser positivo, negativo ou neutro")

    modelo = documento.get("modelo")
    if not isinstance(modelo, dict) or not modelo.get("nome"):
        raise ErroAnaliseInvalida("modelo.nome deve ser obrigatório")

    if "data_processamento" not in documento:
        raise ErroAnaliseInvalida("data_processamento deve ser obrigatória")
    
    data_processamento = documento["data_processamento"]

    if not isinstance(data_processamento, datetime) or data_processamento.tzinfo is None:
        raise ErroAnaliseInvalida(
            "data_processamento deve ser uma data com fuso horário (UTC)"
        )

    if "data_publicacao" in documento:
        data_publicacao = documento["data_publicacao"]

        if (
            not isinstance(data_publicacao, datetime)
            or data_publicacao.tzinfo is None
        ):
            raise ErroAnaliseInvalida(
                "data_publicacao deve ser uma data com fuso horário (UTC)"
            )


def salvar_analise(colecao: Collection, documento: dict[str, Any]):

    validar_analise(documento)
    try:
        colecao.insert_one(dict(documento))
    except DuplicateKeyError:
        return False
    return True


def salvar_analises(colecao: Collection, documentos: Iterable[dict[str, Any]]):

    copias = [dict(documento) for documento in documentos]
    for copia in copias:
        validar_analise(copia)

    if not copias:
        return {"inseridos": 0, "duplicados": 0}

    try:
        resultado = colecao.insert_many(copias, ordered=False)
    except BulkWriteError as erro:
        falhas = erro.details["writeErrors"]
        if erro.details.get("writeConcernErrors") or any(
            falha["code"] != 11000 for falha in falhas
        ):
            raise
        return {"inseridos": erro.details["nInserted"], "duplicados": len(falhas)}
    return {"inseridos": len(resultado.inserted_ids), "duplicados": 0}


def _validar_data_filtro(valor: Any, campo: str) -> date | None:
    if valor is None:
        return None
    if not isinstance(valor, date) or isinstance(valor, datetime):
        raise ErroConsultaInvalida(f"{campo} deve ser uma data válida.")
    return valor


TAMANHO_MAXIMO_ASSUNTO = 100


def _condicao_assunto(assunto: str) -> dict[str, Any]:
    """Filtro por assunto (#113) com a mesma regra da pesquisa do Administrador.

    Cada termo vira uma expressão regular fechada (o texto digitado nunca é usado
    como regex crua) e o MongoDB conta quantos termos aparecem no texto, sem trazer
    os documentos para o Python. Assim a paginação e os totais continuam no banco.
    """
    termos = termos_da_consulta(assunto)
    if not termos:
        # Só pontuação ou símbolos: nenhum texto é sobre "isso".
        return {"$expr": {"$eq": [1, 0]}}
    texto = {"$ifNull": ["$texto_original", ""]}
    presentes = [
        {
            "$cond": [
                {"$regexMatch": {"input": texto, "regex": padrao_do_termo(termo)}},
                1,
                0,
            ]
        }
        for termo in termos
    ]
    return {"$expr": {"$gte": [{"$add": presentes}, minimo_de_termos(termos)]}}


def _validar_assunto(assunto: str | None) -> str | None:
    if assunto is None:
        return None
    if not isinstance(assunto, str):
        raise ErroConsultaInvalida("assunto deve ser um texto.")
    assunto = " ".join(assunto.split())
    if len(assunto) > TAMANHO_MAXIMO_ASSUNTO:
        raise ErroConsultaInvalida(
            f"assunto deve ter no máximo {TAMANHO_MAXIMO_ASSUNTO} caracteres."
        )
    return assunto or None


def _filtro_consulta(
    inicio: date | None = None,
    fim: date | None = None,
    sentimento: str | None = None,
    assunto: str | None = None,
) -> dict[str, Any]:
    inicio_validado = _validar_data_filtro(inicio, "inicio")
    fim_validado = _validar_data_filtro(fim, "fim")
    if (
        inicio_validado is not None
        and fim_validado is not None
        and inicio_validado > fim_validado
    ):
        raise ErroConsultaInvalida("inicio não pode ser maior que fim.")
    if sentimento is not None and sentimento not in SENTIMENTOS_VALIDOS:
        raise ErroConsultaInvalida(
            "sentimento deve ser positivo, negativo ou neutro."
        )

    filtro: dict[str, Any] = {}
    if sentimento is not None:
        filtro["sentimento"] = sentimento
    periodo: dict[str, datetime] = {}
    if inicio_validado is not None:
        periodo["$gte"] = datetime.combine(inicio_validado, time.min, UTC)
    if fim_validado is not None:
        periodo["$lte"] = datetime.combine(fim_validado, time.max, UTC)
    if periodo:
        filtro["data_publicacao"] = periodo
    assunto_validado = _validar_assunto(assunto)
    if assunto_validado is not None:
        filtro.update(_condicao_assunto(assunto_validado))
    return filtro


def listar_analises(
    colecao: Collection,
    *,
    inicio: date | None = None,
    fim: date | None = None,
    sentimento: str | None = None,
    pagina: int = 1,
    tamanho: int = 20,
    assunto: str | None = None,
) -> dict[str, Any]:
    if type(pagina) is not int or pagina < 1:
        raise ErroConsultaInvalida("pagina deve ser um inteiro maior ou igual a 1.")
    if type(tamanho) is not int or not (1 <= tamanho <= LIMITE_MAXIMO_PAGINA):
        raise ErroConsultaInvalida(
            f"tamanho deve ser um inteiro entre 1 e {LIMITE_MAXIMO_PAGINA}."
        )

    filtro = _filtro_consulta(inicio, fim, sentimento, assunto)
    try:
        total = colecao.count_documents(filtro)
        # A chave única (fonte, id_origem) desempata datas iguais de forma estável.
        cursor = (
            colecao.find(filtro, {"_id": 0})
            .sort([("data_processamento", -1), ("fonte", 1), ("id_origem", 1)])
            .skip((pagina - 1) * tamanho)
            .limit(tamanho)
        )
        itens = list(cursor)
    except PyMongoError:
        raise ErroLeituraAnalises(
            "Falha ao consultar o MongoDB; verifique a conexão."
        ) from None
    return {"itens": itens, "pagina": pagina, "tamanho": tamanho, "total": total}


def resumir_analises(
    colecao: Collection,
    *,
    inicio: date | None = None,
    fim: date | None = None,
    sentimento: str | None = None,
    assunto: str | None = None,
) -> dict[str, Any]:
    filtro = _filtro_consulta(inicio, fim, sentimento, assunto)
    contagens = {classe: 0 for classe in ("positivo", "negativo", "neutro")}
    try:
        for grupo in colecao.aggregate([
            {"$match": filtro},
            {"$group": {"_id": "$sentimento", "total": {"$sum": 1}}},
        ]):
            if grupo.get("_id") in contagens:
                contagens[grupo["_id"]] = grupo["total"]
        sem_data = 0
        if inicio is not None or fim is not None:
            # Mesmos filtros, menos o período: quantos textos sem data ficaram de fora.
            filtro_sem_data = _filtro_consulta(sentimento=sentimento, assunto=assunto)
            filtro_sem_data["data_publicacao"] = None
            sem_data = colecao.count_documents(filtro_sem_data)
    except PyMongoError:
        raise ErroLeituraAnalises(
            "Falha ao consultar o MongoDB; verifique a conexão."
        ) from None
    return {
        "total": sum(contagens.values()),
        "por_sentimento": contagens,
        "sem_data_publicacao": sem_data,
    }


def _serializar_data_iso(valor: Any) -> str | None:
    if valor is None:
        return None
    if isinstance(valor, datetime):
        data = (valor if valor.tzinfo is not None else valor.replace(tzinfo=UTC)).astimezone(
            UTC
        )
        data = data.replace(microsecond=(data.microsecond // 1000) * 1000)
        return data.isoformat().replace("+00:00", "Z")
    if isinstance(valor, date):
        return datetime(valor.year, valor.month, valor.day, tzinfo=UTC).isoformat().replace(
            "+00:00", "Z"
        )
    return str(valor)


def _normalizar_data_registro(valor: Any) -> datetime | str | None:
    if valor is None:
        return None
    if isinstance(valor, datetime):
        data = (valor if valor.tzinfo is not None else valor.replace(tzinfo=UTC)).astimezone(
            UTC
        )
        return data.replace(microsecond=(data.microsecond // 1000) * 1000)
    if isinstance(valor, date):
        return datetime(valor.year, valor.month, valor.day, tzinfo=UTC)
    if isinstance(valor, str):
        texto = valor.strip()
        if not texto:
            return None
        if len(texto) == 10:
            try:
                calendario = date.fromisoformat(texto)
            except ValueError:
                return texto
            return datetime(calendario.year, calendario.month, calendario.day, tzinfo=UTC)
        try:
            data = datetime.fromisoformat(texto.replace("Z", "+00:00"))
        except ValueError:
            return texto
        data = (data if data.tzinfo is not None else data.replace(tzinfo=UTC)).astimezone(UTC)
        return data.replace(microsecond=(data.microsecond // 1000) * 1000)
    return str(valor)


def normalizar_fonte(valor: Any) -> str:
    """Remove espaços extras da fonte preservando grafia legível."""
    if not isinstance(valor, str):
        return ""
    return " ".join(valor.strip().split())


def _id_origem_valido(bruto: Any) -> str | None:
    """Valida `id_origem` aceitando texto não nulo ou inteiro finito sem sentinela."""
    if bruto is None or isinstance(bruto, (bool, dict, list, tuple, set, bytes, bytearray)):
        return None
    if isinstance(bruto, float):
        if not math.isfinite(bruto) or not bruto.is_integer():
            return None
        return str(int(bruto))
    if isinstance(bruto, int):
        return str(bruto)
    if not isinstance(bruto, str):
        return None
    identificador = " ".join(bruto.strip().split())
    if not identificador or identificador.casefold() in _IDENTIFICADORES_INVALIDOS:
        return None
    return identificador


def garantir_id_origem(registro: Mapping[str, Any]) -> str:
    """Retorna o identificador de origem ou gera hash SHA-256 determinístico."""
    identificador = _id_origem_valido(registro.get("id_origem"))
    if identificador is not None:
        return identificador

    fonte = normalizar_fonte(registro.get("fonte")).casefold()
    texto = " ".join(str(registro.get("texto_original") or "").split())
    data_chave = _serializar_data_iso(_normalizar_data_registro(registro.get("data_publicacao"))) or ""
    payload = f"{fonte}\0{texto}\0{data_chave}".encode()
    return f"auto_{hashlib.sha256(payload).hexdigest()[:24]}"


def chave_natural_registro(registro: Mapping[str, Any]) -> tuple[str, str]:
    """Chave lógica estável `(fonte normalizada, id_origem)` para deduplicação."""
    return (normalizar_fonte(registro.get("fonte")).casefold(), garantir_id_origem(registro))


def _normalizar_registro_bruto(
    registro: Mapping[str, Any],
    *,
    origem_coleta: str | None = None,
) -> dict[str, Any]:
    if not isinstance(registro, Mapping):
        raise ErroAnaliseInvalida("Cada registro deve ser um mapeamento válido.")
    fonte_bruta = registro.get("fonte")
    texto_bruto = registro.get("texto_original")
    fonte = normalizar_fonte(fonte_bruta)
    if not fonte:
        raise ErroAnaliseInvalida("Campo obrigatório ausente ou vazio: fonte")
    if not isinstance(texto_bruto, str) or not texto_bruto.strip():
        raise ErroAnaliseInvalida("Campo obrigatório ausente ou vazio: texto_original")

    id_origem = garantir_id_origem(registro)
    documento: dict[str, Any] = {
        "id_origem": id_origem,
        "fonte": fonte,
        "texto_original": texto_bruto,
    }

    texto_tratado = registro.get("texto_tratado")
    if isinstance(texto_tratado, str) and texto_tratado.strip():
        documento["texto_tratado"] = texto_tratado.strip()

    for campo in ("rotulo_original", "rotulo_padronizado"):
        valor = registro.get(campo)
        if valor is not None:
            texto = str(valor).strip()
            if texto:
                documento[campo] = texto

    data_publicacao = _normalizar_data_registro(registro.get("data_publicacao"))
    if data_publicacao is not None:
        documento["data_publicacao"] = data_publicacao

    metadados = registro.get("metadados")
    if metadados is not None:
        if not isinstance(metadados, Mapping):
            raise ErroAnaliseInvalida("metadados precisa ser um dicionário válido.")
        if metadados:
            documento["metadados"] = dict(metadados)

    if isinstance(origem_coleta, str) and origem_coleta.strip():
        documento["origem_coleta"] = origem_coleta.strip()

    return documento


def _serializar_registro_base(doc: Mapping[str, Any]) -> dict[str, Any] | None:
    if not all(
        isinstance(doc.get(campo), str) and doc[campo].strip()
        for campo in CAMPOS_TEXTO_OBRIGATORIOS
    ):
        return None
    registro: dict[str, Any] = {
        "id_origem": doc["id_origem"].strip(),
        "fonte": doc["fonte"].strip(),
        "texto_original": doc["texto_original"],
    }
    texto_tratado = doc.get("texto_tratado")
    if isinstance(texto_tratado, str) and texto_tratado.strip():
        registro["texto_tratado"] = texto_tratado.strip()
    for campo in ("rotulo_original", "rotulo_padronizado"):
        if doc.get(campo) is not None:
            registro[campo] = doc[campo]
    if doc.get("data_publicacao") is not None:
        registro["data_publicacao"] = _serializar_data_iso(doc["data_publicacao"])
    if isinstance(doc.get("metadados"), Mapping) and doc["metadados"]:
        registro["metadados"] = dict(doc["metadados"])
    return registro


def _reconciliar_fontes_existentes(
    col_registros: Collection,
    por_chave: Mapping[tuple[str, str], dict[str, Any]],
) -> dict[tuple[str, str], str]:
    """Reaproveita a grafia de `fonte` já persistida quando difere apenas em caixa."""
    fontes_existentes: dict[tuple[str, str], str] = {}
    ids_lote = list({id_origem for _, id_origem in por_chave})
    try:
        for inicio in range(0, len(ids_lote), TAMANHO_LOTE_CONSULTA_CHAVES):
            sub_ids = ids_lote[inicio : inicio + TAMANHO_LOTE_CONSULTA_CHAVES]
            encontrados = col_registros.find(
                {"id_origem": {"$in": sub_ids}},
                {"_id": 0, "fonte": 1, "id_origem": 1},
            )
            if not isinstance(encontrados, Iterable):
                continue
            for doc_ex in encontrados:
                if not isinstance(doc_ex, Mapping):
                    continue
                f_ex = doc_ex.get("fonte")
                i_ex = doc_ex.get("id_origem")
                if isinstance(f_ex, str) and isinstance(i_ex, str):
                    chave_ex = (normalizar_fonte(f_ex).casefold(), i_ex.strip())
                    if chave_ex in por_chave:
                        fontes_existentes.setdefault(chave_ex, f_ex)
    except PyMongoError:
        raise ErroLeituraAnalises(
            "Falha ao consultar registros no MongoDB; verifique a conexão."
        ) from None
    return fontes_existentes


def _compensar_registros_dataset(
    colecao: Collection,
    *,
    dataset_id: str,
    chaves: list[dict[str, str]],
    chaves_inseridas: list[dict[str, str]],
) -> None:
    """Remove vínculos e registros órfãos caso a gravação em `datasets` falhe."""
    with suppress(Exception):
        col_registros = _colecao_auxiliar(colecao, NOME_COLECAO_REGISTROS)
        for inicio in range(0, len(chaves), TAMANHO_LOTE_CONSULTA_CHAVES):
            lote = chaves[inicio : inicio + TAMANHO_LOTE_CONSULTA_CHAVES]
            col_registros.update_many(
                {"$or": [{"fonte": c["fonte"], "id_origem": c["id_origem"]} for c in lote]},
                {"$pull": {"ids_datasets": dataset_id}},
            )
        for inicio in range(0, len(chaves_inseridas), TAMANHO_LOTE_CONSULTA_CHAVES):
            lote_ins = chaves_inseridas[inicio : inicio + TAMANHO_LOTE_CONSULTA_CHAVES]
            col_registros.delete_many(
                {
                    "$or": [
                        {"fonte": c["fonte"], "id_origem": c["id_origem"]}
                        for c in lote_ins
                    ],
                    "ids_datasets": {"$size": 0},
                }
            )


def salvar_registros(
    colecao: Collection,
    registros: Iterable[Mapping[str, Any]],
    *,
    id_dataset: str | None = None,
    origem_coleta: str | None = None,
) -> dict[str, Any]:
    """Persiste registros brutos na coleção `registros` com upsert por `(fonte, id_origem)`."""
    col_registros = _colecao_auxiliar(colecao, NOME_COLECAO_REGISTROS)
    por_chave: dict[tuple[str, str], dict[str, Any]] = {}
    recebidos = 0
    for item in registros:
        recebidos += 1
        normalizado = _normalizar_registro_bruto(item, origem_coleta=origem_coleta)
        chave = (normalizar_fonte(normalizado["fonte"]).casefold(), normalizado["id_origem"])
        if chave not in por_chave:
            por_chave[chave] = normalizado
        else:
            existente_lote = por_chave[chave]
            fonte_original = existente_lote["fonte"]
            meta_ant = existente_lote.get("metadados")
            meta_nov = normalizado.get("metadados")
            existente_lote.update(normalizado)
            existente_lote["fonte"] = fonte_original
            if isinstance(meta_ant, dict) and isinstance(meta_nov, dict):
                existente_lote["metadados"] = {**meta_ant, **meta_nov}

    if not por_chave:
        return {
            "recebidos": recebidos,
            "inseridos": 0,
            "existentes": 0,
            "chaves": [],
            "chaves_inseridas": [],
        }

    fontes_existentes = _reconciliar_fontes_existentes(col_registros, por_chave)
    agora = datetime.now(UTC)
    operacoes: list[UpdateOne] = []
    chaves_ordenadas: list[dict[str, str]] = []
    for (fonte_cf, id_origem), doc in por_chave.items():
        fonte_canonica = fontes_existentes.get((fonte_cf, id_origem), doc["fonte"])
        chaves_ordenadas.append({"fonte": fonte_canonica, "id_origem": id_origem})
        campos_set: dict[str, Any] = {
            "texto_original": doc["texto_original"],
            "atualizado_em": agora,
        }
        for opcional in (
            "texto_tratado",
            "rotulo_original",
            "rotulo_padronizado",
            "data_publicacao",
            "metadados",
        ):
            if opcional in doc:
                campos_set[opcional] = doc[opcional]

        campos_insert: dict[str, Any] = {
            "fonte": fonte_canonica,
            "id_origem": id_origem,
            "criado_em": agora,
        }
        if "origem_coleta" in doc:
            campos_insert["origem_coleta"] = doc["origem_coleta"]

        atualizacao: dict[str, Any] = {
            "$set": campos_set,
            "$setOnInsert": campos_insert,
        }
        if isinstance(id_dataset, str) and id_dataset.strip():
            atualizacao["$addToSet"] = {"ids_datasets": id_dataset.strip()}

        operacoes.append(
            UpdateOne(
                {"fonte": fonte_canonica, "id_origem": id_origem},
                atualizacao,
                upsert=True,
            )
        )

    try:
        resultado = col_registros.bulk_write(operacoes, ordered=False)
    except PyMongoError:
        raise ErroLeituraAnalises(
            "Falha ao salvar registros no MongoDB; verifique a conexão."
        ) from None

    upserted_ids = getattr(resultado, "upserted_ids", None)
    if isinstance(upserted_ids, Mapping):
        chaves_inseridas = [
            chaves_ordenadas[idx]
            for idx in sorted(upserted_ids)
            if isinstance(idx, int) and 0 <= idx < len(chaves_ordenadas)
        ]
    else:
        inseridos_fallback = int(getattr(resultado, "upserted_count", 0) or 0)
        matched_fallback = int(getattr(resultado, "matched_count", 0) or 0)
        chaves_inseridas = (
            list(chaves_ordenadas)
            if inseridos_fallback > 0 and matched_fallback == 0
            else []
        )

    return {
        "recebidos": recebidos,
        "inseridos": int(getattr(resultado, "upserted_count", 0) or 0),
        "existentes": int(getattr(resultado, "matched_count", 0) or 0),
        "chaves": chaves_ordenadas,
        "chaves_inseridas": chaves_inseridas,
    }


def salvar_dataset(
    colecao: Collection,
    nome_arquivo: str,
    registros: Iterable[Mapping[str, Any]],
    *,
    id_dataset: str | None = None,
    tipo: str = "upload_csv",
    origem_coleta: str | None = None,
    metadados: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Persiste registros e metadados de um dataset no MongoDB de forma idempotente."""
    if not isinstance(nome_arquivo, str) or not nome_arquivo.strip():
        raise ErroAnaliseInvalida("nome_arquivo deve ser texto não vazio.")

    dataset_id = (
        id_dataset.strip()
        if isinstance(id_dataset, str) and id_dataset.strip()
        else f"ds_{uuid4().hex[:12]}"
    )
    lista_registros = [dict(r) for r in registros]
    resumo_escrita = salvar_registros(
        colecao,
        lista_registros,
        id_dataset=dataset_id,
        origem_coleta=origem_coleta,
    )
    chaves = resumo_escrita["chaves"]
    col_datasets = _colecao_auxiliar(colecao, NOME_COLECAO_DATASETS)
    agora = datetime.now(UTC)

    campos_set: dict[str, Any] = {
        "nome_arquivo": nome_arquivo.strip(),
        "tipo": tipo,
        "quantidade_registros": len(chaves),
        "atualizado_em": agora,
    }
    if len(chaves) <= LIMITE_CHAVES_EMBEDDED_DATASET:
        campos_set["chaves_registros"] = chaves
    if metadados:
        campos_set["metadados"] = dict(metadados)

    try:
        col_datasets.update_one(
            {"id_dataset": dataset_id},
            {
                "$set": campos_set,
                "$setOnInsert": {"id_dataset": dataset_id, "criado_em": agora},
            },
            upsert=True,
        )
    except PyMongoError:
        _compensar_registros_dataset(
            colecao,
            dataset_id=dataset_id,
            chaves=chaves,
            chaves_inseridas=resumo_escrita.get("chaves_inseridas", []),
        )
        raise ErroLeituraAnalises(
            "Falha ao salvar metadados do dataset no MongoDB; verifique a conexão."
        ) from None

    registros_serializados = [
        serializado
        for item in lista_registros
        if (
            serializado := _serializar_registro_base(
                _normalizar_registro_bruto(item, origem_coleta=origem_coleta)
            )
        )
        is not None
    ]
    return {
        "id_dataset": dataset_id,
        "nome_arquivo": nome_arquivo.strip(),
        "tipo": tipo,
        "quantidade_registros": len(chaves),
        "registros": registros_serializados,
    }


def possui_dataset(colecao: Collection, id_dataset: str) -> bool:
    """Informa se o dataset existe íntegro no MongoDB."""
    if not isinstance(id_dataset, str) or not id_dataset.strip():
        return False
    dataset_id = id_dataset.strip()
    col_datasets = _colecao_auxiliar(colecao, NOME_COLECAO_DATASETS)
    try:
        doc = col_datasets.find_one(
            {"id_dataset": dataset_id},
            {"_id": 1, "quantidade_registros": 1},
        )
        if doc is None:
            return False
        if int(doc.get("quantidade_registros") or 0) > 0:
            col_registros = _colecao_auxiliar(colecao, NOME_COLECAO_REGISTROS)
            return col_registros.find_one({"ids_datasets": dataset_id}, {"_id": 1}) is not None
        return True
    except PyMongoError:
        raise ErroLeituraAnalises(
            "Falha ao consultar datasets no MongoDB; verifique a conexão."
        ) from None


def _carregar_registros_dataset(
    colecao: Collection,
    doc_dataset: Mapping[str, Any],
) -> list[dict[str, Any]]:
    col_registros = _colecao_auxiliar(colecao, NOME_COLECAO_REGISTROS)
    id_dataset = doc_dataset["id_dataset"]
    try:
        docs = list(col_registros.find({"ids_datasets": id_dataset}, {"_id": 0}))
    except PyMongoError:
        raise ErroLeituraAnalises(
            "Falha ao carregar registros do dataset no MongoDB; verifique a conexão."
        ) from None

    por_chave: dict[tuple[str, str], dict[str, Any]] = {}
    serializados: list[dict[str, Any]] = []
    for doc in docs:
        item = _serializar_registro_base(doc)
        if item is None:
            continue
        chave = (normalizar_fonte(item["fonte"]).casefold(), item["id_origem"])
        por_chave[chave] = item
        serializados.append(item)

    chaves_ordenadas = doc_dataset.get("chaves_registros")
    if not isinstance(chaves_ordenadas, list) or not chaves_ordenadas:
        return serializados

    ordenados: list[dict[str, Any]] = []
    usados: set[tuple[str, str]] = set()
    for ref in chaves_ordenadas:
        if not isinstance(ref, Mapping):
            continue
        id_ref = ref.get("id_origem")
        chave = (
            normalizar_fonte(ref.get("fonte")).casefold(),
            id_ref.strip() if isinstance(id_ref, str) else "",
        )
        if chave in por_chave and chave not in usados:
            ordenados.append(por_chave[chave])
            usados.add(chave)
    for item in serializados:
        chave = (normalizar_fonte(item["fonte"]).casefold(), item["id_origem"])
        if chave not in usados:
            ordenados.append(item)
    return ordenados


def obter_dataset(
    colecao: Collection,
    id_dataset: str,
    *,
    incluir_registros: bool = True,
) -> dict[str, Any] | None:
    """Recupera metadados (e opcionalmente os registros ordenados) de um dataset."""
    if not isinstance(id_dataset, str) or not id_dataset.strip():
        return None
    col_datasets = _colecao_auxiliar(colecao, NOME_COLECAO_DATASETS)
    try:
        doc = col_datasets.find_one({"id_dataset": id_dataset.strip()}, {"_id": 0})
    except PyMongoError:
        raise ErroLeituraAnalises(
            "Falha ao consultar dataset no MongoDB; verifique a conexão."
        ) from None
    if doc is None:
        return None

    saida: dict[str, Any] = {
        "id_dataset": doc["id_dataset"],
        "nome_arquivo": doc["nome_arquivo"],
        "tipo": doc.get("tipo", "upload_csv"),
        "quantidade_registros": doc.get("quantidade_registros", 0),
    }
    if incluir_registros:
        saida["registros"] = _carregar_registros_dataset(colecao, doc)
    return saida


def listar_datasets(
    colecao: Collection,
    *,
    incluir_registros: bool = False,
) -> list[dict[str, Any]]:
    """Lista os datasets persistidos ordenados pela criação."""
    col_datasets = _colecao_auxiliar(colecao, NOME_COLECAO_DATASETS)
    try:
        docs = list(
            col_datasets.find({}, {"_id": 0}).sort([("criado_em", ASCENDING), ("id_dataset", ASCENDING)])
        )
    except PyMongoError:
        raise ErroLeituraAnalises(
            "Falha ao listar datasets no MongoDB; verifique a conexão."
        ) from None

    datasets: list[dict[str, Any]] = []
    for doc in docs:
        item: dict[str, Any] = {
            "id_dataset": doc["id_dataset"],
            "nome_arquivo": doc["nome_arquivo"],
            "tipo": doc.get("tipo", "upload_csv"),
            "quantidade_registros": doc.get("quantidade_registros", 0),
        }
        if incluir_registros:
            item["registros"] = _carregar_registros_dataset(colecao, doc)
        datasets.append(item)
    return datasets


def listar_registros_base(colecao: Collection) -> list[dict[str, Any]]:
    """Recupera a base persistida combinando `registros` e `analises` sem duplicatas."""
    projecao = {
        "_id": 0,
        "id_origem": 1,
        "fonte": 1,
        "texto_original": 1,
        "texto_tratado": 1,
        "data_publicacao": 1,
        "rotulo_original": 1,
        "rotulo_padronizado": 1,
        "metadados": 1,
    }
    documentos_registros: list[dict[str, Any]] = []
    try:
        database = getattr(colecao, "database", None)
        if database is not None and hasattr(database, "__getitem__"):
            col_registros = _colecao_auxiliar(colecao, NOME_COLECAO_REGISTROS)
            documentos_registros = list(col_registros.find({}, projecao))
        documentos_analises = list(colecao.find({}, projecao))
    except PyMongoError:
        raise ErroLeituraAnalises(
            "Falha ao consultar o MongoDB; verifique a conexão."
        ) from None

    por_chave: dict[tuple[str, str], dict[str, Any]] = {}
    for origem_docs in (documentos_registros, documentos_analises):
        for doc in origem_docs:
            registro = _serializar_registro_base(doc)
            if registro is None:
                continue
            chave = (normalizar_fonte(registro["fonte"]).casefold(), registro["id_origem"])
            if chave not in por_chave:
                por_chave[chave] = registro
            else:
                existente = por_chave[chave]
                for campo in (
                    "texto_tratado",
                    "rotulo_original",
                    "rotulo_padronizado",
                    "data_publicacao",
                    "metadados",
                ):
                    if campo not in existente and campo in registro:
                        existente[campo] = registro[campo]

    return list(por_chave.values())


def obter_analises_por_chaves(
    colecao: Collection,
    chaves: Iterable[tuple[str, str]],
) -> dict[tuple[str, str], dict[str, Any]]:
    """Busca análises já persistidas para o conjunto de chaves `(fonte normalizada, id_origem)`."""
    por_id: dict[str, set[str]] = {}
    for fonte, id_origem in chaves:
        fonte_cf = normalizar_fonte(fonte).casefold()
        id_limpo = id_origem.strip() if isinstance(id_origem, str) else ""
        if not fonte_cf or not id_limpo:
            continue
        por_id.setdefault(id_limpo, set()).add(fonte_cf)

    ids_unicos = list(por_id)
    if not ids_unicos:
        return {}

    encontradas: dict[tuple[str, str], dict[str, Any]] = {}
    try:
        for inicio in range(0, len(ids_unicos), TAMANHO_LOTE_CONSULTA_CHAVES):
            lote_ids = ids_unicos[inicio : inicio + TAMANHO_LOTE_CONSULTA_CHAVES]
            filtro = {"id_origem": {"$in": lote_ids}}
            for doc in colecao.find(filtro, {"_id": 0}):
                fonte_doc = doc.get("fonte")
                id_doc = doc.get("id_origem")
                if isinstance(fonte_doc, str) and isinstance(id_doc, str):
                    chave = (normalizar_fonte(fonte_doc).casefold(), id_doc.strip())
                    if chave[0] in por_id.get(chave[1], ()):
                        encontradas[chave] = doc
    except PyMongoError:
        raise ErroLeituraAnalises(
            "Falha ao consultar análises existentes no MongoDB; verifique a conexão."
        ) from None
    return encontradas


def normalizar_consulta_pesquisa(consulta: str) -> str:
    """Normaliza consulta de busca (minúsculas, sem acentos e espaços colapsados)."""
    if not isinstance(consulta, str):
        raise ErroConsultaInvalida("consulta deve ser texto não vazio.")
    decomposto = unicodedata.normalize("NFKD", consulta.casefold())
    sem_acentos = "".join(c for c in decomposto if not unicodedata.combining(c))
    tokens = re.findall(r"\w+", sem_acentos)
    normalizada = " ".join(tokens) if tokens else " ".join(sem_acentos.split())
    if not normalizada:
        raise ErroConsultaInvalida("consulta deve ser texto não vazio.")
    return normalizada


def montar_chave_cache_pesquisa(
    consulta: str,
    *,
    complementar_com_x: bool = True,
) -> dict[str, Any]:
    """Monta a chave exata de cache da pesquisa híbrida."""
    consulta_normalizada = normalizar_consulta_pesquisa(consulta)
    chave_cache = f"{consulta_normalizada}|x:{1 if complementar_com_x else 0}"
    return {
        "chave_cache": chave_cache,
        "consulta_normalizada": consulta_normalizada,
        "complementar_com_x": bool(complementar_com_x),
    }


def buscar_cache_pesquisa(
    colecao: Collection,
    consulta: str,
    *,
    complementar_com_x: bool = True,
) -> dict[str, Any] | None:
    """Retorna cache exato de pesquisa equivalente, nunca por substring parcial."""
    espec = montar_chave_cache_pesquisa(consulta, complementar_com_x=complementar_com_x)
    col_pesquisas = _colecao_auxiliar(colecao, NOME_COLECAO_PESQUISAS)
    try:
        cache = col_pesquisas.find_one({"chave_cache": espec["chave_cache"]}, {"_id": 0})
    except PyMongoError:
        raise ErroLeituraAnalises(
            "Falha ao consultar cache de pesquisa no MongoDB; verifique a conexão."
        ) from None
    if cache is None:
        return None
    # Passados 30 dias, a mesma pesquisa pode voltar ao X (decisão da PO).
    atualizado_em = cache.get("atualizado_em")
    if isinstance(atualizado_em, datetime):
        if atualizado_em.tzinfo is None:
            atualizado_em = atualizado_em.replace(tzinfo=UTC)
        if datetime.now(UTC) - atualizado_em > VALIDADE_CACHE_PESQUISA:
            return None
    return cache


def _dia_utc(agora: datetime | None = None) -> str:
    return (agora or datetime.now(UTC)).astimezone(UTC).date().isoformat()


def contar_buscas_x_publicas(colecao: Collection, agora: datetime | None = None) -> int:
    """Quantas buscas no X o Usuário já fez hoje (dia em UTC), somando todos."""
    col = _colecao_auxiliar(colecao, NOME_COLECAO_BUSCAS_X_PUBLICAS)
    try:
        return len(list(col.find({"dia": _dia_utc(agora)}, {"_id": 1})))
    except PyMongoError:
        raise ErroLeituraAnalises(
            "Falha ao consultar o limite de buscas no X; verifique a conexão."
        ) from None


def reservar_busca_x_publica(
    colecao: Collection, termo: str, limite: int, agora: datetime | None = None
) -> bool:
    """Reserva uma das buscas do dia; devolve False se o limite já foi atingido.

    Grava a reserva e só depois conta as do dia. Se o total passou do limite, esta
    reserva desiste e se apaga. Duas buscas exatamente ao mesmo tempo podem desistir
    juntas na última vaga, mas o limite nunca é ultrapassado. O contador fica no
    MongoDB e sobrevive a reinícios.
    """
    agora = (agora or datetime.now(UTC)).astimezone(UTC)
    dia = _dia_utc(agora)
    marca = uuid4().hex
    col = _colecao_auxiliar(colecao, NOME_COLECAO_BUSCAS_X_PUBLICAS)
    try:
        col.update_one(
            {"marca": marca},
            {"$set": {"dia": dia, "termo": " ".join(termo.split()), "criado_em": agora}},
            upsert=True,
        )
        if len(list(col.find({"dia": dia}, {"_id": 1}))) <= limite:
            return True
        col.delete_many({"marca": marca})
        return False
    except PyMongoError:
        raise ErroLeituraAnalises(
            "Falha ao registrar a busca no X; verifique a conexão."
        ) from None


def salvar_cache_pesquisa(
    colecao: Collection,
    consulta: str,
    *,
    complementar_com_x: bool,
    quantidade_solicitada: int,
    quantidade_atendida: int,
    esgotado_na_origem: bool,
    origem: dict[str, int] | None = None,
    chaves_registros: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    """Persiste ou atualiza cache de pesquisa concluída na coleção `pesquisas`."""
    espec = montar_chave_cache_pesquisa(consulta, complementar_com_x=complementar_com_x)
    col_pesquisas = _colecao_auxiliar(colecao, NOME_COLECAO_PESQUISAS)
    agora = datetime.now(UTC)

    campos_set: dict[str, Any] = {
        "consulta_original": " ".join(consulta.split()),
        "consulta_normalizada": espec["consulta_normalizada"],
        "complementar_com_x": espec["complementar_com_x"],
        "quantidade_solicitada": int(quantidade_solicitada),
        "quantidade_atendida": int(quantidade_atendida),
        "esgotado_na_origem": bool(esgotado_na_origem),
        "atualizado_em": agora,
    }
    if origem is not None:
        campos_set["origem"] = dict(origem)
    if chaves_registros is not None:
        campos_set["chaves_registros"] = list(chaves_registros)

    try:
        col_pesquisas.update_one(
            {"chave_cache": espec["chave_cache"]},
            {
                "$set": campos_set,
                "$setOnInsert": {"chave_cache": espec["chave_cache"], "criado_em": agora},
            },
            upsert=True,
        )
    except PyMongoError:
        raise ErroLeituraAnalises(
            "Falha ao salvar cache de pesquisa no MongoDB; verifique a conexão."
        ) from None

    return {"chave_cache": espec["chave_cache"], **campos_set}


class RepositorioAnalises:
    """Repositório canônico para persistência e consulta no MongoDB."""

    def __init__(self, colecao: Collection) -> None:
        self.colecao = colecao
        self._indices_complementares_garantidos = False

    def _garantir_indices_complementares(self) -> None:
        if not self._indices_complementares_garantidos and isinstance(self.colecao, Collection):
            criar_indices_complementares(self.colecao)
            self._indices_complementares_garantidos = True

    def criar_indices(self):
        return criar_indices(self.colecao)

    def criar_indices_complementares(self):
        return criar_indices_complementares(self.colecao)

    def buscar_por_id_origem(self, fonte: str, id_origem: str) -> dict[str, Any] | None:
        return buscar_por_id_origem(self.colecao, fonte, id_origem)

    def buscar_por_id(self, id_documento: str | ObjectId) -> dict[str, Any] | None:
        return buscar_por_id(self.colecao, id_documento)

    def salvar_analise(self, documento: dict[str, Any]) -> bool:
        return salvar_analise(self.colecao, documento)

    def salvar_analises(self, documentos: Iterable[dict[str, Any]]) -> dict[str, int]:
        return salvar_analises(self.colecao, list(documentos))

    def listar_analises(
        self,
        *,
        inicio: date | None = None,
        fim: date | None = None,
        sentimento: str | None = None,
        pagina: int = 1,
        tamanho: int = 20,
        assunto: str | None = None,
    ) -> dict[str, Any]:
        return listar_analises(
            self.colecao,
            inicio=inicio,
            fim=fim,
            sentimento=sentimento,
            pagina=pagina,
            tamanho=tamanho,
            assunto=assunto,
        )

    def resumir_analises(
        self,
        *,
        inicio: date | None = None,
        fim: date | None = None,
        sentimento: str | None = None,
        assunto: str | None = None,
    ) -> dict[str, Any]:
        return resumir_analises(
            self.colecao,
            inicio=inicio,
            fim=fim,
            sentimento=sentimento,
            assunto=assunto,
        )

    def listar_registros_base(self) -> list[dict[str, Any]]:
        self._garantir_indices_complementares()
        return listar_registros_base(self.colecao)

    def salvar_registros(
        self,
        registros: Iterable[Mapping[str, Any]],
        *,
        id_dataset: str | None = None,
        origem_coleta: str | None = None,
    ) -> dict[str, Any]:
        self._garantir_indices_complementares()
        return salvar_registros(
            self.colecao,
            registros,
            id_dataset=id_dataset,
            origem_coleta=origem_coleta,
        )

    def salvar_dataset(
        self,
        nome_arquivo: str,
        registros: Iterable[Mapping[str, Any]],
        *,
        id_dataset: str | None = None,
        tipo: str = "upload_csv",
        origem_coleta: str | None = None,
        metadados: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        self._garantir_indices_complementares()
        return salvar_dataset(
            self.colecao,
            nome_arquivo,
            registros,
            id_dataset=id_dataset,
            tipo=tipo,
            origem_coleta=origem_coleta,
            metadados=metadados,
        )

    def possui_dataset(self, id_dataset: str) -> bool:
        self._garantir_indices_complementares()
        return possui_dataset(self.colecao, id_dataset)

    def obter_dataset(
        self, id_dataset: str, *, incluir_registros: bool = True
    ) -> dict[str, Any] | None:
        self._garantir_indices_complementares()
        return obter_dataset(self.colecao, id_dataset, incluir_registros=incluir_registros)

    def listar_datasets(self, *, incluir_registros: bool = False) -> list[dict[str, Any]]:
        self._garantir_indices_complementares()
        return listar_datasets(self.colecao, incluir_registros=incluir_registros)

    def obter_analises_por_chaves(
        self, chaves: Iterable[tuple[str, str]]
    ) -> dict[tuple[str, str], dict[str, Any]]:
        return obter_analises_por_chaves(self.colecao, chaves)

    def contar_buscas_x_publicas(self, agora: datetime | None = None) -> int:
        return contar_buscas_x_publicas(self.colecao, agora)

    def reservar_busca_x_publica(
        self, termo: str, limite: int, agora: datetime | None = None
    ) -> bool:
        return reservar_busca_x_publica(self.colecao, termo, limite, agora)

    def buscar_cache_pesquisa(
        self, consulta: str, *, complementar_com_x: bool = True
    ) -> dict[str, Any] | None:
        self._garantir_indices_complementares()
        return buscar_cache_pesquisa(
            self.colecao, consulta, complementar_com_x=complementar_com_x
        )

    def salvar_cache_pesquisa(
        self,
        consulta: str,
        *,
        complementar_com_x: bool,
        quantidade_solicitada: int,
        quantidade_atendida: int,
        esgotado_na_origem: bool,
        origem: dict[str, int] | None = None,
        chaves_registros: list[dict[str, str]] | None = None,
    ) -> dict[str, Any]:
        self._garantir_indices_complementares()
        return salvar_cache_pesquisa(
            self.colecao,
            consulta,
            complementar_com_x=complementar_com_x,
            quantidade_solicitada=quantidade_solicitada,
            quantidade_atendida=quantidade_atendida,
            esgotado_na_origem=esgotado_na_origem,
            origem=origem,
            chaves_registros=chaves_registros,
        )

