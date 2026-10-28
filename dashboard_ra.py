# 1. IMPORTAÇÃO DE BIBLIOTECAS
import streamlit as st # Usada para criar a interface web do dashboard
import pandas as pd    # Usada para ler, tratar, agrupar e analisar os dados
import os              # Usada para ler os caminhos dos arquivos no seu computador

# 2. CONFIGURAÇÃO INICIAL DA PÁGINA WEB
# Define o título da aba do navegador, o layout em tela cheia e o ícone
st.set_page_config(page_title="Reclame Aqui - Dashboard", layout="wide", page_icon="📊")

# 3. FUNÇÃO DE IMPORTAÇÃO E TRATAMENTO DOS DADOS (ETAPA A)
# O @st.cache_data guarda o resultado na memória. Assim, o site não trava lendo os arquivos CSV novamente toda vez que se clica em um filtro.
@st.cache_data
def load_data():
    # Dicionário mapeando o nome exato do arquivo CSV para o nome da Empresa
    arquivos = {
        "RECLAMEAQUI_NAGEM.csv": "Nagem",
        "RECLAMEAQUI_PAODEACUCAR.csv": "Pão de Açúcar",
        "RECLAMEAQUI_BIGLOJAS.csv": "BIG Lojas",
        "RECLAMEAQUI_CARREFUOR.csv": "Carrefour",
        "RECLAMEAQUI_HAPVIDA.csv": "Hapvida",
        "RECLAMEAQUI_IBYTE.csv": "Ibyte"
    }
    
    df_list = [] # Lista vazia para guardar cada tabela lida
    
    # Descobre o caminho da pasta atual onde este arquivo dashboard_ra.py está salvo
    diretorio_atual = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else os.getcwd()
    
    # Laço de repetição para ler arquivo por arquivo
    for file, empresa in arquivos.items():
        caminho_completo = os.path.join(diretorio_atual, file) # Junta o caminho da pasta com o nome do arquivo CSV (os.path.join), 
                                                                # criando um endereço válido para qualquer sistema operacional.
        
        # Tenta abrir o arquivo. Se achar, lê com pandas e cria a coluna EMPRESA
        if os.path.exists(file): # Verifica se existe
            dft = pd.read_csv(file) # Lê o arquivo CSV com pandas
            dft['EMPRESA'] = empresa # Cria uma nova coluna chamada EMPRESA e preenche com o nome da empresa correspondente
            df_list.append(dft) # Adiciona essa tabela tratada na lista "df_list"
        elif os.path.exists(caminho_completo):
            dft = pd.read_csv(caminho_completo)
            dft['EMPRESA'] = empresa
            df_list.append(dft)
            
    # Se a lista de tabelas estiver vazia, retorna um dataframe vazio para evitar erro
    if not df_list:
        return pd.DataFrame()
        
    # Concatena os 6 arquivos empilhando-os em uma única tabela mestra (df_all)
    df_all = pd.concat(df_list, ignore_index=True)
    
    # --- TRATAMENTO DE DUPLICADOS E NULOS ---
    # Remove registros duplicados baseados no ID da reclamação para garantir todos
    if 'ID' in df_all.columns:
        df_all.drop_duplicates(subset=['ID'], inplace=True)
    else:
        df_all.drop_duplicates(inplace=True)
        
    # Converte a coluna de tempo de Texto para formato de data/hora
    df_all['TEMPO'] = pd.to_datetime(df_all['TEMPO'], errors='coerce')
    df_all = df_all.dropna(subset=['TEMPO']) # Apaga as linhas onde a data ficou nula
    
    # Cria colunas novas separando o ano e o mês
    df_all['ANO_MES'] = df_all['TEMPO'].dt.to_period('M').astype(str)
    df_all['ANO'] = df_all['TEMPO'].dt.year
    df_all['MES'] = df_all['TEMPO'].dt.month
    
    # --- TRATAMENTO DE LOCALIDADE ---
    # Divide a coluna 'LOCAL' (ex: Fortaleza - CE) em duas colunas: CIDADE e ESTADO
    if 'LOCAL' in df_all.columns:
        df_all[['CIDADE', 'ESTADO']] = df_all['LOCAL'].str.split(' - ', n=1, expand=True)
    else:
        df_all['CIDADE'] = 'Não Informado'
        df_all['ESTADO'] = 'Não Informado'
        
    # Corrige problemas de digitação e preenche espaços vazios com 'Não Informado'
    correcao_estados = {'C': 'CE', 'P': 'PE', '--': 'Não Informado', 'naoconsta': 'Não Informado', 'None': 'Não Informado'}
    df_all['ESTADO'] = df_all['ESTADO'].replace(correcao_estados).fillna('Não Informado').str.strip()
    df_all['CIDADE'] = df_all['CIDADE'].replace({'naoconsta': 'Não Informado', '--': 'Não Informado'}).fillna('Não Informado').str.strip()
    
    # --- TRATAMENTO DE TEXTOS ---
    # Coloca os Status no formato de Título
    if 'STATUS' in df_all.columns:
        df_all['STATUS'] = df_all['STATUS'].astype(str).str.strip().str.title()
    
    # Extrai só a categoria principal ignorando os códigos complexos depois do "<->"
    if 'CATEGORIA' in df_all.columns:
        def extrair_categoria(x):
            if '<->' in x and len(x.split('<->')) > 1:
                return x.split('<->')[1].strip().title()
            else:
                return x.strip().title()

        # Passa a função para o .apply() apenas pelo nome
        df_all['CATEGORIA_MACRO'] = df_all['CATEGORIA'].astype(str).apply(extrair_categoria)

    # Retorna o dataframe pronto para uso
    return df_all

# Executa a função e salva na variável principal 'df'
df = load_data()

# Trava a tela com mensagem vermelha caso não ache os CSVs
if df.empty:
    st.error("Arquivos CSV não encontrados na pasta.")
    st.stop()

# 4. CRIAÇÃO DOS FILTROS (BARRA LATERAL)
st.sidebar.header("Filtros") # Título da barra lateral

# Filtro 1: Empresas
empresas = st.sidebar.multiselect("Empresa", sorted(df['EMPRESA'].unique()), default=sorted(df['EMPRESA'].unique()))

# Filtro 2: Período
min_date = df['TEMPO'].min().date()
max_date = df['TEMPO'].max().date()
periodo = st.sidebar.date_input("Período", value=(min_date, max_date), min_value=min_date, max_value=max_date)

# Filtro 3, 4 e 5: Estado, Status e Categoria
estados = st.sidebar.multiselect("Estado", sorted([e for e in df['ESTADO'].unique() if e != 'Não Informado']))
status = st.sidebar.multiselect("Status", sorted(df['STATUS'].unique()))
categorias = st.sidebar.multiselect("Categoria", sorted(df['CATEGORIA_MACRO'].unique()))

# --- APLICAÇÃO DOS FILTROS ---
# Cria uma cópia da base de dados e vai aplicando as regras conforme o usuário escolhe
df_filtrado = df.copy()

if empresas: 
    df_filtrado = df_filtrado[df_filtrado['EMPRESA'].isin(empresas)]
if len(periodo) == 2: 
    df_filtrado = df_filtrado[(df_filtrado['TEMPO'].dt.date >= periodo[0]) & (df_filtrado['TEMPO'].dt.date <= periodo[1])]
if estados: 
    df_filtrado = df_filtrado[df_filtrado['ESTADO'].isin(estados)]
if status: 
    df_filtrado = df_filtrado[df_filtrado['STATUS'].isin(status)]
if categorias: 
    df_filtrado = df_filtrado[df_filtrado['CATEGORIA_MACRO'].isin(categorias)]

# 5. ESTRUTURA PRINCIPAL (TÍTULO E ABAS)
st.title("📊 Análise Reclamações no Reclame Aqui")
st.caption("Análise comparativa de 6 empresas | Módulo 3 Data Analytics")
st.markdown("---")

# Cria 3 abas navegáveis para colocar tudo num único arquivo
aba1, aba2, aba3 = st.tabs(["📈 Dashboard Interativo", "💻 Detalhamento Analítico", "📝 Conclusões do Projeto"])

# ABA 1: DASHBOARD NATIVO
with aba1:
    total_rec = len(df_filtrado)
    total_res = len(df_filtrado[df_filtrado['STATUS'] == 'Resolvido'])
    total_nao_resp = len(df_filtrado[df_filtrado['STATUS'].isin(['Não Respondida', 'Nao Respondida'])])

    # Cálculo da Taxa de Resolução
    if total_rec > 0:
        tx_resolucao = (total_res / total_rec) * 100
    else:
        tx_resolucao = 0

    # Cálculo da Taxa de Resposta
    if total_rec > 0:
        tx_resposta = ((total_rec - total_nao_resp) / total_rec) * 100
    else:
        tx_resposta = 0

    # Cria 4 colunas horizontais e insere as caixas de métricas
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total de reclamações", f"{total_rec:,}".replace(",", "."))
    col2.metric("Taxa de resolução", f"{tx_resolucao:.1f}%")
    col3.metric("Taxa de resposta", f"{tx_resposta:.1f}%")
    col4.metric("Não respondidas", f"{total_nao_resp}")
    st.markdown("---")

    # --- Gráfico 1: Linha de Evolução Mensal ---
    st.subheader("1. Evolução mensal das reclamações")
    df_evo = df_filtrado.groupby('ANO_MES').size() # Conta o volume por mês
    st.line_chart(df_evo) # Renderiza o gráfico de linha nativo do Streamlit

    # Divide a tela em 2 para os gráficos de barras
    c1, c2 = st.columns(2)
    with c1:
        # --- Gráfico 2: Barras de Reclamações por Empresa ---
        st.subheader("2. Reclamações por empresa")
        df_emp = df_filtrado['EMPRESA'].value_counts() # Conta o volume por empresa
        st.bar_chart(df_emp) 

    with c2:
        # --- Gráfico 3: Barras de Distribuição por Status ---
        st.subheader("3. Distribuição por status")
        df_stat = df_filtrado['STATUS'].value_counts() # Conta o volume por status
        st.bar_chart(df_stat)

    # --- Gráfico 4: Top 10 Interativo (Estado vs Cidade) ---
    st.subheader("4. Top 10 Localidades com mais Reclamações")
    
    # Cria o botão de alternância horizontal (Estado ou Cidade)
    visao_local = st.radio("Visualizar ranking por:", ["Estado", "Cidade"], horizontal=True)
    
    # Condição: Conta por Estado se clicar no botão Estado, senão, conta por Cidade
    if visao_local == "Estado":
        df_local = df_filtrado['ESTADO'].value_counts().head(10)
    else:
        df_local = df_filtrado['CIDADE'].value_counts().head(10)
        
    # Renderiza o gráfico de barras e força elas a ficarem horizontais
    st.bar_chart(df_local, horizontal=True)

    st.markdown("---")
    st.subheader("Tabela de Registros")
    # Mostra um DataFrame filtrando colunas relevantes, ordenando por data (mais recente) e mostrando só 300
    st.dataframe(df_filtrado[['ID', 'EMPRESA', 'TEMPO', 'ESTADO', 'CIDADE', 'STATUS', 'CATEGORIA_MACRO', 'DESCRICAO']].sort_values(by='TEMPO', ascending=False).head(300))

# ABA 2: DETALHAMENTO ANALÍTICO
with aba2:
    st.header("Detalhamento Analítico")
    st.markdown("Visão tabular aprofundada dos principais indicadores e cruzamentos de dados entre as empresas avaliadas.")
    
    st.subheader("1. Resumo Histórico por Empresa")
    st.markdown("Volume total e intervalo de datas dos registros coletados para cada companhia.")
    
    # Agrupa por Empresa e faz múltiplos cálculos (agg) simultaneamente
    df_agg = df.groupby('EMPRESA').agg(
        Total_Reclamacoes=('ID', 'count'),
        Primeiro_Registro=('TEMPO', 'min'),
        Ultimo_Registro=('TEMPO', 'max')
    ).sort_values('Total_Reclamacoes', ascending=False)
    
    # Formata a data
    df_agg['Primeiro_Registro'] = df_agg['Primeiro_Registro'].dt.strftime('%Y-%m-%d')
    df_agg['Ultimo_Registro'] = df_agg['Ultimo_Registro'].dt.strftime('%Y-%m-%d')
    st.dataframe(df_agg, use_container_width=True) # Renderiza ocupando a largura total
    
    # Uso de pivot_table()
    st.subheader("2. Matriz de Atendimento: Empresa vs Status")
    st.markdown("Distribuição do volume de chamados de acordo com o status atual do processo.")
    
    # Cria matriz cruzada (Empresas nas linhas, Status nas colunas) contando pelo ID e preenchendo vazios com Zero
    pivot_status = pd.pivot_table(df, index='EMPRESA', columns='STATUS', values='ID', aggfunc='count', fill_value=0)
    st.dataframe(pivot_status, use_container_width=True)
    
    st.markdown("---")
    
    # Divide a tela em 2
    c3, c4 = st.columns(2)
    
    with c3:
        st.subheader("3. Principais Motivos de Reclamação")
        st.markdown("Ranking das 5 categorias com maior volume de queixas.")
        
        # 1. Limpeza dos textos
        motivos_limpos = (
            df['CATEGORIA_MACRO']
            .astype(str)
            .str.replace(' - Loja Física', '', regex=False)
            .str.replace(' Loja Física', '', regex=False)
            .str.replace('Big', '', case=False)
            .str.replace('Nagem', '', case=False)
            .str.replace('Ibyte', '', case=False)
            .str.replace('Carrefour', '', case=False)
            .str.replace('-', '', regex=False)
            .str.strip()
        )
        
        # Preenche os campos que ficaram em branco com o texto padrão
        motivos_limpos = motivos_limpos.replace('', 'Problemas Gerais em Loja')
        
        # 2. Contagem depois da limpeza (agrupa os valores repetidos)
        df_motivos = motivos_limpos.value_counts().reset_index()
        df_motivos.columns = ['Motivo da Reclamação', 'Quantidade']
        
        # Exibe o Top 5 correto sem duplicados
        st.dataframe(df_motivos.head(5), use_container_width=True, hide_index=True)

    with c4:
        st.subheader("4. Principais Polos (Estado e Cidade)")
        st.markdown("Detalhamento cruzado das localidades exatas com mais registros.")
        
        # Agrupa cruzando Estado e Cidade ao mesmo tempo
        df_locais = df.groupby(['ESTADO', 'CIDADE']).size().reset_index(name='Volume').sort_values('Volume', ascending=False).head(5)
        
        # Exibe a tabela alinhada corretamente dentro da coluna 4
        st.dataframe(df_locais, use_container_width=True, hide_index=True)

# ABA 3: Conclusões e Respostas
with aba3:
    st.header("Conclusões e Respostas do Projeto")
    
    # Caixa com o texto respondendo aos 6 itens do trabalho e 2 extras
    st.info("""
    **1. Qual empresa possui mais reclamações?**  
    A **Hapvida** lidera o volume absoluto com 1.016 reclamações originais, seguida por Pão de Açúcar e Nagem (ambas com 1.000 chamados originais antes da verificação rigorosa de duplicados).

    **2. Qual empresa apresenta a maior taxa de resolução?**  
    A **Ibyte** destaca-se com o melhor desempenho, apresentando uma taxa de resolução próxima dos 43%.

    **3. Quais são as categorias mais reclamadas?**  
    Os maiores volumes estão ligados aos problemas de "Loja Física" genérica (Nagem e BIG Lojas) e problemas de "Dificuldade para agendamento de exames/consultas" da Hapvida.

    **4. Como as reclamações evoluíram ao longo do tempo?**  
    Houve uma estabilidade entre 2017 e 2020. Em 2021 as reclamações triplicaram e atingiram um pico histórico alarmante em 2022.

    **5. Quais estados ou cidades concentram mais reclamações?**  
    Em nível estadual, **São Paulo (SP)** lidera disparado, seguido pelo Ceará (CE). Nas cidades, a capital São Paulo e Fortaleza concentram os maiores volumes de registos.

    **6. Qual empresa possui o maior percentual de reclamações não respondidas?**  
    A **Hapvida**, que apresenta um cenário crítico de atendimento, deixando mais de 60% dos seus chamados retidos no status "Não Respondida".
    
    ---
    **PERGUNTAS ADICIONAIS (EXTRAS):**
    
    **7. (Extra 1) Qual mês do ano concentra historicamente o maior volume de problemas (Sazonalidade)?**  
    O mês de **Agosto** acumula o maior pico de reclamações registradas ao analisar todo o histórico sazonal das empresas.
    
    **8. (Extra 2) Qual empresa possui o maior volume absoluto de status dado explicitamente como "Não Resolvido"?**  
    A **BIG Lojas**, que registrou a maior quantidade de encerramentos onde o consumidor declarou de forma definitiva que o problema não teve solução final.
    """)