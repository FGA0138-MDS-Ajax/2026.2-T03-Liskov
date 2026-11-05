#!/usr/bin/env python3
"""Replaneja issues do SentIA; simulação por padrão; --apply para gravar.
Requer GitHub CLI autenticado (gh auth login). Não altera branches, PRs ou commits.
"""
import argparse
import datetime as dt
import json
import pathlib
import subprocess
import sys

REPO = 'FGA0138-MDS-Ajax/2026.2-T03-Liskov'
BASE = f'repos/{REPO}'
ML = ['Ricardo-909-Leal', 'Gabriel-Ma7os']
B = ['Brenowr']
QA = ['Figueirin']
DB = ['MariaEduarda-jg']
DOD = '''## Definition of Done
- [ ] Critérios de aceitação atendidos e demonstrados com evidências.
- [ ] Código ou documentação em branch, com Pull Request revisado para a branch de integração adotada.
- [ ] Testes aplicáveis realizados e CI verificada; pendências explicitadas.
- [ ] Validação pela Product Owner e documentação arquitetural atualizada quando necessário.
'''
NOTICE = '''## Histórico e decisão de replanejamento (29/10/2026)
A issue existia no planejamento original com pipeline clássico (limpeza/stopwords/stemming/TF-IDF) e/ou corpus TweetSentBR. O escopo foi reavaliado para permitir o uso de BERTweet-PT-Sentiment, que utiliza tokenização e representação próprias. Esta alteração **não comprova execução ou conclusão** dos requisitos anteriores. RFs, testes T04–T07, GQM e documentos de Visão e Arquitetura precisam de atualização/aceite formal. O texto original será salvo no backup local pelo script antes da alteração.
'''

def body(obj, ref, sprint, leads, tasks, checks, dependencies='', note=''):
    return (f'## Objetivo\n{obj}\n\n**Referências:** {ref}  \n**Planejamento:** {sprint} — replanejada em 29/10/2026  \n**Responsáveis:** {leads}  \n**Estimativa:** Story Points a definir pela equipe\n'
            + (f'**Dependências:** {dependencies}\n' if dependencies else '')
            + '\n## Atividades\n' + '\n'.join('- '+x for x in tasks)
            + '\n\n## Critérios de aceitação\n' + '\n'.join('- [ ] '+x for x in checks)
            + '\n\n' + (note+'\n\n' if note else '') + NOTICE + '\n' + DOD)

updates = {
 3: {'title':'[Dados] Definir, inspecionar e documentar dataset independente para avaliação', 'assignees':B, 'labels':['prioridade:must','area:dados','tipo:preparacao'], 'body':body(
 'Curar e disponibilizar dados auditáveis em português para importação, inferência e avaliação, diante da indisponibilidade de grande parte dos textos do TweetSentBR. Breno responde pela engenharia de dados; Ricardo e Gabriel pela metodologia de ML.',
 'RF01/RF02, apoio a RNF01/US08','Sprint 1 (pendente, prioridade de desbloqueio)','Breno; apoio técnico de Ricardo e Gabriel',
 ['Inventariar fontes e informar URL, disponibilidade, domínio, licença/termos e método de obtenção; registrar a limitação do TweetSentBR.', 'Fornecer amostras e rotina reprodutível de carregamento/normalização, com campos id_origem, texto, fonte, rótulo original quando houver e data_publicacao quando existir.', 'Quantificar registros, classes, duplicações, campos nulos e disponibilidade de datas, sem inventar data de publicação.', 'Fornecer IDs/digests e proveniência para permitir à frente ML verificar separação de treino/validação/teste; verificar licenças antes de publicar textos.', 'Combinar com Ricardo e Gabriel o dataset independente de avaliação e riscos de vazamento do pré-treino.'],
 ['Origem e estrutura dos dados documentadas; dataset ou procedimento de obtenção reproduzível.', 'Contagens, classes, duplicatas, campos ausentes e datas auditáveis.', 'Contrato de registros alinhado com importador (#2) e ML, sem presumir 15 mil tweets acessíveis.', 'PR com artefatos permitidos e aceite das frentes de dados/ML.'], '#1, #2 e issue de avaliação de modelo')},
 5: {'title':'[RF03][US03] Preparar entradas textuais compatíveis com BERTweet', 'assignees':ML, 'labels':['prioridade:must','area:ml','tipo:funcionalidade'], 'body':body(
 'Definir preparação mínima e segura da entrada textual para o classificador BERTweet, preservando informações úteis ao sentimento e o texto original. Evitar aplicar o pipeline clássico antes do tokenizador próprio.', 'RF03/US03','Sprint 2 (replanejada para integração do BERTweet)','Ricardo e Gabriel',
 ['Documentar exatamente quais normalizações já são realizadas pelo pysentimiento/tokenizador.', 'Aceitar textos brasileiros com URLs, @menções, pontuação, emojis, negações e acentuação; preservar o original.', 'Definir e implementar validação de entradas vazias, não-string e lote; integrar com #9.', 'Caso mantenham baseline clássico, isolar suas transformações das utilizadas pelo BERTweet.'],
 ['Entrada válida não perde informações semânticas essenciais e gera resultado reproduzível.', 'Regras de tratamento e limites documentados; testes de casos de borda.', 'Entrada compatível com a interface do classificador sem TF-IDF/stemming/remoção de stopwords externos.'], '#6, #7, #8 e #9')},
 6: {'title':'[RF04][US04] Reavaliar stopwords na estratégia BERTweet', 'assignees':ML, 'labels':['prioridade:suporte','area:ml','tipo:preparacao'], 'body':body(
 'Documentar a decisão técnica de NÃO remover stopwords como etapa externa ao BERTweet, preservando negações e contexto. O requisito original de remoção deverá ser negociado/revisado no Documento de Visão, sem ser marcado como implementado.', 'RF04/US04 (revisão de escopo)','Sprint 2 (replanejada)','Ricardo e Gabriel',
 ['Identificar no pipeline BERTweet como o tokenizador recebe palavras comuns e negações.', 'Registrar impacto esperado da remoção sobre negações e significado; exemplificar com frases positivas/negativas.', 'Isolar eventual remoção de stopwords somente para baseline clássico, se mantido.', 'Solicitar atualização formal do requisito RF04, critérios de aceitação e roteiro T05.'],
 ['Há decisão arquitetural documentada sobre não aplicar stopwords externas ao BERTweet.', 'Exemplos com negação preservada e testes de contrato.', 'Nenhum critério da antiga remoção é artificialmente marcado como concluído.'], '#5, #9, #10')},
 7: {'title':'[RF05][US05] Reavaliar stemming na estratégia BERTweet', 'assignees':ML, 'labels':['prioridade:suporte','area:ml','tipo:preparacao'], 'body':body(
 'Documentar a dispensa de stemming externo antes do BERTweet. O tokenizador do modelo não deve receber radicais produzidos por uma etapa clássica sem justificativa empírica.', 'RF05/US05 (revisão de escopo)','Sprint 2 (replanejada)','Ricardo e Gabriel',
 ['Confirmar que a entrada do modelo usa texto apropriado à tokenização original.', 'Documentar por que stemming pode alterar tokens e degradar semântica.', 'Manter stemming restrito a baseline clássico opcional, se aplicável.', 'Atualizar proposta para RF05 e roteiro T06 com aprovação da PO.'],
 ['Decisão e efeito sobre interfaces documentados.', 'Exemplos e testes demonstram que a entrada BERTweet não sofre stemming externo.', 'Mudança de requisito registrada sem alegar implementação da técnica antiga.'], '#5, #9, #10')},
 8: {'title':'[RF06][US06] Integrar tokenização/representação do BERTweet e preservar baseline TF-IDF', 'assignees':ML, 'labels':['prioridade:must','area:ml','tipo:funcionalidade'], 'body':body(
 'Adequar a representação textual ao classificador pré-treinado: a via BERTweet usa seu tokenizador e embeddings próprios, sem vetorizador TF-IDF externo. O baseline scikit-learn/TF-IDF poderá ser preservado como alternativa de comparação, não como requisito de entrada do BERTweet.', 'RF06/US06 (mudança de abordagem)','Sprint 2–3 (replanejada)','Ricardo e Gabriel',
 ['Conferir tokenização na biblioteca e integração ao componente de inferência.', 'Publicar teste básico com frases PT-BR e saída compatível com o classificador.', 'Manter pipeline TF-IDF do baseline isolado, documentando ajuste somente no treino, sem fit no teste.', 'Documentar dependências e migração do requisito RF06 e do teste T07.'],
 ['Inferência BERTweet funciona sem aplicação de TF-IDF externo.', 'Baseline, se mantido, não executa fit sobre dados de teste.', 'Interfaces e decisão arquitetural documentadas; testes pertinentes.'], '#5, #9 e issue de integração do classificador')},
 9: {'title':'[Integração][ML] Encadear pipeline de inferência BERTweet em lote', 'assignees':ML, 'labels':['prioridade:must','area:ml','tipo:funcionalidade'], 'body':body(
 'Integrar a passagem de textos do módulo de aquisição/importação para a classificação BERTweet e produzir registros de resultado compatíveis com a persistência. Esta é responsabilidade de Machine Learning (Ricardo e Gabriel), NÃO da montagem de datasets (Breno).', 'Integração RF03–RF07 / US03–US07','Sprint 2–3 (replanejada)','Ricardo e Gabriel; Breno apenas fornece o contrato dos dados',
 ['Definir entrada em lote com texto_original/id_origem/fonte e metadados opcionais.', 'Chamar o classificador BERTweet uma vez por lote, preservando correspondência entre entrada e saída e separando rótulo original de previsão.', 'Fornecer sentimento, probabilidades, identificação do modelo e metadados para #11; tratar erros sem perda silenciosa de dados.', 'Implementar execução reprodutível e verificação de integração com lotes curtos; documentar contrato com API e banco.'],
 ['Pipeline em lote processa entradas do contrato de dados e devolve saídas no contrato da #11.', 'Sem remoção externa de stopwords, stemming ou TF-IDF na via BERTweet.', 'Testes de ordem, contagem, erros e propagação de metadados publicados; PR revisado.'], '#1, #2, #5–#8, #11 e nova issue RF07')},
 10: {'title':'[Testes] Validar entrada, tokenização e inferência BERTweet com pytest', 'assignees':QA, 'labels':['prioridade:must','area:qualidade','tipo:teste'], 'body':body(
 'Reorientar os testes T04–T07 originalmente ligados a stopwords/stemming/TF-IDF para validar o pipeline BERTweet adotado e seu contrato, sem confundir testes com analisador simulado e validação do modelo real.', 'Suporte RF03–RF07 / testes T04–T07 em revisão','Sprint 2–3 (replanejada)','Renato (QA); apoio de Ricardo/Gabriel',
 ['Criar fixtures com português brasileiro, negação, emojis, URLs, acentuação e textos vazios.', 'Testar preservação da ordem, rótulos POS/NEG/NEU padronizados, probabilidades e metadados.', 'Testar comportamento para lote vazio, texto inválido e falha de inferência; distinguir teste de unidade com mock de teste real com modelo baixado.', 'Validar que o caminho BERTweet não usa transformações externas clássicas.', 'Executar pytest no pipeline CI e registrar total aprovado/falho/ignorado e evidências do PR.'],
 ['Casos unitários e de integração apropriados executam no CI com resultados rastreáveis.', 'Teste com mock não é apresentado como evidência de acurácia real.', 'Entradas e saídas aderem ao contrato de #9 e #11.', 'Roteiro dos testes T04–T07 atualizado com a decisão de escopo.'], '#5–#9, #11 e nova issue RF07')},
 11: {'title':'[Banco] Documentar esquema MongoDB compatível com BERTweet e datasets heterogêneos', 'assignees':DB, 'labels':['prioridade:suporte','area:banco','tipo:preparacao'], 'body':body(
 'Finalizar **somente a definição e documentação** do esquema lógico MongoDB e contrato de integração de dados/classificação. A persistência via pymongo, CRUD, conexão e API NÃO são parte desta issue: ficam para a Sprint 4 e #12.', 'Preparação RF08 / US09','Sprint 2 (documentação e contrato)','Maria Eduarda; revisão de Julia, Ricardo/Gabriel e Breno',
 ['Revisar o documento já publicado em feat/issue-11-esquema-mongodb (campos, tipos, exemplos JSON, índices e decisões).', 'Distinguir id_origem, fonte, texto_original, sentimento previsto, rotulo_original opcional, probabilidades e identificador/versão do modelo.', 'Manter data_publicacao opcional quando ausente e data_processamento obrigatória; filtros devem declarar qual data usam, sem inventar publicação.', 'Validar que texto_tratado seja opcional (BERTweet utiliza tokenizador próprio), e que a estrutura não fique acoplada a um único modelo.', 'Revisar com dados e ML formatos de entrada e saída, índices e tratamento de ausências; atualizar exemplos e abrir PR para branch de integração.'],
 ['Documento com tipos, campos, obrigatoriedade, índices e exemplos mínimo/completo/inválido.', 'Contrato adequado ao dataset real e ao resultado do BERTweet; datas corretamente diferenciadas.', 'Revisão por dados, ML e banco registrada no PR; documentação aprovada pela PO.', 'Nenhuma implementação de MongoDB exigida nesta issue.'], '#3, #9 e nova issue RF07', '## Limite de escopo\nA implementação posterior de persistência pertence à Sprint 4. A #12 cobre apenas ambiente e conectividade. Não exigir feature/CRUD agora.')}
}

newissues = [
 {'title':'[RF07][US07] Integrar classificador BERTweet pré-treinado ao SentIA', 'assignees':ML,'labels':['prioridade:must','area:ml','tipo:funcionalidade'], 'body':body(
 'Integrar o modelo pré-treinado pysentimiento/bertweet-pt-sentiment para inferência de sentimentos em português (positivo, negativo, neutro), com uso pela API futura e sem treinar Transformer do zero.', 'RF07 / US07','Sprint 3 (27/10–02/11/2026)','Ricardo e Gabriel',
 ['Consolidar código existente na branch feat/sentia-modelo no pacote oficial do projeto; definir importação pública e versão do checkpoint.', 'Carregar classificador uma vez; implementar inferência para string e lote, usando o pré-processamento próprio do pysentimiento.', 'Normalizar POS/NEG/NEU e expor sentimento, probabilidades e nome/versão do modelo; não aplicar stemming, stopwords ou TF-IDF externos.', 'Testar entrada vazia, tipo inválido, saída inesperada e erros de inferência; acrescentar pelo menos uma evidência com modelo real.', 'Documentar instalação, custo de inicialização/CPU/RAM e integração ao contrato #9/#11; não versionar pesos pesados.'],
 ['Código inferencia reproduzível em branch/PR com testes de contrato passando.', 'Predições de lote mantêm ordem e devolvem três classes e probabilidades padronizadas.', 'Resultados de mocks explicitamente separados de teste do modelo real.', 'PR revisado/CI e aceite da PO.'], '#3, #5, #8, #9 e #11')},
 {'title':'[RNF01][US08] Avaliar BERTweet com dataset independente e comparar modelos', 'assignees':ML,'labels':['prioridade:must','area:ml','tipo:teste'], 'body':body(
 'Avaliar a qualidade real do BERTweet sobre dados independentes, comparando-o ao baseline clássico no domínio de tweets e documentando riscos de vazamento, incerteza e custos.', 'RNF01 / US08 / GQM Métrica 2.1','Sprint 3 (27/10–02/11/2026)','Ricardo e Gabriel; Breno na proveniência do dataset; Renato na auditoria',
 ['Escolher corpus com Breno; registrar URL, licença/condições, domínio, classes, IDs, tamanho e rótulos.', 'Demonstrar separação de treino/validação/teste sob controle da equipe e investigar possível sobreposição com dados de fine-tuning do modelo pré-treinado.', 'Avaliar BERTweet e baseline nos MESMOS textos, quando comparáveis, sem ajustar hiperparâmetros pelo teste.', 'Publicar acurácia, F1 macro, precision/recall por classe, matriz de confusão, quantidades e margens de incerteza.', 'Medir latência e consumo no ambiente disponível; publicar scripts, seeds, dependências e comandos reprodutíveis.', 'Comparar com meta documental ~80% e recomendar, sem alterar unilateralmente, metas ou escopo.'],
 ['Dataset de teste e proveniência auditáveis; limitações de independência explicitadas.', 'Comparação reproduzível com métricas por classe/domínio e amostras declaradas.', 'Resultados reais publicados em PR, sem apresentar benchmarks externos ou mocks como métricas do SentIA.', 'Decisão fundamentada encaminhada para revisão pela PO.'], '#3 e nova issue RF07')}
]


def gh(args, payload=None):
    command = ['gh', 'api'] + args
    if payload is None:
        p = subprocess.run(command, text=True, capture_output=True)
    else:
        p = subprocess.run(command, input=json.dumps(payload, ensure_ascii=False), text=True, capture_output=True)
    if p.returncode:
        raise RuntimeError(f'Falha: {" ".join(command)}\n{p.stderr.strip()}')
    return json.loads(p.stdout) if p.stdout.strip() else None


def main():
    parser=argparse.ArgumentParser(description='Replanejamento das issues SentIA para BERTweet')
    parser.add_argument('--apply',action='store_true',help='Aplica no GitHub; sem esta opção somente simula')
    args=parser.parse_args()
    try:
        current={n:gh([f'{BASE}/issues/{n}']) for n in updates}
        allitems=gh([f'{BASE}/issues?state=all&per_page=100'])
    except (OSError,RuntimeError) as exc:
        sys.exit(f'ERRO: {exc}\nExecute gh auth status e gh auth login antes.')
    existing_titles={x['title'] for x in allitems if 'pull_request' not in x}
    timestamp=dt.datetime.now().strftime('%Y%m%d-%H%M%S')
    backup=pathlib.Path(f'backup-issues-sentia-{timestamp}.json')
    backup.write_text(json.dumps(current,ensure_ascii=False,indent=2),encoding='utf-8')
    print(f'Backup original criado: {backup.resolve()}')
    print('Modo:', 'APLICAÇÃO REAL' if args.apply else 'SIMULAÇÃO')
    print('\nAtualizações:')
    for n, d in updates.items():
        print(f'  #{n}: {current[n]["title"]}\n      -> {d["title"]} | responsáveis: {", ".join(d["assignees"])}')
    print('\nNovas issues:')
    for d in newissues:
        print(f'  {d["title"]}' + (' [já existe: ignorada]' if d['title'] in existing_titles else ''))
    if not args.apply:
        print('\nNenhuma mudança foi enviada. Para executar: python3 atualizar_issues_sentia.py --apply')
        return
    for n,d in updates.items():
        try:
            result=gh(['-X','PATCH',f'{BASE}/issues/{n}','--input','-'],d)
            print(f'ATUALIZADA #{n}: {result["html_url"]}')
        except Exception as exc:
            print(f'ERRO ao atualizar #{n}: {exc}',file=sys.stderr)
    for d in newissues:
        if d['title'] in existing_titles:
            print('JÁ EXISTE (ignorada):',d['title'])
            continue
        try:
            result=gh(['-X','POST',f'{BASE}/issues','--input','-'],d)
            print(f'CRIADA #{result["number"]}: {result["html_url"]}')
        except Exception as exc:
            print(f'ERRO ao criar {d["title"]}: {exc}',file=sys.stderr)
    print('\nVerifique no GitHub os resultados e o contrato de arquitetura. Nenhuma issue foi fechada.')

if __name__=='__main__':
    main()
