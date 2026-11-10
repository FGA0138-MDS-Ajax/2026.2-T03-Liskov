"""Testes adicionais exclusivos da homologação experimental dos PRs #44/#45."""
import csv
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
from bson import BSON
from scripts.comparar_modelos import dividir_tweetsentbr, normalizar_texto
from src.processamento.aquisicao import adquirir_dados
from src.processamento.classificacao.avaliacao import avaliar
from src.processamento.classificacao.bertweet import ClassificadorBertweet
from src.processamento.pipeline import ErroPipeline, PipelineClassificacao

TEXTOS = ['Adorei o atendimento! 😊', 'Não gostei do atendimento! 😠', 'O produto chegou hoje.']
SIGLAS = ['POS', 'NEG', 'NEU']
PT = ['positivo', 'negativo', 'neutro']

class AnalisadorEspiao:
    def __init__(self): self.recebidos = []
    def predict(self, textos):
        assert isinstance(textos, list) and all(isinstance(t, str) for t in textos)
        self.recebidos.extend(textos)
        return [SimpleNamespace(output=SIGLAS[TEXTOS.index(t)], probas={s: .8 if s==SIGLAS[TEXTOS.index(t)] else .1 for s in SIGLAS}) for t in textos]

@pytest.fixture
def csv_sintetico(tmp_path):
    caminho=tmp_path/'sintetico.csv'
    with caminho.open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=['id','texto','rotulo','fonte','data','categoria'])
        w.writeheader()
        for i,(texto,rotulo) in enumerate(zip(TEXTOS,SIGLAS)):
            w.writerow(dict(id=f'syn-{i}',texto=texto,rotulo=rotulo,fonte='sintetica',data='',categoria=f'grupo-{i}'))
    return caminho

def assert_contrato(doc):
    for key in ['id_origem','fonte','texto_original','sentimento']:
        assert isinstance(doc[key],str) and doc[key].strip()
    assert doc['sentimento'] in PT
    assert isinstance(doc['modelo']['nome'],str) and doc['modelo']['nome']
    assert isinstance(doc['data_processamento'],datetime) and doc['data_processamento'].utcoffset().total_seconds()==0
    assert set(doc['probabilidades'])==set(PT)
    assert sum(doc['probabilidades'].values())==pytest.approx(1)
    BSON.encode(doc)  # serialização BSON, sem conexão ou gravação no MongoDB

def test_csv_aquisicao_classificacao_avaliacao_bson(csv_sintetico):
    registros=adquirir_dados(csv_sintetico)
    assert [r['texto_original'] for r in registros]==TEXTOS
    assert [r['rotulo_original'] for r in registros]==SIGLAS
    spy=AnalisadorEspiao()
    clf=ClassificadorBertweet(analisador=spy,tamanho_lote=2)
    resultados=PipelineClassificacao(classificador=clf,tamanho_lote=2).processar_csv(str(csv_sintetico))
    assert spy.recebidos==TEXTOS
    assert [r['id_origem'] for r in resultados]==['syn-0','syn-1','syn-2']
    assert [r['sentimento'] for r in resultados]==PT
    for i,doc in enumerate(resultados):
        assert_contrato(doc)
        assert doc['fonte']=='sintetica'
        assert doc['metadados']=={'categoria':f'grupo-{i}'}
        assert doc['rotulo_original']==SIGLAS[i]
        assert doc['rotulo_padronizado']==PT[i]
        assert 'data_publicacao' not in doc
    m=avaliar(SIGLAS,[r['sentimento'] for r in resultados])
    assert m['acuracia']==pytest.approx(1)
    assert m['f1_macro']==pytest.approx(1)
    assert m['matriz_confusao']==[[1,0,0],[0,1,0],[0,0,1]]

def test_rotulo_humano_nao_e_substituido_por_previsao(csv_sintetico):
    registros=adquirir_dados(csv_sintetico)
    registros[0]['rotulo_original']='NEG'; registros[0]['rotulo_padronizado']='NEG'
    docs=PipelineClassificacao(classificador=ClassificadorBertweet(analisador=AnalisadorEspiao())).processar_registros(registros)
    assert docs[0]['rotulo_original']=='NEG' and docs[0]['rotulo_padronizado']=='negativo'
    assert docs[0]['sentimento']=='positivo'
    assert avaliar([d['rotulo_padronizado'] for d in docs],[d['sentimento'] for d in docs])['acuracia']==pytest.approx(2/3)

def test_particao_agrupa_duplicatas_e_exclui_conflitos(tmp_path):
    caminho=tmp_path/'grupos.csv'
    with caminho.open('w',encoding='utf-8',newline='') as f:
        w=csv.writer(f); w.writerow(['texto','rotulo','fonte'])
        for i in range(30):
            texto=f'Produto numero {i}'
            w.writerow([texto,SIGLAS[i%3],'sintetica'])
            w.writerow(['  '+texto.upper()+'  ',SIGLAS[i%3],'sintetica'])
        w.writerow(['Conflito','POS','sintetica']); w.writerow(['CONFLITO','NEG','sintetica'])
    xt,yt,xv,yv=dividir_tweetsentbr(str(caminho))
    a={normalizar_texto(t) for t in xt}; b={normalizar_texto(t) for t in xv}
    assert not a & b and len(xt)+len(xv)==60
    assert 'conflito' not in a|b
    assert dividir_tweetsentbr(str(caminho))==(xt,yt,xv,yv)

class ClassificadorSaida:
    nome_modelo='modelo-teste'
    sentimento='positivo'
    def prever_com_probabilidades(self,textos):
        return [dict(sentimento=self.sentimento,probabilidades=dict(positivo=.8,negativo=.1,neutro=.1)) for _ in textos]

def reg():
    return dict(id_origem='syn',fonte='sintetica',texto_original='Texto',data_publicacao=None)

@pytest.mark.parametrize('campo',['id_origem','fonte'])
@pytest.mark.parametrize('valor',[None,''])
def test_pipeline_rejeita_identificacao_obrigatoria_invalida(campo,valor):
    r=reg(); r[campo]=valor
    with pytest.raises(ErroPipeline):
        PipelineClassificacao(classificador=ClassificadorSaida()).processar_registros([r])

@pytest.mark.parametrize('sentimento',[None,''])
def test_pipeline_rejeita_sentimento_ausente(sentimento):
    clf=ClassificadorSaida(); clf.sentimento=sentimento
    with pytest.raises(ErroPipeline):
        PipelineClassificacao(classificador=clf).processar_registros([reg()])

def test_pipeline_aceita_data_calendario_prevista_no_contrato():
    r=reg(); r['data_publicacao']='2026-10-01'
    docs=PipelineClassificacao(classificador=ClassificadorSaida()).processar_registros([r])
    assert docs[0]['data_publicacao']==datetime(2026,10,1,tzinfo=timezone.utc)
