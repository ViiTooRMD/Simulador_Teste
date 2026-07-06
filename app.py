import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# 1. Configuração da Página e Identidade Visual Jamef
st.set_page_config(
    page_title="Simulador de Custos e Fretes - Jamef",
    page_icon="🚛",
    layout="wide",
)

# Estilização CSS para injetar a marca Jamef na aplicação (Azul #002855 e Vermelho #E30613)
st.markdown("""
    <style>
    .stApp {
        background-color: #F8F9FA;
    }
    h1, h2, h3 {
        color: #002855 !important;
        font-family: 'Helvetica Neue', sans-serif;
    }
    /* Estilo dos Botões Jamef (Vermelho) */
    div.stButton > button:first-child {
        background-color: #E30613 !important;
        color: white !important;
        border-radius: 6px !important;
        border: none !important;
        font-weight: bold !important;
        padding: 0.6rem 1.2rem !important;
        transition: all 0.3s ease;
    }
    div.stButton > button:first-child:hover {
        background-color: #002855 !important;
        color: white !important;
    }
    /* Estilo customizado do Sidebar (Azul Escuro) */
    [data-testid="stSidebar"] {
        background-color: #002855 !important;
    }
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3, [data-testid="stSidebar"] p, [data-testid="stSidebar"] label {
        color: #FFFFFF !important;
    }
    /* Cards de KPI */
    .metric-card {
        background-color: white;
        padding: 20px;
        border-radius: 8px;
        border-left: 5px solid #E30613;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
        margin-bottom: 15px;
    }
    </style>
""", unsafe_allow_html=True)

# 2. Tabelas Padrão "Embarcadas" (Mock para o MVP)
@st.cache_data
def carregar_tabelas_padrao():
    # Tabela de Frete Padrão (Passo 3)
    frete_data = [
        {"cidade_origem": "Curitiba", "cidade_destino": "SÃO PAULO", "uf_destino": "SP", "frete_peso_minimo": 150.0, "frete_excedente_por_kg": 1.2},
        {"cidade_origem": "Curitiba", "cidade_destino": "CAMPINAS", "uf_destino": "SP", "frete_peso_minimo": 180.0, "frete_excedente_por_kg": 1.5},
        {"cidade_origem": "Curitiba", "cidade_destino": "BELO HORIZONTE", "uf_destino": "MG", "frete_peso_minimo": 220.0, "frete_excedente_por_kg": 1.8},
        {"cidade_origem": "Curitiba", "cidade_destino": "RIO DE JANEIRO", "uf_destino": "RJ", "frete_peso_minimo": 250.0, "frete_excedente_por_kg": 2.0},
        {"cidade_origem": "Curitiba", "cidade_destino": "PALMAS", "uf_destino": "TO", "frete_peso_minimo": 350.0, "frete_excedente_por_kg": 3.2},
        {"cidade_origem": "Curitiba", "cidade_destino": "MACEIO", "uf_destino": "AL", "frete_peso_minimo": 420.0, "frete_excedente_por_kg": 4.1},
        {"cidade_origem": "Curitiba", "cidade_destino": "RIO LARGO", "uf_destino": "AL", "frete_peso_minimo": 400.0, "frete_excedente_por_kg": 3.9},
    ]
    # Tabela de Custo Padrão/Rateio (Passo 4)
    custo_data = [
        {"cidade_origem": "Curitiba", "cidade_destino": "SÃO PAULO", "uf_destino": "SP", "custo_fixo_por_viagem": 80.0, "custo_variavel_por_kg": 0.45},
        {"cidade_origem": "Curitiba", "cidade_destino": "CAMPINAS", "uf_destino": "SP", "custo_fixo_por_viagem": 100.0, "custo_variavel_por_kg": 0.55},
        {"cidade_origem": "Curitiba", "cidade_destino": "BELO HORIZONTE", "uf_destino": "MG", "custo_fixo_por_viagem": 120.0, "custo_variavel_por_kg": 0.70},
        {"cidade_origem": "Curitiba", "cidade_destino": "RIO DE JANEIRO", "uf_destino": "RJ", "custo_fixo_por_viagem": 150.0, "custo_variavel_por_kg": 0.85},
        {"cidade_origem": "Curitiba", "cidade_destino": "PALMAS", "uf_destino": "TO", "custo_fixo_por_viagem": 210.0, "custo_variavel_por_kg": 1.10},
        {"cidade_origem": "Curitiba", "cidade_destino": "MACEIO", "uf_destino": "AL", "custo_fixo_por_viagem": 280.0, "custo_variavel_por_kg": 1.45},
        {"cidade_origem": "Curitiba", "cidade_destino": "RIO LARGO", "uf_destino": "AL", "custo_fixo_por_viagem": 270.0, "custo_variavel_por_kg": 1.40},
    ]
    return pd.DataFrame(frete_data), pd.DataFrame(custo_data)

df_frete_padrao, df_custo_padrao = carregar_tabelas_padrao()

# Header Principal
st.title("Simulador de Custos e Fretes — Jamef")
st.caption("Plataforma Interna de Simulação e Viabilidade de Negócios")
st.markdown("---")

# ==========================================
# STEP I — PARAMETRIZAÇÃO (MENU LATERAL)
# ==========================================
st.sidebar.markdown("<h2 style='text-align: center; color: white;'>JAMEF</h2>", unsafe_allow_html=True)
st.sidebar.header("🛠️ Passo 1: Parâmetros")

cidade_origem = st.sidebar.selectbox("Cidade de Origem", ["Curitiba", "São Paulo", "Belo Horizonte"])
st.sidebar.text_input("Filial / PMV", value="Filial Curitiba - PR", disabled=True)
st.sidebar.text_input("Sigla Filial", value="CWB", disabled=True)

cargo_vendedor = st.sidebar.selectbox("Alçada do Usuário", ["Vendedor", "Gerente Regional", "Diretor/Pricing"])

# Trava dinâmica de alçada comercial
if cargo_vendedor == "Vendedor":
    desconto_max = 5.0
elif cargo_vendedor == "Gerente Regional":
    desconto_max = 15.0
else:
    desconto_max = 100.0

desconto_aplicado = st.sidebar.slider(
    "Desconto Comercial (%)", 
    min_value=0.0, 
    max_value=float(desconto_max), 
    value=0.0, 
    step=0.5,
    help="O limite de desconto é definido conforme a alçada comercial selecionada."
)

margem_alvo = st.sidebar.number_input("Margem Alvo Esperada (%)", min_value=1.0, max_value=100.0, value=15.0)

# ==========================================
# STEP II — FLUXO DE DADOS (UPLOAD DO ARQUIVO)
# ==========================================
st.header("📥 Passo 2: Upload do Histórico")

col1, col2 = st.columns(2)

with col1:
    uploaded_file = st.file_uploader(
        "Arraste e solte o arquivo de simulação (.csv ou .xlsx)", 
        type=["csv", "xlsx"],
        help="O arquivo deve conter as colunas: Cidade Destino, UF, Peso Real, Peso Cubado, Volume, Data Movimento, CNPJ_Destinatario, Valor Mercadoria"
    )

with col2:
    st.write(" ")
    st.write(" ")
    usar_exemplo = st.button("💡 Usar Dados de Exemplo (Testar sem arquivo)")

df_usuario = None

# Geração de dados de exemplo (baseados no seu print)
if usar_exemplo:
    dados_exemplo = {
        "Cidade Destino": ["PALMAS", "MACEIO", "RIO LARGO"],
        "UF": ["TO", "AL", "AL"],
        "Peso Real": [84.00, 234.00, 93.00],
        "Peso Cubado": [193.08, 459.03, 202.44],
        "Volume": [2, 4, 2],
        "Data Movimento": ["21/10/2025", "23/10/2025", "31/10/2025"],
        "CNPJ_Destinatario": ["06057223037504", "06057223037504", "06057223037504"],
        "Valor Mercadoria": [9178.41, 17853.74, 9620.00]
    }
    df_usuario = pd.DataFrame(dados_exemplo)
    st.success("✓ Dados de simulação de exemplo carregados com sucesso!")
elif uploaded_file is not None:
    try:
        if uploaded_file.name.endswith('.csv'):
            df_usuario = pd.read_csv(uploaded_file, sep=None, engine='python')
        else:
            df_usuario = pd.read_excel(uploaded_file)
        st.success(f"✓ Arquivo '{uploaded_file.name}' validado com sucesso!")
    except Exception as e:
        st.error(f"Erro ao ler o arquivo: {e}")

# ==========================================
# CÁLCULOS (STEPS III E IV — FRETE E CUSTO)
# ==========================================
if df_usuario is not None:
    df_calc = df_usuario.copy()
    
    # Garantir nomes padronizados sem espaços nas pontas
    df_calc.columns = df_calc.columns.str.strip()
    
    fretes_calculados = []
    custos_calculados = []
    
    for idx, row in df_calc.iterrows():
        # Suporta maiúsculo e minúsculo na busca
        destino = str(row["Cidade Destino"]).strip().upper()
        uf = str(row["UF"]).strip().upper()
        peso_real = float(row["Peso Real"])
        peso_cubado = float(row["Peso Cubado"])
        valor_merc = float(row["Valor Mercadoria"])
        
        peso_considerado = max(peso_real, peso_cubado)
        
        # --- Cálculo do Frete Padrão (Step III) ---
        match_frete = df_frete_padrao[
            (df_frete_padrao["cidade_destino"].str.upper() == destino) & 
            (df_frete_padrao["uf_destino"].str.upper() == uf)
        ]
        
        if not match_frete.empty:
            p_min = match_frete.iloc[0]["frete_peso_minimo"]
            p_exc = match_frete.iloc[0]["frete_excedente_por_kg"]
            # Excedente a partir de 100kg
            frete_peso = p_min + (max(0.0, peso_considerado - 100.0) * p_exc)
        else:
            # Fallback genérico caso a rota não esteja cadastrada no mock
            frete_peso = 150.0 + (peso_considerado * 1.5)
            
        # Aplicação da alçada de desconto comercial
        frete_com_desconto = frete_peso * (1 - (desconto_aplicado / 100.0))
        fretes_calculados.append(frete_com_desconto)
        
        # --- Atribuição de Custo Padrão/Rateio (Step IV) ---
        match_custo = df_custo_padrao[
            (df_custo_padrao["cidade_destino"].str.upper() == destino) & 
            (df_custo_padrao["uf_destino"].str.upper() == uf)
        ]
        
        if not match_custo.empty:
            c_fixo = match_custo.iloc[0]["custo_fixo_por_viagem"]
            c_var = match_custo.iloc[0]["custo_variavel_por_kg"]
            custo_total = c_fixo + (peso_real * c_var)
        else:
            # Fallback
            custo_total = 100.0 + (peso_real * 0.5)
            
        custos_calculados.append(custo_total)
        
    df_calc["Frete Simulado (R$)"] = fretes_calculados
    df_calc["Custo Rateado (R$)"] = custos_calculados
    df_calc["Margem Nominal (R$)"] = df_calc["Frete Simulado (R$)"] - df_calc["Custo Rateado (R$)"]
    df_calc["Margem (%)"] = (df_calc["Margem Nominal (R$)"] / df_calc["Frete Simulado (R$)"]) * 100.0

    # ==========================================
    # STEP V — DASHBOARD DE RESUMO (RESULTADOS)
    # ==========================================
    st.markdown("---")
    st.header("📊 Passo 5: Dashboard e Resumo da Simulação")
    
    # KPIs Gerais
    receita_total = df_calc["Frete Simulado (R$)"].sum()
    custo_total = df_calc["Custo Rateado (R$)"].sum()
    margem_nominal = receita_total - custo_total
    margem_percentual = (margem_nominal / receita_total) * 100 if receita_total > 0 else 0
    
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    
    with kpi1:
        st.markdown(f"""
        <div class="metric-card">
            <p style='color:#666; margin:0;'>Frete Total Simulado</p>
            <h2 style='margin:0; color:#002855;'>R$ {receita_total:,.2f}</h2>
        </div>
        """, unsafe_allow_html=True)
        
    with kpi2:
        st.markdown(f"""
        <div class="metric-card">
            <p style='color:#666; margin:0;'>Custo Operacional Total</p>
            <h2 style='margin:0; color:#002855;'>R$ {custo_total:,.2f}</h2>
        </div>
        """, unsafe_allow_html=True)
        
    with kpi3:
        st.markdown(f"""
        <div class="metric-card">
            <p style='color:#666; margin:0;'>Margem Nominal</p>
            <h2 style='margin:0; color:#002855;'>R$ {margem_nominal:,.2f}</h2>
        </div>
        """, unsafe_allow_html=True)
        
    with kpi4:
        cor_margem = "#28A745" if margem_percentual >= margem_alvo else "#DC3545"
        st.markdown(f"""
        <div class="metric-card" style='border-left: 5px solid {cor_margem};'>
            <p style='color:#666; margin:0;'>Margem Real (% vs Alvo)</p>
            <h2 style='margin:0; color:{cor_margem};'>{margem_percentual:.1f}%</h2>
            <small style='color:#666;'>Alvo: {margem_alvo}%</small>
        </div>
        """, unsafe_allow_html=True)

    # Gráfico de Desempenho por Rota
    st.subheader("📈 Margem de Contribuição por Rota (%)")
    
    df_rotas = df_calc.groupby("Cidade Destino").agg({
        "Frete Simulado (R$)": "sum",
        "Custo Rateado (R$)": "sum"
    }).reset_index()
    
    df_rotas["Margem (%)"] = ((df_rotas["Frete Simulado (R$)"] - df_rotas["Custo Rateado (R$)"]) / df_rotas["Frete Simulado (R$)"]) * 100.0
    
    # Customização do gráfico com as cores da Jamef
    fig = px.bar(
        df_rotas, 
        x="Cidade Destino", 
        y="Margem (%)",
        text="Margem (%)",
        color_discrete_sequence=["#002855"]
    )
    fig.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
    fig.add_hline(y=margem_alvo, line_dash="dash", line_color="#E30613", annotation_text="Margem Alvo")
    st.plotly_chart(fig, use_container_width=True)

    # Tabela Detalhada Pronta para Análise
    st.subheader("📋 Visão Consolidada dos Embarques")
    df_exibicao = df_calc[[
        "Cidade Destino", "UF", "Peso Real", "Valor Mercadoria", 
        "Frete Simulado (R$)", "Custo Rateado (R$)", "Margem Nominal (R$)", "Margem (%)"
    ]]
    st.dataframe(df_exibicao.style.format({
        "Peso Real": "{:,.1f} kg",
        "Valor Mercadoria": "R$ {:,.2f}",
        "Frete Simulado (R$)": "R$ {:,.2f}",
        "Custo Rateado (R$)": "R$ {:,.2f}",
        "Margem Nominal (R$)": "R$ {:,.2f}",
        "Margem (%)": "{:.2f}%"
    }), use_container_width=True)

else:
    st.info("💡 Por favor, arraste o arquivo padrão no Passo 2 ou clique em 'Usar Dados de Exemplo' para ver o simulador em ação!")
