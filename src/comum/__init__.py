"""Funções puras compartilhadas entre o serviço, os dados e o painel.

Nada aqui acessa banco, rede ou interface: só regras de texto. Por isso o painel
pode importar este pacote sem quebrar a fronteira da arquitetura (2.4.2).
"""
