"""Dados de exemplo FICTÍCIOS, para desenvolver o painel sem o backend.

Nada aqui representa integração concluída. Os textos são sintéticos e não têm
menções a usuários. Os registros sem data imitam o TweetSentBR, que não possui
data de publicação.
"""

from dataclasses import replace
from datetime import UTC, date, datetime, timedelta

from src.apresentacao.contrato import (
    LIMITE_TERMOS_PADRAO,
    SENTIMENTOS,
    Analise,
    ErroFonteDados,
    EvolucaoAnalises,
    FiltrosAnalises,
    Granularidade,
    PaginaAnalises,
    PontoEvolucao,
    ResumoAnalises,
    Sentimento,
    TermoFrequente,
    TermosAnalises,
)
from src.comum.busca_textual import contar_termos, corresponde


def inicio_do_periodo(dia: date, granularidade: Granularidade) -> date:
    """Mesmo agrupamento da API: semanas começam na segunda-feira."""
    if granularidade == "semana":
        return dia - timedelta(days=dia.weekday())
    if granularidade == "mes":
        return dia.replace(day=1)
    return dia

MODELO_FICTICIO = "modelo-de-exemplo"
_PROCESSADO_EM = datetime(2026, 11, 1, 12, 0, tzinfo=UTC)

_LINHAS: list[tuple[str, Sentimento, tuple[int, int, int] | None]] = [
    ("Adorei o atendimento, resolveram tudo rápido.", "positivo", (2026, 8, 3)),
    ("O produto chegou antes do prazo e funciona bem.", "positivo", (2026, 8, 12)),
    ("Experiência excelente, recomendo para todos.", "positivo", (2026, 8, 25)),
    ("Gostei bastante da nova versão do aplicativo.", "positivo", (2026, 9, 2)),
    ("Muito bom, superou o que eu esperava.", "positivo", (2026, 9, 14)),
    ("Serviço ótimo e equipe bem atenciosa.", "positivo", (2026, 10, 1)),
    ("Programa divertido, valeu a pena assistir.", "positivo", None),
    ("Que episódio bom, ri do começo ao fim.", "positivo", None),
    ("Recebi o pedido hoje pela manhã.", "neutro", (2026, 8, 9)),
    ("A loja abre às nove nos dias de semana.", "neutro", (2026, 9, 5)),
    ("Atualizei o aplicativo para a versão mais recente.", "neutro", (2026, 9, 21)),
    ("O programa passa às oito da noite.", "neutro", None),
    ("A entrega atrasou mais de duas semanas.", "negativo", (2026, 8, 18)),
    ("Atendimento péssimo, ninguém responde.", "negativo", (2026, 9, 9)),
    ("O produto veio com defeito e sem manual.", "negativo", (2026, 10, 7)),
    ("O aplicativo trava toda vez que abro.", "negativo", (2026, 10, 20)),
    ("Episódio fraco, perdi meu tempo.", "negativo", None),
]

ANALISES_DE_EXEMPLO: list[Analise] = [
    Analise(
        id_origem=f"exemplo_{indice:03d}",
        fonte="dados_de_exemplo",
        texto_original=texto,
        sentimento=sentimento,
        modelo_nome=MODELO_FICTICIO,
        data_processamento=_PROCESSADO_EM,
        data_publicacao=datetime(*data, tzinfo=UTC) if data else None,
    )
    for indice, (texto, sentimento, data) in enumerate(_LINHAS, start=1)
]


class FonteMock:
    """Imita a API: filtra, pagina e totaliza os registros recebidos."""

    def __init__(self, analises: list[Analise] | None = None) -> None:
        self._analises = ANALISES_DE_EXEMPLO if analises is None else analises

    def _filtrar(self, filtros: FiltrosAnalises) -> tuple[list[Analise], int]:
        # Mesma regra de assunto da API (src/comum/busca_textual.py).
        selecionadas = [
            a
            for a in self._analises
            if (filtros.sentimento is None or a.sentimento == filtros.sentimento)
            and (not filtros.assunto or corresponde(filtros.assunto, a.texto_original))
        ]
        if filtros.inicio is None and filtros.fim is None:
            return selecionadas, 0

        # A data de referência ainda depende de decisão (issue #24). Aqui se
        # usa provisoriamente a publicação; registros sem data ficam de fora.
        com_data = [a for a in selecionadas if a.data_publicacao is not None]
        sem_data = len(selecionadas) - len(com_data)
        no_periodo = [
            a
            for a in com_data
            if (filtros.inicio is None or a.data_publicacao.date() >= filtros.inicio)
            and (filtros.fim is None or a.data_publicacao.date() <= filtros.fim)
        ]
        return no_periodo, sem_data

    def listar(
        self, filtros: FiltrosAnalises, pagina: int = 1, tamanho: int = 20
    ) -> PaginaAnalises:
        selecionadas, _ = self._filtrar(filtros)
        inicio = (pagina - 1) * tamanho
        return PaginaAnalises(
            itens=selecionadas[inicio : inicio + tamanho],
            pagina=pagina,
            tamanho=tamanho,
            total=len(selecionadas),
        )

    def resumir(self, filtros: FiltrosAnalises) -> ResumoAnalises:
        selecionadas, sem_data = self._filtrar(filtros)
        return ResumoAnalises(
            total=len(selecionadas),
            por_sentimento={
                s: sum(a.sentimento == s for a in selecionadas) for s in SENTIMENTOS
            },
            sem_data_publicacao=sem_data,
        )


    def termos(
        self, filtros: FiltrosAnalises, limite: int = LIMITE_TERMOS_PADRAO
    ) -> TermosAnalises:
        selecionadas, _ = self._filtrar(filtros)
        contagem = contar_termos(
            [a.texto_original for a in selecionadas], limite=limite, assunto=filtros.assunto
        )
        return TermosAnalises(
            termos=[TermoFrequente(t, n) for t, n in contagem],
            textos_lidos=len(selecionadas),
            total=len(selecionadas),
        )

    def evolucao(
        self, filtros: FiltrosAnalises, granularidade: Granularidade = "semana"
    ) -> EvolucaoAnalises:
        selecionadas, _ = self._filtrar(filtros)
        sem_periodo, _ = self._filtrar(replace(filtros, inicio=None, fim=None))
        pontos: dict[date, dict[Sentimento, int]] = {}
        for analise in selecionadas:
            if analise.data_publicacao is None:
                continue
            periodo = inicio_do_periodo(analise.data_publicacao.date(), granularidade)
            contagens = pontos.setdefault(periodo, dict.fromkeys(SENTIMENTOS, 0))
            contagens[analise.sentimento] += 1
        return EvolucaoAnalises(
            granularidade=granularidade,
            pontos=[PontoEvolucao(p, c) for p, c in sorted(pontos.items())],
            sem_data_publicacao=sum(a.data_publicacao is None for a in sem_periodo),
        )


class FonteMockComErro:
    """Simula indisponibilidade, para validar o estado de erro das telas."""

    MENSAGEM = "Erro simulado: a fonte de dados está indisponível."

    def listar(
        self, filtros: FiltrosAnalises, pagina: int = 1, tamanho: int = 20
    ) -> PaginaAnalises:
        raise ErroFonteDados(self.MENSAGEM)

    def resumir(self, filtros: FiltrosAnalises) -> ResumoAnalises:
        raise ErroFonteDados(self.MENSAGEM)

    def termos(
        self, filtros: FiltrosAnalises, limite: int = LIMITE_TERMOS_PADRAO
    ) -> TermosAnalises:
        raise ErroFonteDados(self.MENSAGEM)

    def evolucao(
        self, filtros: FiltrosAnalises, granularidade: Granularidade = "semana"
    ) -> EvolucaoAnalises:
        raise ErroFonteDados(self.MENSAGEM)


