# MongoDB no desenvolvimento — configuração e verificação

Esta entrega prepara a conexão via PyMongo, sem implementar CRUD nem concluir RF08.
São aceitos MongoDB local e Atlas. Para desenvolvimento sem conta externa, prefira
um servidor local já instalado; use Atlas somente com conta, cluster e acesso
autorizados pela equipe. Os testes unitários abaixo não precisam de nenhum servidor.

## Pré-requisitos e instalação

- [uv](https://docs.astral.sh/uv/getting-started/installation/) instalado.
- Python 3.11, selecionado pela `.python-version` da migração do PR #48.
- Para o ping real: servidor local em execução **ou** cluster Atlas acessível,
  usuário de banco e permissão de acesso de rede configurados.

Referência atual: integração `bfaf7da`, 09/11/2026. O #48 já está integrado
na base (`c6fc535`); use uv diretamente na raiz:

```bash
uv sync --locked
```

`pymongo` e `python-dotenv` já estão no `pyproject.toml`; o lock também fornece
`dnspython` para URIs `mongodb+srv`. Não instale `bson` separadamente e não recrie
`requirements.txt` depois da migração.

## Configuração local

Inicie o MongoDB pelo procedimento da sua instalação e confirme a porta configurada.
Em um ambiente local sem autenticação e restrito à própria máquina, o exemplo é:

```dotenv
MONGODB_URI=mongodb://127.0.0.1:27017/sentia
```

Usar o nome `sentia` alinha a configuração ao esquema documentado. O ping usa
`client.admin.command("ping")` e não cria banco, collection, índice ou documento.
Não exponha um servidor sem autenticação fora de localhost.

## Configuração Atlas

1. Use um cluster autorizado para desenvolvimento e aguarde sua disponibilidade.
2. Configure um usuário de banco com as permissões necessárias; ele é diferente da
   conta usada para entrar no console Atlas.
3. Autorize somente os IPs necessários na configuração de acesso de rede.
4. Obtenha a string de conexão do driver Python no console e salve-a apenas no
   ambiente local. O formato ilustrativo, sem credenciais reais, é:

```dotenv
MONGODB_URI=mongodb+srv://<usuario>:<senha-codificada>@<host-do-cluster>/sentia
```

Substitua os placeholders somente no seu `.env` privado. Caracteres reservados do
usuário/senha devem ser codificados para URI. Não copie a string real para commits,
issues, PRs, relatórios, capturas de tela ou comandos que fiquem no histórico.

## Criar ou completar o .env sem sobrescrever

O arquivo `.env.example` pode ser usado como referência; `.env` é ignorado pelo Git.
Se já existir um `.env` do frontend, **preserve todas as variáveis dele** e acrescente
somente a linha `MONGODB_URI` em um editor local. Evite criar duas definições dessa
mesma variável. Não execute `cp .env.example .env` sobre um arquivo existente.

Para criar um arquivo vazio somente quando ainda não existe:

```bash
uv run python -c "from pathlib import Path; Path('.env').touch(exist_ok=True)"
```

Edite esse arquivo e adicione a URI local ou Atlas. Variável já definida no ambiente
tem prioridade sobre `.env`, conforme o comportamento padrão de `load_dotenv`.
Confira somente o estado do arquivo, sem exibir seu conteúdo:

```bash
git check-ignore .env
```

## Executar a verificação

Na raiz, com a configuração preenchida:

```bash
uv run python test_mongo.py
```

- **Código 0:** cliente criado, ping concluído e cliente encerrado; imprime sucesso.
- **Código 1:** URI ausente/vazia/inválida, falha de conexão, autenticação, timeout
  ou encerramento. Diagnóstico seguro sai em stderr, sem URI nem detalhes brutos.
- Linux/macOS: consulte `echo $?` imediatamente após o comando; PowerShell: `$LASTEXITCODE`.

O módulo não instancia cliente no import. `connect_to_mongodb()` lê a configuração,
cria uma instância nova e executa o ping. Se falhar, tenta fechar essa instância em
`finally`; no sucesso, o chamador passa a ser responsável por
`disconnect_from_mongodb(cliente)`. A CLI também usa `finally` e retorna erro se o
encerramento falhar. Falha adicional no fechamento não mascara o erro original do ping.

Em código Python é possível configurar `timeout_ms=5000` ou outro inteiro positivo
e injetar `client_factory` nos testes. O timeout vale para seleção de servidor,
estabelecimento do socket e operações de socket; não é promessa de prazo total de
execução, especialmente com resolução DNS.

## Testes sem credenciais e sem MongoDB

```bash
uv run pytest tests/test_database.py -v -ra
uv run pytest -v -ra
uv run pytest --cov=src --cov-report=term-missing
```

Os testes simulam construtor, ping, falhas, fechamento, subprocesso/exit code e
mensagens com marcadores sintéticos. Eles não comprovam conectividade real do Atlas.

## Solução básica de problemas

| Mensagem / situação | Verificações locais |
|---|---|
| Defina MONGODB_URI | Confirme o nome da variável e se está preenchida no ambiente ou `.env` da raiz. Não imprima o valor em logs. |
| Configuração inválida / DNS | Confira esquema `mongodb://` ou `mongodb+srv://`, placeholders substituídos, host, codificação das credenciais e resolução DNS/SRV. |
| Rede / timeout | Confira servidor local e porta; no Atlas, cluster disponível, IP autorizado, firewall, proxy/VPN e conectividade DNS/TLS. Não amplie acesso indiscriminadamente. |
| Operação recusada | Confira usuário de banco, senha, permissões e `authSource` quando exigido pela configuração. |
| Encerramento falhou | A execução permanece com erro; investigue o driver/ambiente sem publicar dados de conexão. |

Não remova a validação de TLS para contornar erros. Não há conexão real automática
na suíte; execute a CLI real somente contra o ambiente local/externo autorizado.

## Histórico de integração #47/#48

Os PRs #47 e #48 e suas correções já compõem `c6fc535`, ancestral da referência
PC1. As instruções anteriores para combinar requirements antigos com o ambiente
do frontend eram transitórias; não se aplicam à instalação atual. O histórico
completo foi preservado na
[revisão anterior deste documento](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/blob/ca25e1223564f55b2465f9de87672cfae878df07/docs/mongodb_setup.md).
Não restaurar requirements removidos; manifesto e lock são a fonte atual.

O PR #47 relata ping real do autor, mas esta revisão documental executa testes
com mocks; isso não é uma nova homologação Atlas. Persistência, consultas, índices
automatizados e API de análises permanecem nas entregas correspondentes.
Ver [estado atual](qa/pc1/STATUS_ENTREGAS.md) e [contratos](contratos-dados.md).
