# Alterações: armazenamento em memória e ajustes na API

## Objetivo

Permitir que a API do SentIA trabalhe tanto com MongoDB quanto com armazenamento em memória, mantendo as mesmas rotas de consulta e processamento.

## O que foi alterado

- **Seleção do armazenamento:** a variável `SENTIA_ARMAZENAMENTO` permite escolher `mongodb` ou `memoria`. O padrão continua sendo `mongodb`.
- **Integração com a API:** as rotas de processamento, listagem e resumo identificam o tipo de repositório e chamam a implementação correspondente.
- **Consultas em memória:** foram adicionadas funções para listar e resumir análises, com filtros por período e sentimento e paginação na listagem.
- **Deduplicação:** o repositório em memória valida as análises e evita inserir novamente registros com a mesma combinação de `fonte` e `id_origem`. O salvamento informa quantos registros foram inseridos e quantos eram duplicados.
- **Lotes e exemplos:** o tamanho do lote de análise foi alterado de 32 para 100, e o limite de exemplos foi alterado de 10 para 100.

## Como usar

1. Configure o armazenamento no arquivo `.env`:
   - `SENTIA_ARMAZENAMENTO=memoria` para usar o repositório em memória.
   - `SENTIA_ARMAZENAMENTO=mongodb` para usar o MongoDB.
2. Para usar o modo MongoDB, mantenha também as configurações de conexão do banco preenchidas conforme o ambiente.
3. Inicie a API:

   ```powershell
   uv run uvicorn src.servico.main:app --reload
   ```

4. Inicie a interface, em outro terminal:

   ```powershell
   uv run streamlit run src/apresentacao/app.py
   ```

5. Utilize as rotas existentes da API. O modo de armazenamento é selecionado pela configuração; não é necessário usar endpoints diferentes.

## Observações

- O modo em memória mantém os dados no processo da aplicação; eles não devem ser considerados persistentes após reiniciar a API.
- O modo MongoDB continua disponível e é o padrão quando `SENTIA_ARMAZENAMENTO` não está definido.
- Os testes de API executados durante o desenvolvimento (`tests/test_api.py` e `tests/test_consultas_api.py`) passaram: 65 testes aprovados e 1 aviso.

