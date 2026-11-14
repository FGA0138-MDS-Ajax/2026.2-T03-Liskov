# Revisão de formatos, referências e controle editorial

**Data:** 14/11/2026. **Base técnica:** `1723a7d62d55fa98fbf6eaf5cc9da80650dbe920`. **Revisão:** 0.3, reconciliação I-01–I-03, catálogo do PR #92 e Mini-tarefa GQM. Leitura factual/textual integral dos três PDFs acadêmicos concluída; certificação visual/normativa e publicação final pendentes. Sem atribuição de nota ao grupo.

## 1. Fontes e alcance da leitura direta

**Quadro 1 — Identidade dos originais efetivamente lidos**

| Fonte privada | Versão/data/total | SHA-256 |
| --- | --- | --- |
| Visão: `T03_Liskov -Documento de Visao do Produto e Projeto Escopo.pdf` | v1.0.0, 30/09/2026, 41 páginas | `9da7c31fa07a012bfa68e541dcbdc18453075256377737253a7a3b84506c7ccd` |
| Arquitetura: `T03_Liskov - Documento de Arquitetura-1.pdf` | v1.0.0, histórico “07/10”, sem ano impresso nessa célula, 29 páginas | `8596fbb6e102da2d71919e0ccb75fffa9f7e94802280b49e66f2284958becd19` |
| Mini-tarefa: `T03_Liskov - Tarefa GQM.pdf`, fornecido pelo usuário na raiz local | 14 páginas; contexto 2026/2; sem versão/data de revisão explícitas | `ecb629621eb253d4b85f78aa17f42db1012b4498369268681595782fc6cda0d4` |
| Formulário do professor | Template 2026/2, 17 páginas | Identificado no relatório QA #91; lido integralmente no primeiro envio |

Fonte: `pdftotext -layout`, leitura de todas as páginas dos dois textos, `pdfinfo` e `hashlib.sha256` nesta sessão. A Visão coincide com o hash publicado pelo [Sol Medium][Q2]. Arquivos de leitura privados em `/tmp/liskov_docs/inner/` e `/tmp/liskov_docs/arq_inner/`; extrações novas em `/tmp/sol-high-visao.txt` e `/tmp/sol-high-arquitetura.txt`. Os PDFs foram recuperados das cópias Liskov nos ZIPs locais de correções de Visão/Arquitetura, sem publicação dos arquivos ou identificação pessoal das páginas iniciais.

Foram vistas imagens renderizadas das páginas 4, 9 e 18 da Visão e 8, 19, 20, 21, 24, 25 e 26 da Arquitetura, cobrindo as figuras históricas e suas legendas. Isso complementa a leitura textual integral, mas **não** é medição de todas as margens/fontes no editor nem auditoria visual integral das cópias anotadas. A cópia anotada da Visão foi auditada pela outra frente; esta revisão se ancora no original acima, não presume ter lido todas as anotações.

A ressalva do primeiro envio do #90 sobre indisponibilidade de Visão/Arquitetura está superada. O GQM histórico incorporado à Visão, pp. 28–32, foi lido. A Mini-tarefa GQM separada foi posteriormente fornecida pelo usuário e lida em todas as 14 páginas; as pp. 3/9/13 também foram inspecionadas como imagem. Somente **`PACOTE_PRE_INSPECAO_LISKOV.zip`** permanece sem recuperação nesta sessão, sem afirmar inexistência. Os documentos `docs/inspecao/*` são acessíveis no [PR #92][A1], commit `25f2587`, e não são arquivos faltantes.

## 2. Checklist de apresentação e paginação

O formulário §3.1 e Quadro 5 orientam as verificações. Seus itens/quadros repetidos devem ser alinhados com professor/inspetor; não foi calculada nota. Não foram inventadas medidas ABNT ou edições normativas. O template da disciplina e as normas adotadas ainda devem orientar a edição final.

**Quadro 2 — Resultado por critério de formato**

| Critério | Visão original | Arquitetura original | Tratamento na revisão / pendência |
| --- | --- | --- | --- |
| Margens/rodapés, fontes e espaçamento | Paginação 1–41; aspectos físicos não medidos | Paginação 1–29; aspectos físicos não medidos | Medir no editor e no PDF final; Markdown não certifica medidas físicas |
| Numeração e autoria de figuras | Figuras 1 (p. 4), 2.1 (p. 9), 3 (p. 18); padrão misto; fontes explícitas nas pp. 4/18, sem linha de fonte na p. 9 renderizada | Figura 1 (p. 8) e Figura 01 (legenda p. 19, imagem p. 20) repetem número; 02 (legenda p. 20, imagem p. 21), 03 (p. 24), figuras 4/5 mencionadas p. 25 com imagens pp. 25/26 sem legendas próprias visíveis | Renumerar sequencialmente e adicionar fonte individual; imagens históricas não foram publicadas |
| Chamadas e explicação de figuras | Ishikawa explicado pp. 3/5; ciclo e processo explicados pp. 8–10/17–20 | Componentes, casos, atividades e pacotes explicados pp. 8–25; imagens de fluxo/classes com chamada na p. 25 | Manter explicações, aproximar chamada/legenda/imagem e atualizar pipeline clássico |
| Tabelas/quadros | Tabelas 2.2.1/2.3.1/2.4.1/2.5.1 identificadas; tabelas de épicos/perfis/cenários/backlog pp. 20–27 usam “Tabela :” sem número; placeholders “xxx/xxxx” pp. 23/25 | Tabela 1 de dados pp. 9–10 e Tabela 01 de UC p. 18 duplicam numeração; Quadro 2 p. 22 e Tabela 2 pp. 12–13 precisam de sequência por tipo e fonte individual | Manter numeração própria dos rascunhos; regenerar listas e chamadas na edição final |
| Identificação/versionamento | Integrantes e histórico na p. 1, autoria “Todos”, 30/09/2026 | Integrantes/histórico na p. 2; “Todos(as)”, 07/10; rodapé da p. 2 diz “Visão de Produto e Projeto” | Corrigir rótulo do documento e completar ano com confirmação; sem republicar matrículas/pontos |
| Sumário/páginas | 41 páginas; seção 6.2 inicia p. 34 e tabela T01 p. 35; bibliografia pp. 40–41 | Sumário p. 3 indica bibliografia p. 30, mas seção 3 está na p. 29; §2.6 inicia p. 26 e §2.7 p. 27 | Regenerar sumário; citar página impressa/física do hash conferido |
| Apêndices/referências cruzadas | Bibliografia inventariada abaixo | Apêndice A prometido p. 16, ausente até o fim p. 29 | Suprir conteúdo em nova edição ou substituir remissão por política real, preservando defeito histórico |
| Citações/bibliografia | Cohn ausente; entradas sem chamada localizada e acessos em branco, conforme Quadro 3 | Três entradas com chamadas correspondentes, conforme Quadro 4 | Normalização final e conferência editorial pendentes; auditoria factual já realizada |

Fonte: leitura direta e amostra visual identificada no §1. Esses são defeitos/localizações verificáveis, sem inferir reprovação ou conformidade total dos PDFs.

A página de **“exportar resumos” é 27**, §2.7, e a **bibliografia da Arquitetura é somente p. 29**. Essas localizações corrigem as sínteses “p. 26” e “pp. 28–29” do Argon. A p. 26 contém o diagrama de classes e início da implantação; não contém a permissão P1 de exportação.

## 3. Correspondência bibliográfica dos originais

**Quadro 3 — Inventário da Visão (bibliografia pp. 40–41)**

| Entrada histórica | Local da entrada | Chamada localizada no original | Resultado / ação proposta |
| --- | --- | --- | --- |
| Schwaber; Sutherland, Guia do Scrum, 2020 | p. 40, item 1 | Figura 2.1 p. 9 menciona “Guia do Scrum (2020)”, sem autores; corpo fala Scrum sem chamada autor-data | Acrescentar chamada inequívoca no texto; não dizer que nenhuma menção ao guia existe |
| Beck, Extreme Programming Explained, 2000 | p. 40, item 2 | **Figura 2.1 p. 9 contém “Beck, 2000”**, visível na imagem e ausente do texto extraído | Não é obra totalmente sem citação; acrescentar/normalizar chamada no texto e preservar a fonte da figura |
| Sommerville, Engenharia de Software, 2019 | p. 40, item 3 | Nenhuma chamada autor-data localizada na leitura integral de texto e figuras de processo | Referenciar onde efetivamente fundamenta o texto ou retirar da bibliografia da nova versão, sem apagar o histórico |
| Krekel et al., pytest, 2004 | p. 40, item 4 | Nome da ferramenta em pp. 33–34, sem chamada Krekel/2004 localizada | Vincular documentação efetivamente utilizada e conferir metadados; não inferir autor/ano só do nome pytest |
| Bird; Klein; Loper, 2009 | p. 40 | p. 5, preparação textual | Correspondência presente; reposicionar para discussão do baseline quando o fluxo principal mudar |
| Brand24 | p. 40 | Menção institucional p. 7, sem ano de chamada | `Acesso em: __ 2026`; preencher somente acesso real, não data histórica inventada |
| Brandwatch | p. 40 | Menção institucional p. 7, sem ano de chamada | Mesmo defeito de acesso; normalizar chamada |
| Brasil, LGPD, 2018 | p. 40 | p. 5 | Correspondência presente; revisão jurídica de implantação não foi executada nesta frente |
| Ishikawa, 1976 | p. 40 | p. 3 e figura/explicação pp. 4–5 | Correspondência presente |
| Liu, 2012 | p. 40 | p. 3 | Correspondência presente |
| Manning; Raghavan; Schütze, 2008 | p. 40 | p. 5 | Correspondência presente; aplicação ao baseline deve ser delimitada |
| Moore, 1991 | p. 41 | p. 6 | Correspondência presente para quadro de posição |
| Pang; Lee, 2008 | p. 41 | p. 3 | Correspondência presente |
| Pedregosa et al., 2011 | p. 41 | p. 5 | Correspondência presente para scikit-learn/baseline |
| Salton; Buckley, 1988 | p. 41 | p. 5 | Correspondência presente para TF-IDF do baseline |
| Sprinklr | p. 41 | Menção institucional p. 7, sem ano de chamada | `Acesso em: __ 2026`; normalizar chamada e acesso real |
| **Cohn, 2005** (citação sem entrada) | Ausente nas pp. 40–41 | p. 28, Planning Poker | A Mini-tarefa agora identifica Cohn, Agile Estimating and Planning (2005), p. 13. Propor essa referência para a Visão, confirmando com a autoria que é a obra citada; não apagar a omissão histórica |

Fonte: Visão original com hash do §1, incluindo inspeção visual da Figura 2.1. A afirmação do Argon sobre “quatro obras não citadas” é refinada: Beck aparece na figura; o Guia tem menção por título; Sommerville e a entrada Krekel não têm chamada autor-data localizada. A extração textual sozinha não detecta todas as citações em figuras. A mistura de quatro referências numeradas com as demais sem numeração também deve ser uniformizada na edição final.

**Quadro 4 — Inventário da Arquitetura (bibliografia p. 29)**

| Entrada histórica | Chamada no corpo | Resultado |
| --- | --- | --- |
| Bass; Clements; Kazman. Software Architecture in Practice. 4. ed., 2021 | p. 6, §2.2 | Correspondência presente; manter na fundamentação do estilo |
| Liskov. Visão do Produto e do Projeto, v1.0.0, 2026 | p. 6, §2.2; demais remissões à Visão | Correspondência presente; nova versão deve identificar documento e versão corretos |
| Brum; Nunes. Building a sentiment corpus of tweets in Brazilian Portuguese. LREC, 2018 | p. 10, fonte da Tabela 1 | Correspondência presente; título/URL e acesso “7 out. 2026” constam do original; não comprova disponibilidade/licença do corpus local |

Fonte: leitura direta do original. Não foram constatadas nesse inventário as mesmas lacunas de Cohn/datas em branco da Visão; não transferir defeitos entre documentos.

### 3.1 Mini-tarefa GQM separada

Arquivo do Quadro 1, 14 páginas; lidos integralmente introdução, objetivos negociais e de projeto, esquemas GQM, modelos de coleta/análise e bibliografia. As imagens das pp. 3/9/13 confirmam os títulos e as tabelas decisórias. O original contém matrículas na p. 2 e permanece **somente local**, conforme instrução expressa do usuário. Os resumos abaixo não reproduzem identificadores pessoais nem o PDF.

**Quadro 5 — Auditoria do documento GQM adicional**

| Aspecto / localização | Resultado verificável | Proposta / limite |
| --- | --- | --- |
| Identificação e histórico, pp. 1–2 | Título, equipe e funções; versão/data de revisão não explícitas | Registrar versão/histórico na edição futura; contexto 2026/2 não é data comprovada de publicação |
| Sumário e títulos, pp. 3–6 | §3.3 duplicado no sumário; §2.1 aparece nas pp. 4 e 6; início de §2.3 na p. 7, embora sumário indique p. 8; métrica de projeto inicia p. 9, sumário indica p. 10 | Eliminar duplicações e regenerar sumário após normalizar estilos |
| Quadros negociais, pp. 5–9 | Tabelas de comparação/GQM/coleta/decisão sem numeração e fonte individual; quadros de projeto 3.1–3.5 têm identificação e fontes nas pp. 10–13 | Uniformizar numeração, fonte e chamadas sem atribuir conformidade às margens não medidas |
| Vocabulário e edição, pp. 4/6/9 | “duasmétricas”; “precisão (acurácia)” usa termos distintos como equivalentes; fragmento “x’Suspeito” antes de ação de auditoria | Corrigir edição e separar acurácia global de precisão por classe no relatório |
| Bibliografia, pp. 13–14 | Basili/Caldiera/Rombach (1994) citados p. 4; Cohn (2005) citado p. 11; Visão Liskov v1.0.0 (2026) referida nas pp. 4–6/9/13 | As três entradas têm correspondência no texto; não herdam a falta de Cohn da bibliografia da Visão |
| Critérios e fórmulas, pp. 8–13 | Limiar F1 por classe 60% presente; ≥80% e >90% se sobrepõem; “70% a 79%” não explicita frações até 80%; variação relativa depende de média anterior | Ratificar precedência, fronteiras e denominadores em PO-02/PO-12; não classificar ausência de dados como zero |

Fonte: leitura direta e imagens do PDF com SHA-256 do Quadro 1. Esses achados não representam execução do plano ou aprovação da PO.

Referências transcritas da bibliografia da Mini-tarefa (metadados do documento, sem verificação editorial externa das obras):

- BASILI, Victor R.; CALDIERA, Gianluigi; ROMBACH, H. Dieter. The Goal Question Metric Approach. In: MARCINIAK, John J. (ed.). *Encyclopedia of Software Engineering*. New York: John Wiley & Sons, 1994. v. 1, p. 528–532. Chamada: p. 4.
- COHN, Mike. *Agile Estimating and Planning*. Upper Saddle River: Prentice Hall, 2005. Chamada: p. 11; entrada: p. 13. Referência recuperada para propor a correção da Visão p. 28/pp. 40–41, após confirmar correspondência com a obra usada.
- LISKOV. *SentIA – Análise de Sentimentos: Visão do Produto e do Projeto*. Versão 1.0.0. Brasília, DF: Universidade de Brasília, 2026. Entrada: p. 14; remissões ao documento e sua DoD no corpo.

## 4. Referências novas da revisão

**Quadro 6 — Correspondência das fontes novas**

| ID | Fonte e metadados verificados | Uso efetivo nesta revisão | Correspondência e pendência |
| --- | --- | --- | --- |
| R1 | PYSENTIMIENTO. *bertweet-pt-sentiment*. Hugging Face, [s.d.]. Disponível em: <https://huggingface.co/pysentimiento/bertweet-pt-sentiment>. Acesso em: 14 nov. 2026 | Arquitetura §2 e matriz D18: identidade do checkpoint e base portuguesa | Referência e chamada presentes; fixar revisão da ficha/pesos na reprodução futura |
| R2 | PÉREZ, Juan Manuel et al. *pysentimiento: A Python Toolkit for Opinion Mining and Social NLP tasks*. arXiv:2106.09462v3, 2024. DOI: 10.48550/arXiv.2106.09462. Disponível em: <https://arxiv.org/abs/2106.09462v3>. Acesso em: 14 nov. 2026 | Arquitetura §2: identificação da biblioteca e contexto | Título/ano referem versão v3, revista em 13 jul. 2024; não copiar automaticamente título/autores da versão v1 da ficha |
| R3 | NGUYEN, Dat Quoc; VU, Thanh; NGUYEN, Anh Tuan. *BERTweet: A pre-trained language model for English Tweets*. arXiv:2005.10200v2, 2020. DOI: 10.48550/arXiv.2005.10200. Disponível em: <https://arxiv.org/abs/2005.10200v2>. Acesso em: 14 nov. 2026 | Matriz D18: distinguir modelo inglês do checkpoint português | Fonte de contraste terminológico, não prova de treinamento do modelo português; não usada como fundamentação na bibliografia da Arquitetura |
| Local F1 | *Template de Inspeção — MDS — Semestre 2026/2*. Autoria nominal/data editorial N/D no texto extraído | Esta revisão, §§1–2, e cobertura dos Quadros 7/8 | Identificação editorial deve ser conferida no documento institucional; não deduzir autoria de metadado `python-docx` |
| H1–H5, C1–C20, T1–T4 e I/P | Equipe Liskov. Código, documentação, testes, PRs e issues do SentIA | Afirmações de comportamento e estado técnico | Links de código fixados no SHA; PRs/issues são mutáveis e têm data de consulta explícita |

Fonte: páginas primárias consultadas no primeiro envio e repositório fixado por SHA. Estes metadados novos não substituem o inventário dos originais. A identificação de Cohn foi recuperada da bibliografia da Mini-tarefa, sem deduzir título apenas de autor/ano.

## 5. Correções, publicação e limites remanescentes

Efetuado nos seis Markdown: reconciliação com todas as seções textuais originais; controle de versões/autoria sem matrículas; backlog US01–US18 e acréscimos posteriores; fontes e páginas verificadas; CI real com MongoDB; catálogo canônico/aliases da PO; registro de defeitos bibliográficos/figuras/apêndice/sumário. Os originais não foram alterados.

Antes da publicação acadêmica: decisões PO-01a/b sobre modelo/testes, PO-02/PO-12 sobre métricas e PO-14b sobre nova edição; revisão humana; confirmar a aplicação da referência de Cohn recuperada e ajustar chamadas bibliográficas; preencher acessos reais; normalizar legendas, numeração, sumário e estilos; renderizar Mermaid e exportar PDF sem matrículas/anotações. Medir margens/rodapés e revisar todas as páginas no editor/PDF final. A Mini-tarefa separada já foi lida; apenas o pacote de pré-inspeção continua sem recuperação nesta sessão. O confronto com o plano operacional #91 revelou critérios históricos a incorporar, registrados na Visão e em PO-02/PO-12.

O PR #90 pode ser apresentado à revisão técnica como proposta factual reconciliada. Isso não é aceite do produto nem conformidade ABNT final. Cabe à PO/equipe aprovar a nova versão; merge e publicação dependem de autorização humana específica.

[A1]: https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/blob/25f258786981f29552d2df2f1b4597ab7ef01c44/docs/inspecao/PLANO_REGULARIZACAO.md
[Q2]: https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/blob/84530e4b3d0ac1762b9100c4c728e6208ffca810/docs/qa/inspecao/RELATORIO_EXECUCAO.md
