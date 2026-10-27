# template-repository - Branch Main

## Classificação de sentimentos do SentIA

O módulo `classificacao.bertweet` classifica textos em português como
`positivo`, `negativo` ou `neutro`. Ele usa o analisador de sentimentos em
português do [PySentimiento](https://github.com/pysentimiento/pysentimiento),
que carrega o modelo
[`pysentimiento/bertweet-pt-sentiment`](https://huggingface.co/pysentimiento/bertweet-pt-sentiment).
O cartão do modelo informa que a base é o BERTabaporu, uma variante RoBERTa
treinada com tweets em português. Embora o identificador contenha “bertweet”,
essa é a arquitetura/base informada pelo próprio cartão do modelo.

### Instalação e primeira execução

Use Python 3.12 e instale as dependências do projeto:

```bash
python -m pip install -r requirements.txt
```

Na primeira inicialização, o PySentimiento baixa os arquivos do modelo do
Hugging Face e os mantém no cache local. É necessário ter acesso à internet e
espaço em disco nessa primeira execução. Os pesos não devem ser adicionados a
este repositório Git; a biblioteca baixa a versão publicada pelo mantenedor.

### Uso

```python
from classificacao.bertweet import ClassificadorBertweet

# Carregue uma vez na inicialização da aplicação e reutilize a instância.
classificador = ClassificadorBertweet(tamanho_lote=32)

# Rótulos simples
rotulos = classificador.prever(["Adorei o atendimento!", "A entrega atrasou."])

# Rótulo e probabilidades, um resultado para cada texto
resultados = classificador.prever_com_probabilidades(["Adorei o atendimento!"])
```

`prever` retorna uma lista de rótulos. `prever_com_probabilidades` retorna uma
lista de objetos com as chaves `sentimento` e `probabilidades`; as
probabilidades sempre usam as chaves `positivo`, `negativo` e `neutro`.
Uma string isolada é tratada como um único texto. Uma lista vazia retorna uma
lista vazia. Entradas que não sejam strings e textos vazios são rejeitados com
`TypeError` ou `ValueError`. O tamanho do lote precisa ser um inteiro positivo.

O pré-processamento próprio para tweets é realizado pelo PySentimiento; não
aplique TF-IDF, stemming ou remoção de stopwords antes deste classificador.
Este componente fornece inferência, não foi ajustado com dados específicos do
SentIA. Métricas de desempenho do projeto dependem de avaliação com um conjunto
rotulado separado.

Template de Repositório para a matéria de Métodos de Desenvolvimento de Software lecionado pelo professor Ricardo Ajax.

Essa Branch deve ser usada exclusivamente para a versão de produção dos softwares da equipe.

O repositório conta com mais 3 branchs:
* docs: Usada para armazenar a documentação do projeto.
* developer: usada como um intermediário antes do código chegar realmente para produção. É o ambiente ideal para realizar os últimos testes antes das apresentações.
* gh-pages: Local dos arquivos estáticos de deploy da documentação. (Para deploy da documentação, consultar seu monitor)

## Especificações Técnicas do Repositório

Este repositório é planejado e estruturado para que seja realizado documentações de software. Caso haja outra necessidades, deve-se consultar a professora.

Atualmente se usa a ferramenta MkDocs para gerar sua documentação baseado nos seus arquivos markdowns, vocês podem achar mais instruções sobre o MkDocs através do link da documentação da ferramenta: [https://www.mkdocs.org/](https://www.mkdocs.org/).

Também é usado uma "sub-ferramenta" do MkDocs para sua estilização, o Material Theme, que pode ser consultado através do link: [https://squidfunk.github.io/mkdocs-material/](https://squidfunk.github.io/mkdocs-material/).

Este repositório também conta com uma pipeline de automatização de deploy do seu conteúdo MkDocs, para que a cada commit feito na main, a pipeline gere uma versão atualizada da sua documentação em minutos. Vale ressaltar que é importante realizar uma configuração para que tudo funcione da forma correta, as instruções são as seguintes:

* Acesse as configurações do repositório;
* Procure a aba de "Pages"
* Em "Source" escolha a opção "Deploy from a branch";
* Em "Branch" escolha "gh-pages";
* Clique em salvar e pronto;

Após essas etapas de configuração, o seu GitPages deve funcionar normalmente.
