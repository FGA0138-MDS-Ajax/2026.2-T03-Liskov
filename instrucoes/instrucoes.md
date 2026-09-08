# Guia de Versionamento - Métodos de Desenvolvimento de Software (MDS)

Este documento estabelece as diretrizes e comandos essenciais de Git e GitHub que utilizaremos ao longo da disciplina. O objetivo é padronizar nosso fluxo de trabalho, garantindo rastreabilidade, organização e minimizando conflitos durante o desenvolvimento em equipe.

---

## 1. Configuração Inicial e Clonagem

Antes de iniciar qualquer trabalho, configure seu ambiente local e baixe o repositório do projeto.

### Configurando Identidade no Git
```bash
git config --global user.name "Seu Nome"
git config --global user.email "seu-email@exemplo.com"
```

### Clonando o Repositório
Baixe o repositório oficial da disciplina para a sua máquina local e acesse a pasta do projeto:
```bash
git clone https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov
cd 2026.2-T03-Liskov
```

---

## 2. Padronização de Commits (Conventional Commits)

Utilizaremos o padrão **Conventional Commits** para manter o histórico de alterações legível e semântico. Cada commit deve ter um propósito claro e focado em uma única responsabilidade.

### Estrutura do Commit

A mensagem do commit deve seguir a estrutura abaixo:

```
<tipo>: <descrição breve no imperativo>

[corpo opcional explicando o 'por que' e o 'como']
```

### Tipos Permitidos e Quando Utilizar

* **`feat:`** (Feature) Adição de uma nova funcionalidade ao sistema.
  * *Exemplo:* `feat: adiciona sistema de login com JWT`
* **`fix:`** (Bugfix) Correção de um erro ou comportamento inesperado.
  * *Exemplo:* `fix: resolve falha na validação de email vazio no cadastro`
* **`refactor:`** (Refatoração) Alteração no código que não corrige um bug nem adiciona uma nova funcionalidade, mas melhora a estrutura ou legibilidade.
  * *Exemplo:* `refactor: extrai lógica de autenticação para serviço dedicado`
* **`docs:`** (Documentação) Alterações exclusivas em arquivos de documentação (como o README.md).
  * *Exemplo:* `docs: atualiza instruções de instalação no README`
* **`style:`** (Estilo) Mudanças que não afetam o significado do código (espaçamento, formatação, remoção de ponto e vírgula, etc).
  * *Exemplo:* `style: aplica padronização do prettier nos arquivos de rotas`
* **`test:`** (Testes) Adição ou correção de testes automatizados.
  * *Exemplo:* `test: adiciona testes unitários para a classe de usuário`
* **`chore:`** (Tarefas de manutenção) Atualizações de ferramentas, dependências ou configurações de build que não afetam o código em produção.
  * *Exemplo:* `chore: atualiza versão do framework para 14.2`

### Boas Práticas para Commits

1. Mantenha os commits pequenos e focados.
2. Escreva a descrição sempre no tempo verbal **imperativo** (ex: "adiciona", "remove", "corrige").
3. Não utilize letras maiúsculas no início da descrição, a menos que seja um nome próprio, e não finalize com ponto.

---

## 3. Manipulação de Branches

O trabalho nunca deve ser feito diretamente na branch principal (`main`) ou na branch de integração contínua (`developer` ou `develop`). Cada nova tarefa deve ser desenvolvida em uma branch separada.

### Como Nomear sua Branch

O nome da branch deve ser curto, descritivo e contextualizado com o tipo de alteração.

**Formato recomendado:** `<tipo>/<descrição-curta>` ou `<tipo>/<numero-da-issue>-<descrição-curta>`

* *Exemplos:*
  * `feat/login-usuario`
  * `fix/issue-42-validacao-senha`
  * `docs/atualiza-arquitetura`

### Comandos Essenciais para Branches

**1. Listar branches existentes (locais e remotas):**
```bash
git branch -a
```

**2. Atualizar as referências do repositório remoto:**
Antes de criar uma branch, garanta que você tem o estado mais recente do repositório.
```bash
git fetch
```

**3. Criar uma nova branch e mudar para ela simultaneamente:**
Certifique-se de estar partindo da branch correta (geralmente a `developer`) antes de executar este comando.
```bash
git checkout -b <nome-da-sua-branch>
```

**4. Mudar de uma branch para outra:**
```bash
git checkout <nome-da-branch-existente>
```

**5. Excluir uma branch localmente (após o código ser mergeado):**
```bash
git branch -d <nome-da-branch>
```

---

## 4. Fluxo de Trabalho (Garantindo que o commit vá para a branch certa)

Para evitar enviar código incompleto para a branch principal ou fazer commits no lugar errado, siga este fluxo de trabalho para toda nova alteração:

### Passo 1: Partindo da branch de desenvolvimento

Sempre inicie o trabalho a partir da branch de integração da equipe, que chamaremos de `developer`.

```bash
# Muda para a branch de integração
git checkout developer

# Atualiza a sua branch local com as últimas alterações do repositório remoto
git pull origin developer
```

### Passo 2: Criando sua branch de trabalho

Crie a branch específica para a sua tarefa.

```bash
git checkout -b feat/minha-nova-funcionalidade
```

### Passo 3: Realizando e "Commitando" as alterações

Faça as modificações necessárias no código. Após finalizar uma unidade lógica de trabalho:

```bash
# Verifica quais arquivos foram modificados
git status

# Adiciona os arquivos desejados para a área de stage (preparação para o commit)
git add <nome-do-arquivo>
# ou 'git add .' para adicionar todas as alterações do diretório atual

# Realiza o commit utilizando a padronização
git commit -m "feat: implementa envio de notificacao por email"
```

### Passo 4: Enviando a branch para o repositório remoto (GitHub)

Sua branch e seus commits só existem localmente. Para enviá-los para o GitHub:

```bash
# O '-u' (upstream) vincula sua branch local à branch remota
git push -u origin feat/minha-nova-funcionalidade
```

### Passo 5: Criando o Pull Request (PR)

Após o `push`, acesse o repositório no GitHub. Você verá um botão sugerindo a criação de um **Pull Request**.

1. Ao criar o PR, **certifique-se** de que a branch base (destino) seja a `developer`, e não a `main`.
2. A interface mostrará algo como: `base: developer` <- `compare: feat/minha-nova-funcionalidade`.
3. Adicione revisores e preencha a descrição do PR adequadamente.

Apenas após a aprovação (Code Review) da equipe, o código será mesclado (merged) na branch `developer`.

---

**Resumo de Ouro:** Nunca faça commits diretos nas branches `main` ou `developer`. Sempre crie uma branch a partir da `developer` atualizada, faça seus commits semânticos, envie para o remoto e abra um Pull Request.
