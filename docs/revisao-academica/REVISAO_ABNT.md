# Revisão de formatos, referências e controle editorial

**Data:** 14/11/2026. **Base técnica:** `1723a7d62d55fa98fbf6eaf5cc9da80650dbe920`. **Estado:** checklist parcial, sem certificação de conformidade e sem atribuição de nota ao grupo.

## 1. Materiais e método

Foi extraído e lido integralmente o texto do arquivo local `Formulario Inspeçao_professor.pdf` (17 páginas, A4 segundo `pdfinfo`). A extração não é conferência visual de margens ou diagramas. O formulário não foi copiado ao repositório. Os PDFs de Visão, Arquitetura e Mini-tarefa GQM, bem como o ZIP de pré-inspeção, não foram localizados; seus autores, datas, paginação, bibliografia e disposição gráfica são **N/D** nesta revisão.

Esta revisão cobre o §3.1 “Formatos” e o Quadro 5 de formato, além dos itens de identificação/versionamento dos Quadros 7 e 8. O formulário contém duas apresentações de critérios: §3.1 distribui pesos de 10%, 10%, 10%, 30%, 20%, 20%; o Quadro 5 posterior apresenta máximos de 1, 1, 1, 3, 2, 2. O Quadro 7 contém item “i” repetido e valores cuja interpretação exige alinhamento com professor/inspetor. Isso é ambiguidade do instrumento recebido, não defeito atribuído ao SentIA. Nenhuma nota foi calculada.

Não foram inventados valores de margem, tamanhos de fonte ou edição normativa. Antes da exportação final, confirmar o template da disciplina e as edições aplicáveis das normas de apresentação, citações e referências com biblioteca/professor. Links técnicos rastreáveis em Markdown ajudam a auditoria, mas não substituem a normalização acadêmica do documento final.

## 2. Checklist de apresentação e identificação

O Quadro 1 diferencia correções efetivamente feitas nas minutas de verificações que dependem de fonte ou editor. “Pendente” não significa defeito confirmado do PDF.

**Quadro 1 — Conferência por artefato**

| Item do formulário / aspecto | Visão original | Arquitetura original | GQM original | Tratamento nas minutas / próximo passo |
| --- | --- | --- | --- | --- |
| Formatos i: margens, cabeçalhos, rodapés e área útil | Não verificado | Não verificado | Não verificado | Markdown não fixa medidas físicas; medir no editor e PDF final conforme template aprovado |
| Fonte, espaçamento e alinhamento | Não verificado | Não verificado | Não verificado | Conferir estilos, títulos, listas, quebras e células após exportação |
| Formatos ii: numeração de figuras/quadros/tabelas | N/D sem original | N/D sem original | N/D sem original | Quadros numerados por documento; figuras 1–4 na minuta de Arquitetura; conferir índice e sequência final |
| Formatos ii: autoria/fonte dos elementos | N/D | N/D | N/D | Fontes incluídas abaixo dos quadros/figuras; confirmar autoria e permissão das imagens históricas |
| Formatos iii: chamada e explicação dos elementos | N/D | N/D | N/D | Texto explica finalidade de cada quadro e figura; revisar texto corrido após diagramação |
| Formatos iv: citações no corpo | N/D | N/D | N/D | Código/PR/issue referenciados; referências acadêmicas R1/R2 citadas na Arquitetura; revisar padrão autor-data final |
| Formatos v: bibliografia completa | N/D | N/D | N/D | Fontes novas identificadas; não reconstruir bibliografia antiga por suposição |
| Formatos vi: correspondência em dois sentidos | Não auditável | Não auditável | Não auditável | Inventário novo no Quadro 2; executar inventário completo quando receber PDFs |
| Quadros 7/8: título, identificação e histórico de revisão | N/D | N/D | N/D | Projeto, turma, data, base SHA e condição de minuta explícitos; versão publicada futura depende de decisão |
| Quadros 7/8: tabela de integrantes/autoria | N/D | N/D | N/D | Funções recuperadas das issues na Visão; nomes e quadro original precisam de reconciliação |
| Paginação, sumário e referências cruzadas | Não verificado | Não verificado | Não verificado | Revisar sumário automático, páginas, títulos órfãos e links após exportar |
| Histórico v1.0.0 | Não disponível | Não disponível | Não disponível | Não sobrescrito; data/autoria histórica permanecem N/D |

Fonte: formulário local, §3.1, Quadros 5/7/8; minutas desta revisão. Os estados “N/D” impedem concluir conformidade ou não conformidade dos originais.

## 3. Auditoria bibliográfica e precisão de atribuição

O Quadro 2 registra fontes acadêmicas novas consultadas em 14/11/2026. As referências ao GitHub são fontes primárias da implementação, fixadas por SHA nas demais minutas. Não se confunde uma versão do software com ano de publicação de um artigo.

**Quadro 2 — Correspondência das fontes novas**

| ID | Fonte e metadados verificados | Uso efetivo nesta revisão | Correspondência e pendência |
| --- | --- | --- | --- |
| R1 | PYSENTIMIENTO. *bertweet-pt-sentiment*. Hugging Face, [s.d.]. Disponível em: <https://huggingface.co/pysentimiento/bertweet-pt-sentiment>. Acesso em: 14 nov. 2026 | Arquitetura §2 e matriz D18: identidade do checkpoint e base portuguesa | Referência e chamada presentes; fixar revisão da ficha/pesos na reprodução futura |
| R2 | PÉREZ, Juan Manuel et al. *pysentimiento: A Python Toolkit for Opinion Mining and Social NLP tasks*. arXiv:2106.09462v3, 2024. DOI: 10.48550/arXiv.2106.09462. Disponível em: <https://arxiv.org/abs/2106.09462v3>. Acesso em: 14 nov. 2026 | Arquitetura §2: identificação da biblioteca e contexto | Título/ano referem versão v3, revista em 13 jul. 2024; não copiar automaticamente título/autores da versão v1 da ficha |
| R3 | NGUYEN, Dat Quoc; VU, Thanh; NGUYEN, Anh Tuan. *BERTweet: A pre-trained language model for English Tweets*. arXiv:2005.10200v2, 2020. DOI: 10.48550/arXiv.2005.10200. Disponível em: <https://arxiv.org/abs/2005.10200v2>. Acesso em: 14 nov. 2026 | Matriz D18: distinguir modelo inglês do checkpoint português | Fonte de contraste terminológico, não prova de treinamento do modelo português; não usada como fundamentação na bibliografia da Arquitetura |
| Local F1 | *Template de Inspeção — MDS — Semestre 2026/2*. Autoria nominal/data editorial N/D no texto extraído | Esta revisão, §§1–2, e cobertura dos Quadros 7/8 | Identificação editorial deve ser conferida no documento institucional; não deduzir autoria de metadado `python-docx` |
| H1–H5, C1–C20, T1–T4 e I/P | Equipe Liskov. Código, documentação, testes, PRs e issues do SentIA | Afirmações de comportamento e estado técnico | Links de código fixados no SHA; PRs/issues são mutáveis e têm data de consulta explícita |

Fonte: páginas primárias R1–R3, formulário local e repositório. O quadro documenta a conferência nova; não equivale a auditoria da bibliografia histórica.

Procedimento para os PDFs pendentes: listar cada citação com página/seção e chave autor/ano; listar todas as entradas bibliográficas; cruzar os dois conjuntos; registrar citações sem referência, referências sem uso, divergências de grafia/ano/título/edição/URL e duplicações. Conferir citações diretas na fonte, incluindo página e atribuição; não transformar resumo em citação literal. Verificar também fontes de cada tabela/figura e se o texto explica o conteúdo. Uma ausência só vira defeito confirmado depois da leitura do artefato correspondente.

## 4. Correções efetuadas e reconciliação pendente

Efetuado **somente nas minutas novas**: identificação de corte e estado; numeração de quadros/figuras; fontes e explicações; distinção entre fato, proposta, relato de autor e aceite; links para fontes de implementação; precisão do nome do checkpoint português; bibliografia nova com consulta datada; preservação explícita dos históricos.

Não efetuado: modificação de PDF/arquivo de instrução; normalização visual no editor; substituição da bibliografia histórica; aprovação da PO; preenchimento de notas pelo inspetor. São necessários os PDFs originais, o pacote e o template normativo para concluir a revisão integral. Registrar em cada correção futura página anterior, localização nova, justificativa, autor, revisor, data e versão.

## 5. Condições para publicação acadêmica

1. Receber as fontes originais e resolver ambiguidades de critérios com professor/inspetor.
2. Reconciliar integralmente o conteúdo das minutas com seções, integrantes, requisitos, figuras e tabelas originais, sem apagar decisões históricas.
3. Registrar revisão técnica e decisões da PO, mantendo itens rejeitados/adiados no histórico.
4. Aplicar os estilos do template adotado no editor; renderizar Mermaid; revisar tamanho, contraste, legibilidade, quebras e correspondência com o texto.
5. Exportar PDF; medir margens/rodapés e verificar sumário, numeração, fontes, citações e links; registrar evidência visual e versão do arquivo.
6. Publicar nova versão por fluxo de revisão autorizado, preservando os originais e sem inferir homologação a partir do PR.

Responsável pela consolidação documental: Héllen e equipe, conforme [issue #86](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/issues/86). Resultados da conferência final: N/D até execução.
