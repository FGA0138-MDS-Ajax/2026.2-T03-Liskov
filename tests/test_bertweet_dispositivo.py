"""Testes da seleção de dispositivo e da recuperação de OOM do BERTweet."""

import logging
import os
from types import SimpleNamespace

import pytest

from src.processamento.classificacao.bertweet import ClassificadorBertweet


@pytest.fixture(autouse=True)
def restaurar_mascaras_de_gpu(monkeypatch):
    # Cada teste comeca sem mascaras; monkeypatch restaura o ambiente ao final.
    monkeypatch.delenv("CUDA_VISIBLE_DEVICES", raising=False)
    monkeypatch.delenv("HIP_VISIBLE_DEVICES", raising=False)


def _resultado():
    return SimpleNamespace(
        output="POS",
        probas={"POS": 0.9, "NEG": 0.05, "NEU": 0.05},
    )


class AnalisadorSimples:
    def predict(self, textos):
        return [_resultado() for _ in textos]


def test_dispositivo_cpu_e_padrao_de_execucao(monkeypatch):
    monkeypatch.setenv("SENTIA_DISPOSITIVO", "cpu")
    chamadas = []

    def factory(**kwargs):
        chamadas.append((kwargs, __import__("os").environ.get("ACCELERATE_USE_CPU")))
        return AnalisadorSimples()

    monkeypatch.setattr(ClassificadorBertweet, "_obter_factory", staticmethod(lambda: factory))
    clf = ClassificadorBertweet()
    assert clf.dispositivo_ativo == "cpu"
    assert chamadas[0][1] == "true"
    assert clf.prever("texto") == ["positivo"]


@pytest.mark.parametrize("valor", ["gpu", "unknown", ""])
def test_rejeita_dispositivo_invalido(monkeypatch, valor):
    monkeypatch.setenv("SENTIA_DISPOSITIVO", valor)
    monkeypatch.setattr(
        ClassificadorBertweet, "_obter_factory",
        staticmethod(lambda: (lambda **kwargs: AnalisadorSimples())),
    )
    with pytest.raises(ValueError, match="SENTIA_DISPOSITIVO"):
        ClassificadorBertweet()


def test_auto_usa_cpu_quando_gpu_indisponivel(monkeypatch):
    import sys

    cuda = SimpleNamespace(
        is_initialized=lambda: False,
        is_available=lambda: False,
        device_count=lambda: 0,
    )
    monkeypatch.setitem(sys.modules, "torch", SimpleNamespace(cuda=cuda))
    monkeypatch.setenv("SENTIA_DISPOSITIVO", "auto")
    monkeypatch.setattr(
        ClassificadorBertweet, "_obter_factory",
        staticmethod(lambda: (lambda **kwargs: AnalisadorSimples())),
    )
    clf = ClassificadorBertweet()
    assert clf.dispositivo_ativo == "cpu"


def test_cuda_aplica_indice_fisico_antes_de_inicializar_runtime(monkeypatch):
    import os
    import sys

    cuda = SimpleNamespace(
        is_initialized=lambda: False,
        is_available=lambda: True,
        device_count=lambda: 1,
    )
    monkeypatch.setitem(sys.modules, "torch", SimpleNamespace(cuda=cuda))
    monkeypatch.setenv("SENTIA_DISPOSITIVO", "cuda")
    monkeypatch.setenv("SENTIA_GPU_INDEX", "1")
    monkeypatch.setattr(
        ClassificadorBertweet, "_obter_factory",
        staticmethod(lambda: (lambda **kwargs: AnalisadorSimples())),
    )
    clf = ClassificadorBertweet()
    assert clf.dispositivo_ativo == "cuda"
    assert os.environ["CUDA_VISIBLE_DEVICES"] == "1"
    assert os.environ["HIP_VISIBLE_DEVICES"] == "1"


def test_cuda_explicita_falha_se_gpu_indisponivel(monkeypatch):
    import sys

    cuda = SimpleNamespace(
        is_initialized=lambda: False,
        is_available=lambda: False,
        device_count=lambda: 0,
    )
    monkeypatch.setitem(sys.modules, "torch", SimpleNamespace(cuda=cuda))
    monkeypatch.setenv("SENTIA_DISPOSITIVO", "cuda")
    monkeypatch.setattr(
        ClassificadorBertweet, "_obter_factory",
        staticmethod(lambda: (lambda **kwargs: AnalisadorSimples())),
    )
    with pytest.raises(RuntimeError, match="não foi possível acessar a GPU"):
        ClassificadorBertweet()


def test_oom_na_gpu_recria_analisador_na_cpu_e_repete_lote(monkeypatch, caplog):
    import sys

    cuda = SimpleNamespace(
        is_initialized=lambda: False,
        is_available=lambda: True,
        device_count=lambda: 1,
        empty_cache=lambda: None,
    )
    monkeypatch.setitem(sys.modules, "torch", SimpleNamespace(cuda=cuda))
    monkeypatch.setenv("SENTIA_DISPOSITIVO", "cuda")
    chamadas_factory = []
    analisador_gpu = SimpleNamespace(
        predict=lambda textos: (_ for _ in ()).throw(
            RuntimeError("CUDA out of memory. Tried to allocate memory")
        )
    )

    def factory(**kwargs):
        chamadas_factory.append(__import__("os").environ.get("ACCELERATE_USE_CPU"))
        if len(chamadas_factory) == 1:
            return analisador_gpu
        return AnalisadorSimples()

    monkeypatch.setattr(ClassificadorBertweet, "_obter_factory", staticmethod(lambda: factory))
    with caplog.at_level(logging.WARNING):
        clf = ClassificadorBertweet()
        assert clf.prever(["texto"]) == ["positivo"]

    assert chamadas_factory == ["false", "true"]
    assert clf.dispositivo_ativo == "cpu"
    assert "Memória insuficiente na GPU" in caplog.text


def test_nao_faz_fallback_para_erros_que_nao_sao_oom(monkeypatch):
    import sys

    cuda = SimpleNamespace(
        is_initialized=lambda: False,
        is_available=lambda: True,
        device_count=lambda: 1,
    )
    monkeypatch.setitem(sys.modules, "torch", SimpleNamespace(cuda=cuda))
    monkeypatch.setenv("SENTIA_DISPOSITIVO", "cuda")
    analisador = SimpleNamespace(
        predict=lambda textos: (_ for _ in ()).throw(RuntimeError("erro de execução"))
    )
    monkeypatch.setattr(
        ClassificadorBertweet, "_obter_factory",
        staticmethod(lambda: (lambda **kwargs: analisador)),
    )
    clf = ClassificadorBertweet()
    with pytest.raises(RuntimeError, match="erro de execução"):
        clf.prever("texto")


@pytest.mark.parametrize(
    ("dispositivo", "espera_fp16"),
    [
        ("cpu", False),
        ("cuda", True),
    ],
)
def test_criar_analisador_configura_precisao(
    monkeypatch, dispositivo, espera_fp16
):
    class ModeloSimulado:
        def __init__(self):
            self.dispositivo = None
            self.fp16 = False

        def to(self, dispositivo):
            self.dispositivo = dispositivo
            return self

        def half(self):
            self.fp16 = True
            return self

    modelo = ModeloSimulado()
    analisador = SimpleNamespace(model=modelo)

    clf = ClassificadorBertweet.__new__(ClassificadorBertweet)
    clf.tamanho_lote = 32
    clf._factory = lambda **kwargs: analisador

    resultado = clf._criar_analisador(dispositivo)

    assert resultado is analisador
    assert modelo.dispositivo == dispositivo
    assert modelo.fp16 is espera_fp16

def test_auto_usa_cpu_quando_pytorch_nao_esta_instalado(
    monkeypatch, caplog
):
    import builtins

    importar_original = builtins.__import__

    def importar_sem_torch(nome, *args, **kwargs):
        if nome == "torch":
            raise ImportError("PyTorch nao instalado")
        return importar_original(nome, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", importar_sem_torch)
    monkeypatch.setenv("SENTIA_DISPOSITIVO", "auto")
    monkeypatch.setattr(
        ClassificadorBertweet,
        "_obter_factory",
        staticmethod(lambda: (lambda **kwargs: AnalisadorSimples())),
    )

    with caplog.at_level(logging.WARNING):
        clf = ClassificadorBertweet()

    assert clf.dispositivo_ativo == "cpu"
    assert "PyTorch indisponível" in caplog.text


def test_cuda_falha_quando_pytorch_nao_esta_instalado(monkeypatch):
    import builtins

    importar_original = builtins.__import__

    def importar_sem_torch(nome, *args, **kwargs):
        if nome == "torch":
            raise ImportError("PyTorch nao instalado")
        return importar_original(nome, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", importar_sem_torch)
    monkeypatch.setenv("SENTIA_DISPOSITIVO", "cuda")
    monkeypatch.setattr(
        ClassificadorBertweet,
        "_obter_factory",
        staticmethod(lambda: (lambda **kwargs: AnalisadorSimples())),
    )

    with pytest.raises(RuntimeError, match="exige PyTorch instalado"):
        ClassificadorBertweet()


def test_registra_dispositivo_selecionado_no_log(monkeypatch, caplog):
    monkeypatch.setenv("SENTIA_DISPOSITIVO", "cpu")
    monkeypatch.setattr(
        ClassificadorBertweet,
        "_obter_factory",
        staticmethod(lambda: (lambda **kwargs: AnalisadorSimples())),
    )

    with caplog.at_level(logging.INFO):
        clf = ClassificadorBertweet()

    assert clf.dispositivo_ativo == "cpu"
    assert "Dispositivo selecionado para inferência BERTweet: cpu." in caplog.text

def test_cuda_falha_se_runtime_ja_inicializado_e_indice_nao_zero(monkeypatch):
    import sys

    cuda = SimpleNamespace(
        is_initialized=lambda: True,
        is_available=lambda: True,
        device_count=lambda: 2,
    )
    monkeypatch.setitem(sys.modules, "torch", SimpleNamespace(cuda=cuda))
    monkeypatch.setenv("SENTIA_DISPOSITIVO", "cuda")
    monkeypatch.setenv("SENTIA_GPU_INDEX", "1")

    factory_chamada = []
    monkeypatch.setattr(
        ClassificadorBertweet,
        "_obter_factory",
        staticmethod(lambda: (lambda **kwargs: factory_chamada.append(kwargs))),
    )

    with pytest.raises(RuntimeError, match="reinicie o processo"):
        ClassificadorBertweet()

    assert factory_chamada == []


def test_auto_usa_cpu_se_runtime_ja_inicializado_e_indice_nao_zero(
    monkeypatch, caplog
):
    import sys

    cuda = SimpleNamespace(
        is_initialized=lambda: True,
        is_available=lambda: True,
        device_count=lambda: 2,
    )
    monkeypatch.setitem(sys.modules, "torch", SimpleNamespace(cuda=cuda))
    monkeypatch.setenv("SENTIA_DISPOSITIVO", "auto")
    monkeypatch.setenv("SENTIA_GPU_INDEX", "1")
    monkeypatch.setattr(
        ClassificadorBertweet,
        "_obter_factory",
        staticmethod(lambda: (lambda **kwargs: AnalisadorSimples())),
    )

    with caplog.at_level(logging.WARNING):
        clf = ClassificadorBertweet()

    assert clf.dispositivo_ativo == "cpu"
    assert "Usando CPU" in caplog.text


def test_analisador_com_slots_usa_predict_sem_type_error():
    class AnalisadorComSlots:
        __slots__ = ()

        def predict(self, textos):
            return [_resultado() for _ in textos]

    clf = ClassificadorBertweet.__new__(ClassificadorBertweet)
    clf._analisador = AnalisadorComSlots()

    assert clf._prever_lote(["texto"])[0].output == "POS"


def test_oom_na_inferencia_direta_recria_modelo_na_cpu(monkeypatch):
    import torch

    monkeypatch.setattr(torch.cuda, "is_initialized", lambda: False)
    monkeypatch.setattr(torch.cuda, "is_available", lambda: True)
    monkeypatch.setattr(torch.cuda, "device_count", lambda: 1)
    monkeypatch.setattr(torch.cuda, "empty_cache", lambda: None)

    monkeypatch.setenv("SENTIA_DISPOSITIVO", "cuda")

    class TokenizerSimulado:
        model_max_length = 128

        def __call__(self, textos, **kwargs):
            return {"input_ids": torch.tensor([[1] for _ in textos])}

    class ModeloSimulado:
        def __init__(self, falhar):
            self.falhar = falhar
            self.chamadas = 0
            self.parametro = torch.nn.Parameter(torch.zeros(1))

        def to(self, dispositivo):
            return self

        def half(self):
            return self

        def parameters(self):
            yield self.parametro

        def eval(self):
            return self

        def __call__(self, **entradas):
            self.chamadas += 1
            if self.falhar:
                raise RuntimeError("CUDA out of memory")

            return SimpleNamespace(
                logits=torch.tensor([[2.0, 0.5, 0.1]])
            )

    modelos = []

    def factory(**kwargs):
        falhar = len(modelos) == 0
        modelo = ModeloSimulado(falhar=falhar)
        modelos.append(modelo)

        return SimpleNamespace(
            tokenizer=TokenizerSimulado(),
            model=modelo,
            preprocessing_args={},
            _get_output=lambda texto, logits, context=None: _resultado(),
        )

    monkeypatch.setattr(
        ClassificadorBertweet,
        "_obter_factory",
        staticmethod(lambda: factory),
    )

    clf = ClassificadorBertweet()

    assert clf.dispositivo_ativo == "cuda"
    assert clf.prever("texto") == ["positivo"]

    assert len(modelos) == 2
    assert modelos[0].chamadas == 1
    assert modelos[1].chamadas == 1
    assert clf.dispositivo_ativo == "cpu"



def test_preserva_mascaras_existentes_e_rejeita_indice_nao_zero(monkeypatch):
    import sys

    cuda = SimpleNamespace(
        is_initialized=lambda: False,
        is_available=lambda: True,
        device_count=lambda: 2,
    )
    monkeypatch.setitem(sys.modules, "torch", SimpleNamespace(cuda=cuda))
    monkeypatch.setenv("SENTIA_DISPOSITIVO", "cuda")
    monkeypatch.setenv("SENTIA_GPU_INDEX", "1")
    monkeypatch.setenv("CUDA_VISIBLE_DEVICES", "0,1")
    monkeypatch.setenv("HIP_VISIBLE_DEVICES", "0,1")

    chamadas_factory = []
    monkeypatch.setattr(
        ClassificadorBertweet,
        "_obter_factory",
        staticmethod(lambda: (lambda **kwargs: chamadas_factory.append(kwargs))),
    )

    with pytest.raises(RuntimeError, match="already configured"):
        ClassificadorBertweet()

    assert os.environ["CUDA_VISIBLE_DEVICES"] == "0,1"
    assert os.environ["HIP_VISIBLE_DEVICES"] == "0,1"
    assert chamadas_factory == []


def test_preserva_mascaras_existentes_com_indice_zero(monkeypatch):
    import sys

    cuda = SimpleNamespace(
        is_initialized=lambda: False,
        is_available=lambda: True,
        device_count=lambda: 1,
    )
    monkeypatch.setitem(sys.modules, "torch", SimpleNamespace(cuda=cuda))
    monkeypatch.setenv("SENTIA_DISPOSITIVO", "cuda")
    monkeypatch.setenv("SENTIA_GPU_INDEX", "0")
    monkeypatch.setenv("CUDA_VISIBLE_DEVICES", "1")
    monkeypatch.setenv("HIP_VISIBLE_DEVICES", "1")
    monkeypatch.setattr(
        ClassificadorBertweet,
        "_obter_factory",
        staticmethod(lambda: (lambda **kwargs: AnalisadorSimples())),
    )

    clf = ClassificadorBertweet()

    assert clf.dispositivo_ativo == "cuda"
    assert os.environ["CUDA_VISIBLE_DEVICES"] == "1"
    assert os.environ["HIP_VISIBLE_DEVICES"] == "1"


def test_analisador_injetado_com_atributos_de_modelo_usa_predict():
    from unittest.mock import Mock

    analisador = SimpleNamespace(
        tokenizer=Mock(),
        model=Mock(),
        preprocessing_args={},
        _get_output=Mock(),
        predict=Mock(return_value=[_resultado()]),
    )

    clf = ClassificadorBertweet(analisador=analisador)

    assert clf.prever("texto") == ["positivo"]
    analisador.predict.assert_called_once_with(["texto"])
    analisador.tokenizer.assert_not_called()
    analisador.model.assert_not_called()
