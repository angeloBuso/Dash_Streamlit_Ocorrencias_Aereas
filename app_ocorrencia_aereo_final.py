# importar bibliotecas
import pandas as pd
import streamlit as st
# pip install --force-reinstall streamlit==0.69
import pydeck as pdk
import matplotlib.pyplot as plt
import seaborn as sns

# Variáveis Globais
ocorrencia = 'https://raw.githubusercontent.com/angeloBuso/Dash_Streamlit_Ocorrencias_Aereas/master/dataSet/ocorrencia_2010_2020_lat_lon_etl.csv'
aeronave = 'https://raw.githubusercontent.com/angeloBuso/Dash_Streamlit_Ocorrencias_Aereas/master/dataSet/aeronave_2010_2020.csv'
ocorrencia_tp = 'https://raw.githubusercontent.com/angeloBuso/Dash_Streamlit_Ocorrencias_Aereas/master/dataSet/ocorrencia_tipo_2010_2020.csv'

index_coluna = "codigo_ocorrencia"

# 1. Definição função carregará dataSet, limpeza e tratamento dos dados

# armazenar em cache os dados carregados -> otimiza memória
@st.cache(suppress_st_warning=True)

def load_data():
    """ Pipeline
    Carrega o dataSet, realiza pré-processamento/limpeza/tratamento
    :return: dataSet com os atributos relevantes para o Dash
    """
    # a. carga dados
    df1= pd.read_csv(ocorrencia, sep= ';')
    df2 = pd.read_csv(aeronave, sep= ';')
    df3 = pd.read_csv(ocorrencia_tp, sep= ';')

    # a.1 dados combinados
        # a.1.1 df1 & df3
    dados= pd.merge(df1,df3, how= 'left', on= 'codigo_ocorrencia1')
        # a.1.2 df1 & df2
    dados= pd.merge(dados, df2, how= 'left', on= 'codigo_ocorrencia2')

    # b. feature selection, rename labels e indicação de indice
    colunas = {
        'ocorrencia_latitude': 'latitude',
        'ocorrencia_longitude': 'longitude',
        'ocorrencia_dia': 'data',
        'ocorrencia_classificacao': 'classificacao',
        'ocorrencia_cidade': 'cidade',
        'ocorrencia_uf': 'uf',
        'total_aeronaves_envolvidas': 'aeronaves_envolvidas',
        'ocorrencia_tipo': 'tipo',
        'ocorrencia_tipo_categoria': 'tipo_categoria',
        'aeronave_tipo_veiculo': 'tipo_veiculo',
        'aeronave_registro_segmento': 'registro_segmento',
        'aeronave_fase_operacao': 'fase_operacao',
        'aeronave_tipo_operacao': 'tipo_operacao',
        'aeronave_nivel_dano': 'nivel_dano',
        'aeronave_fatalidades_total': 'fatalidades'
    }
    dados.index = dados[index_coluna]
    dados = dados.rename(columns=colunas)


    # c. dateTime atributo "data"
    dados['data'] = dados['data'] + " " + dados['ocorrencia_hora']
    # dados.data = dados.data + " " + dados.ocorrencia_hora
    dados.data = pd.to_datetime(dados.data)

    # d. tratando informações de lat e long (identificado apenas no final do projeto)
    # d.1 agrupo e identifico qual métrica busco
    media_lat = dados.groupby('cidade')['latitude'].transform('mean')
    media_lng = dados.groupby('cidade')['longitude'].transform('mean')

    # d.2  aplico
    dados['latitude'].fillna(media_lat, inplace=True)
    dados['longitude'].fillna(media_lng, inplace=True)

    # e. filtro dataSet pelas feature selection
    dados = dados[list(colunas.values())]

    return dados

# 1.1 Carregando os dados.
df = load_data()

# 2. Obtendo uma lista das variáveis unicas das categorias do atributo
classifier = df.classificacao.unique().tolist()

# 3. Construindo Dashboard

# 3.1 SideBar -> ambiente de controle
    # a. Placeholder, designação local (.empty() indica que recebrá alguma informação)
st.sidebar.header("Parâmetros de Controle")
info_sidebar = st.sidebar.empty()

    # b. filtro 1 - slider ano
st.sidebar.subheader("Ano")
var_slider = st.sidebar.slider("Selecione o ano", 2010, 2020, 2020)

    # c. checkBox tabela - carrega a tabela filtrada com um Placeholder.empty()
st.sidebar.subheader("Carregar os dados selecionados?")
tabela = st.sidebar.empty()

    # d. filtro 2 - multi selector
# st.sidebar.subheader("Escolha por classificação acidente")
# options e default caso não for var_globla/indicada tem q passar em uma lista
var_selector= st.sidebar.multiselect(
    label= "Escolha o tipo da ocorrência",
    options= classifier,
    default= classifier
)

    # e. aplicando os 2 "&" filtros no dataSet
df_filtrado = df[(df.data.dt.year == var_slider) & (df.classificacao.isin(var_selector))]

    # f. retornando com os preenchimentos dos Placeholders
info_sidebar.info("{} ocorrências selecionadas." .format(df_filtrado.shape[0], var_slider))

    # g. evolução por ano
acidentes_por_ano = df.data.dt.year.value_counts().sort_index()
st.sidebar.subheader("Evolução")
st.sidebar.bar_chart(acidentes_por_ano, height=150)

    # h. complementando informações com os Markdows
st.sidebar.markdown("""
        **Finalidades das aeronaves**
* `PRIVADA` aeronaves utilizadas para serviços realizados sem remuneração, em benefício dos proprietários ou operadores.
* `REGULAR` aeronaves utilizadas para serviços de transporte aéreo público, realizado por pessoas jurídicas brasileiras.
* `INSTRUÇÃO` aeronaves utilizadas apenas na instrução, treinamento e adestramento de voo pelos aeroclubes aprovados pela ANAC.
* `TÁXI AÉREO` aeronaves utilizadas para serviços de transporte aéreo público não regular de passageiro ou carga, mediante remuneração convencionada entre o usuário e o transportador.
* `AGRÍCOLA`  aeronaves usadas no fomento ou proteção da agricultura em geral.
* `EXPERIMENTAL` aeronaves visando à certificação na categoria experimental.   
    
    Fonte de dados das ocorrências aeronáuticas:
     ***Centro de Investigação e Prevenção de Acidentes Aeronáuticos (CENIPA)***
""")

# 3.2 Main -> corpo do dash
st.title("Visualizando Resultados")

    # a. informações interativas com filtros escolhidos
md_diaria = round(df_filtrado.shape[0]/365,2)
fatalidade = df_filtrado.fatalidades.sum()

st.markdown(f"""
            ℹ️ Estão sendo exibidas as ocorrências classificadas como **{", ".join(var_selector)}**
            para o ano de **{var_slider}**, o que correspondeu uma média diária de **{md_diaria}** ocorrências.
            Ao todo teve {fatalidade} fatalidades registradas.
            """)

    # b. mostrando os dados filtrados
segmento_filtrado = pd.DataFrame(df_filtrado['registro_segmento'].
                        value_counts(normalize=True)).reset_index()
fig, ax = plt.subplots() #figsize=(15,8)
sns.barplot(x=segmento_filtrado['index'],
            y=segmento_filtrado['registro_segmento'], color="#3182bd", ax=ax)
ax.set_ylabel('')
ax.set_xlabel('')
ax.set_title('Percentual de ocorrências por Finalidade')
ax.set_xticklabels(segmento_filtrado['index'], rotation= 90)


uf_filtrado = pd.DataFrame(df_filtrado['uf'].
                        value_counts(normalize=True)).reset_index()
fig1, ax1 = plt.subplots()
sns.barplot(x=uf_filtrado['index'],
            y=uf_filtrado['uf'], color="#3182bd", ax=ax1)
ax1.set_ylabel('')
ax1.set_xlabel('')
ax1.set_title('Percentual de ocorrências por Estados')
ax1.set_xticklabels(uf_filtrado['index'], rotation= 90)

#fase_filtrado = pd.DataFrame(df_filtrado['fase_operacao'].
#                        value_counts(normalize=True)).reset_index()
#fig2, ax2 = plt.subplots()
#sns.barplot(x=fase_filtrado['index'],
#            y=fase_filtrado['fase_operacao'], color="#3182bd", ax=ax2)
#ax2.set_ylabel('')
#ax2.set_xlabel('')
#ax2.set_title('Fase operação da aeronave')
#ax2.set_xticklabels(fase_filtrado['index'], rotation= 90)

if tabela.checkbox("Sim"):
    st.write(df_filtrado)
    st.write('')
    finalidade, estado = st.beta_columns(2)

    with finalidade:
        st.pyplot(fig)

    with estado:
        st.pyplot(fig1)

    #st.pyplot(fig2)


# c. (3) os dados possuem Lat e Lon, logo podemos inserir um mapa
st.subheader("Local das ocorrências")
st.markdown("""
    Mapa possui interatividade, basta usar o *mouse* e navegar
""")
st.map(df_filtrado)

st.subheader("Mapa de Calor")
# c. (1) os dados possuem Lat e Lon, logo podemos inserir um mapa com PyDeck
# Pydeck trabalha com estrutura de Grid Layers sendo cada objeto trabalhado de forma isolada.
# i . indicamos o ponto incial em que o mapa será aberto, além de informar o nível de zoom;
# ii. posterior são inseridos os objetos do tipo "layer"
# c. (2) Pydeck heatmap
st.pydeck_chart(pdk.Deck(
    initial_view_state=pdk.ViewState(
        latitude=-22.85481,
        longitude=-43.17896,
        zoom=3,
        pitch=50
    ),
    layers=[
        pdk.Layer(
            'HeatmapLayer',
            data= df_filtrado,
            opacity=0.9,
            disk_resolution=12,
            radius=30000,
            get_position='[longitude, latitude]',
            get_fill_color='[255, 255, 255, 255]',
            get_line_color='[255, 255, 255]',
            auto_highlight=True,
            elevation_scale=1000,
            # elevation_range=[0, 3000],
            # get_elevation="norm_price",
            pickable=True,
            extruded=True,
        ),
        pdk.Layer(
            'ScatterplotLayer',
            data = df_filtrado,
            get_position='[longitude, latitude]',
            get_color='[255, 255, 255, 30]',
            get_radius=60000,
        ),
    ],
))