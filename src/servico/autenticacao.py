"""Autenticação do Administrador na API (issue #58).

A senha nunca fica no repositório: a API recebe só o hash scrypt dela pela variável
``SENTIA_ADMIN_SENHA_HASH``. Para gerar o hash:

    uv run python -m src.servico.autenticacao

Os tokens são opacos, expiram e ficam só na memória do processo. Reiniciar a API
encerra todas as sessões.
"""

from __future__ import annotations

import base64
import getpass
import hashlib
import hmac
import os
import secrets
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

# Custo do scrypt: cerca de 16 MiB de memória por verificação.
_SCRYPT_N = 2**14
_SCRYPT_R = 8
_SCRYPT_P = 1
_TAMANHO_HASH = 32
_PREFIXO = "scrypt"

SESSAO_MINUTOS_PADRAO = 60
MAXIMO_FALHAS_LOGIN = 5
JANELA_FALHAS_SEGUNDOS = 300


class ErroConfiguracaoAdmin(ValueError):
    """Configuração de administração ausente ou inválida, sem expor o hash."""


def gerar_hash_senha(senha: str, *, sal: bytes | None = None) -> str:
    """Gera o hash da senha no formato ``scrypt:n:r:p:sal:hash`` (base64)."""
    if not isinstance(senha, str) or not senha:
        raise ValueError("A senha não pode ser vazia.")
    sal = secrets.token_bytes(16) if sal is None else sal
    derivado = hashlib.scrypt(
        senha.encode("utf-8"),
        salt=sal,
        n=_SCRYPT_N,
        r=_SCRYPT_R,
        p=_SCRYPT_P,
        dklen=_TAMANHO_HASH,
    )
    partes = (
        _PREFIXO,
        str(_SCRYPT_N),
        str(_SCRYPT_R),
        str(_SCRYPT_P),
        base64.b64encode(sal).decode("ascii"),
        base64.b64encode(derivado).decode("ascii"),
    )
    return ":".join(partes)


def _decodificar_hash(hash_senha: str) -> tuple[int, int, int, bytes, bytes]:
    try:
        prefixo, n, r, p, sal, derivado = hash_senha.split(":")
        if prefixo != _PREFIXO:
            raise ValueError
        return (
            int(n),
            int(r),
            int(p),
            base64.b64decode(sal, validate=True),
            base64.b64decode(derivado, validate=True),
        )
    except (AttributeError, ValueError):
        raise ErroConfiguracaoAdmin(
            "SENTIA_ADMIN_SENHA_HASH não está no formato gerado por "
            "`python -m src.servico.autenticacao`."
        ) from None


def verificar_senha(senha: str, hash_senha: str) -> bool:
    """Compara a senha com o hash em tempo constante."""
    n, r, p, sal, esperado = _decodificar_hash(hash_senha)
    calculado = hashlib.scrypt(
        senha.encode("utf-8"), salt=sal, n=n, r=r, p=p, dklen=len(esperado)
    )
    return hmac.compare_digest(calculado, esperado)


@dataclass(frozen=True)
class ConfiguracaoAdmin:
    usuario: str
    hash_senha: str
    sessao_minutos: int = SESSAO_MINUTOS_PADRAO

    def __post_init__(self) -> None:
        if not self.usuario.strip():
            raise ErroConfiguracaoAdmin("SENTIA_ADMIN_USUARIO não pode ser vazio.")
        _decodificar_hash(self.hash_senha)
        if self.sessao_minutos <= 0:
            raise ErroConfiguracaoAdmin("SENTIA_SESSAO_MINUTOS deve ser maior que zero.")

    @classmethod
    def do_ambiente(cls) -> ConfiguracaoAdmin | None:
        """Lê a configuração do ambiente. Sem usuário ou hash, a administração fica desligada."""
        usuario = os.getenv("SENTIA_ADMIN_USUARIO", "").strip()
        hash_senha = os.getenv("SENTIA_ADMIN_SENHA_HASH", "").strip()
        if not usuario or not hash_senha:
            return None
        minutos = os.getenv("SENTIA_SESSAO_MINUTOS", str(SESSAO_MINUTOS_PADRAO)).strip()
        try:
            sessao_minutos = int(minutos)
        except ValueError:
            raise ErroConfiguracaoAdmin(
                "SENTIA_SESSAO_MINUTOS deve ser um número inteiro."
            ) from None
        return cls(usuario=usuario, hash_senha=hash_senha, sessao_minutos=sessao_minutos)


@dataclass(frozen=True)
class Sessao:
    usuario: str
    expira_em: datetime


def _chave_token(token: str) -> str:
    # Guarda só o resumo do token: um despejo de memória não revela tokens válidos.
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


class GerenciadorSessoes:
    """Cria, valida e revoga tokens opacos com expiração."""

    def __init__(self, relogio: Callable[[], datetime] | None = None) -> None:
        self._relogio = relogio or (lambda: datetime.now(UTC))
        self._sessoes: dict[str, Sessao] = {}
        self._trava = threading.Lock()

    def criar(self, usuario: str, duracao: timedelta) -> tuple[str, Sessao]:
        token = secrets.token_urlsafe(32)
        sessao = Sessao(usuario=usuario, expira_em=self._relogio() + duracao)
        with self._trava:
            self._remover_expiradas()
            self._sessoes[_chave_token(token)] = sessao
        return token, sessao

    def validar(self, token: str) -> Sessao | None:
        with self._trava:
            chave = _chave_token(token)
            sessao = self._sessoes.get(chave)
            if sessao is None:
                return None
            if sessao.expira_em <= self._relogio():
                del self._sessoes[chave]
                return None
            return sessao

    def revogar(self, token: str) -> None:
        with self._trava:
            self._sessoes.pop(_chave_token(token), None)

    def _remover_expiradas(self) -> None:
        agora = self._relogio()
        for chave in [c for c, s in self._sessoes.items() if s.expira_em <= agora]:
            del self._sessoes[chave]


class LimitadorTentativas:
    """Bloqueia novas tentativas depois de muitas falhas seguidas na mesma janela."""

    def __init__(
        self,
        maximo: int = MAXIMO_FALHAS_LOGIN,
        janela_segundos: float = JANELA_FALHAS_SEGUNDOS,
        relogio: Callable[[], float] = time.monotonic,
    ) -> None:
        self._maximo = maximo
        self._janela = janela_segundos
        self._relogio = relogio
        self._falhas: dict[str, list[float]] = {}
        self._trava = threading.Lock()

    def _recentes(self, chave: str) -> list[float]:
        limite = self._relogio() - self._janela
        recentes = [t for t in self._falhas.get(chave, []) if t > limite]
        if recentes:
            self._falhas[chave] = recentes
        else:
            self._falhas.pop(chave, None)
        return recentes

    def bloqueado(self, chave: str) -> bool:
        with self._trava:
            return len(self._recentes(chave)) >= self._maximo

    def registrar_falha(self, chave: str) -> None:
        with self._trava:
            self._falhas[chave] = [*self._recentes(chave), self._relogio()]

    def limpar(self, chave: str) -> None:
        with self._trava:
            self._falhas.pop(chave, None)


class Autenticador:
    """Valida credenciais do Administrador e controla as sessões."""

    def __init__(
        self,
        configuracao: ConfiguracaoAdmin | None,
        sessoes: GerenciadorSessoes | None = None,
        limitador: LimitadorTentativas | None = None,
    ) -> None:
        self.configuracao = configuracao
        self.sessoes = sessoes or GerenciadorSessoes()
        self.limitador = limitador or LimitadorTentativas()

    @property
    def configurado(self) -> bool:
        return self.configuracao is not None

    def credenciais_validas(self, usuario: str, senha: str) -> bool:
        if self.configuracao is None:
            return False
        # Verifica a senha mesmo com usuário errado, para não revelar pelo tempo
        # de resposta qual dos campos estava incorreto.
        senha_ok = verificar_senha(senha, self.configuracao.hash_senha)
        usuario_ok = hmac.compare_digest(
            usuario.encode("utf-8"), self.configuracao.usuario.encode("utf-8")
        )
        return senha_ok and usuario_ok

    def iniciar_sessao(self, usuario: str) -> tuple[str, Sessao]:
        assert self.configuracao is not None
        return self.sessoes.criar(
            usuario, timedelta(minutes=self.configuracao.sessao_minutos)
        )


def main() -> None:
    """Pede a senha no terminal e imprime o valor de SENTIA_ADMIN_SENHA_HASH."""
    senha = getpass.getpass("Senha do Administrador: ")
    if senha != getpass.getpass("Repita a senha: "):
        raise SystemExit("As senhas não conferem.")
    print(f"SENTIA_ADMIN_SENHA_HASH={gerar_hash_senha(senha)}")


if __name__ == "__main__":
    main()
