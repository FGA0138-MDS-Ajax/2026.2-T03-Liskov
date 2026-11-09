# Fontes acadêmicas, requisitos e decisões

Corte: **09/11/2026**. A revisão usa documentos efetivamente encontrados; não
reconstrói os arquivos oficiais a partir do código.

## Disponíveis

| Fonte | Referência consultada | Uso e limite |
|---|---|---|
| Índice acadêmico | [docs/index.md](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/blob/0433a5545628c3de58c247c43012a3cdbd52d93c/docs/index.md) | Apresentação, objetivo e camadas; apenas enumera Visão, Arquitetura e GQM |
| Ata 01 | [25/09/2026](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/blob/0433a5545628c3de58c247c43012a3cdbd52d93c/docs/atas-reuniao/ata-reuniao-1.md) | Problema, proposta inicial, divisão do Documento de Visão; responsabilidades eram propostas |
| Ata 02 | [04/11/2026](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/blob/0433a5545628c3de58c247c43012a3cdbd52d93c/docs/atas-reuniao/ata-reuniao-2.md) | Propósito de redes sociais/temas, manutenção de datasets e banco, mocks para o frontend e planejamento de consulta externa |
| Guia de versionamento | [instrucoes/instrucoes.md](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/blob/0433a5545628c3de58c247c43012a3cdbd52d93c/instrucoes/instrucoes.md) | Branch própria, commits semânticos, PR/revisão; esta tarefa deriva da integração PC1 por instrução expressa |
| Backlog e critérios | [Issues](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/issues), consulta em 09/11 | RF/US/T citados na matriz foram transcritos das issues, não certificados contra PDFs |
| PR #70 | [61926fe](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/pull/70) | Novo frontend; descreve mocks e ausência de rotas, substitui #66 |
| Documentação técnica | [Índice local](README.md) | Código, esquema, contratos propostos e evidências por SHA |

As atas são preservadas na branch `docs`, SHA
`0433a5545628c3de58c247c43012a3cdbd52d93c`, sem cópias divergentes nesta branch.
Os links fixam a revisão lida. A ata 02 registra entendimento dos participantes
sobre o ponto de controle, **não uma rubrica oficial da disciplina**.

## Não localizados

Documento completo de Visão do Produto e Escopo, Documento de Arquitetura,
Tarefa GQM, backlog acadêmico consolidado e critérios oficiais do PC1 não foram
localizados nas árvores consultadas (`docs`, `main`, `developer`, referência PC1),
nos materiais locais de projeto em Documents/Downloads ou em sessões de documentos
conectadas (nenhuma disponível). Não foi encontrado PDF identificável do T03 Liskov.
PDFs pessoais sem relação com o projeto não foram usados.

As remissões a seções do Documento de Arquitetura em textos herdados são
**referências declaradas pelos autores**, sem conferência do documento completo.
As metas GQM mencionadas nas issues #17 e #63 não constituem, por si, metas
aprovadas para o PC1. Não se cria pontuação, percentual mínimo ou prazo acadêmico.

## Contradições e validações pendentes

| Tema | Fonte / implementação | Tratamento e decisão necessária |
|---|---|---|
| Pipeline clássico versus BERTweet | #5–#8 registram replanejamento; código preserva texto sem stopwords/stemming/TF-IDF externos | PO deve homologar RF03–RF06 e roteiros T04–T07; técnica antiga não foi marcada como entregue |
| Propósito do produto versus demonstração | Ata 02 pede análise de redes sociais por tema; painel atual mostra amostra fixa sem busca temática | Apresentar como incremento parcial; definir backlog de busca, sem alterar escopo oficial |
| Independência dos dados | #17 exige proveniência/partições; TweetSentBR local não tem split/IDs originais; BPSAD é outro domínio | Avaliação independente e eventual alteração de metas requerem revisão ML/PO |
| Administração | #58 exige autenticação no servidor; #70 só entrega fluxo simulado | #59–#61 têm interface em mock; não encerrar #58 nem T01–T03 integrados |
| Data dos filtros | #24 exige escolha aprovada; mock usa publicação provisoriamente | Confirmar data/fuso/limites; registros sem publicação não recebem data artificial |
| Landing page e login | Wireframes/contrato herdados citavam decisão PO em 07/11; #57/#58 e #62 registram administração/web | Registrar atribuição às issues, sem transformar comentário herdado em ata formal; aceite visual/escopo pendente |
| Estado do frontend | README/roteiro antigos citavam #66 e placeholder | #66 fechado sem merge; #70 é a proposta atual, presente apenas na integração selecionada |
| Persistência e privacidade | Esquema prevê armazenamento sem autor; pipeline produz documentos e copia metadados | CRUD e curadoria não implementados; política documental não equivale a proteção técnica |

O aceite de requisitos, mudança de escopo, privacidade/licença e adequação acadêmica
permanece com PO/equipe. Esta revisão não altera issues nem declara aprovações.
