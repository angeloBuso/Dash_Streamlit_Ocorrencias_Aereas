# importar bibliotecas
import pandas as pd
import streamlit as st
# pip install --force-reinstall streamlit==0.69
import pydeck as pdk

# Variáveis Globais
dataFrame = "https://raw.githubusercontent.com/carlosfab/curso_data_science_na_pratica/master/modulo_02/ocorrencias_aviacao.csv"
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
    dados = pd.read_csv(dataFrame, index_col=index_coluna)

    # b. feature selection e rename labels
    colunas = {
        'ocorrencia_latitude': 'latitude',
        'ocorrencia_longitude': 'longitude',
        'ocorrencia_dia': 'data',
        'ocorrencia_classificacao': 'classificacao',
        'ocorrencia_tipo': 'tipo',
        'ocorrencia_tipo_categoria': 'tipo_categoria',
        'ocorrencia_tipo_icao': 'tipo_icao',
        'ocorrencia_aerodromo': 'aerodromo',
        'ocorrencia_cidade': 'cidade',
        'investigacao_status': 'status',
        'divulgacao_relatorio_numero': 'relatorio_numero',
        'total_aeronaves_envolvidas': 'aeronaves_envolvidas'
    }
    dados = dados.rename(columns=colunas)

    # c. dateTime atributo "data"
    dados['data'] = dados['data'] + " " + dados['ocorrencia_horario']
    # dados.data = dados.data + " " + dados.ocorrencia_horario
    dados.data = pd.to_datetime(dados.data)

    # d. apenas lat e long BR -> eliminando outlier do dataSet original (identificado apenas no final do projeto)
    lat_BRi, lat_BRf, lon_BRi, lon_BRf = [-33.69111, 2.81972, -72.89583, -34.80861]
    dados= dados[
        dados.latitude.between(lat_BRi, lat_BRf, inclusive= True) &
        dados.longitude.between(lon_BRi, lon_BRf, inclusive= True)
    ]

    # e. filtro dataSet pelas feature selection
    dados = dados[list(colunas.values())]

    return dados

# 1.1 Carregando os dados
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
var_slider = st.sidebar.slider("Selecione o ano", 2008, 2018, 2016)

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

    # g. complementando informações com os Markdows
st.sidebar.markdown("""
    Fonte de dados das ocorrências aeronáuticas:
     ***Centro de Investigação e Prevenção de Acidentes Aeronáuticos (CENIPA)***
""")

# 3.2 Main -> corpo do dash
st.title("Visualizando Resultados")

    # a. informações interativas com filtros escolhidos
st.markdown(f"""
            ℹ️ Estão sendo exibidas as ocorrências classificadas como **{", ".join(var_selector)}**
            para o ano de **{var_slider}**.
            """)

    # b. mostrando os dados filtrados
if tabela.checkbox("Sim"):
    st.write(df_filtrado)

    # c. (1) os dados possuem Lat e Lon, logo podemos inserir um mapa com PyDeck
st.subheader("Mapa de ocorrências")

# Pydeck trabalha com estrutura de Grid Layers sendo cada objeto trabalhado de forma isolada.
# i . indicamos o ponto incial em que o mapa será aberto, além de informar o nível de zoom;
# ii. posterior são inseridos os objetos do tipo "layer"

st.pydeck_chart(pdk.Deck(
    initial_view_state=pdk.ViewState(
        latitude=-22.85481,
        longitude=-43.17896,
        zoom=3,
        pitch=50
    ),
    layers=[
        pdk.Layer(
            'HexagonLayer',
            data= df_filtrado,
            disk_resolution=12,
            radius=30000,
            get_position='[longitude, latitude]',
            get_fill_color='[255, 255, 255, 255]',
            get_line_color='[255, 255, 255]',
            auto_highlight=True,
            elevation_scale=1500,
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

    # c. (3) os dados possuem Lat e Lon, logo podemos inserir um mapa
st.subheader("Local das ocorrências")
st.map(df_filtrado)

