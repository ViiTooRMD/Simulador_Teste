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

# Estilização CSS Jamef
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
        padding: 0.6rem 1.8rem !important;
        transition: all 0.3s ease;
    }
    div.stButton > button:first-child:hover {
        background-color: #002855 !important;
        color: white !important;
    }
    /* Botão Secundário (Voltar) */
    div.stButton > button.secondary-btn {
        background-color: #6C757D !important;
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
    /* Caixa de Login */
    .login-box {
        background-color: white;
        padding: 40px;
        border-radius: 10px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.1);
        max-width: 450px;
        margin: auto;
        border-top: 5px solid #E30613;
    }
    </style>
""", unsafe_allow_html=True)

# 2. Inicialização das Variáveis de Estado (Memória da Sessão)
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False
if "tela_atual" not in st.session_state:
    st.session_state.tela_atual = "LOGIN"
if "usuario_nome" not in st.session_state:
    st.session_state.usuario_nome = ""

# Memória dos dados inseridos pelo usuário ao longo das etapas
if "params" not in st.session_state:
    st.session_state.params = {
        "cidade_origem": "Curitiba",
        "alcada": "Vendedor",
        "desconto": 0.0,
        "margem_alvo": 15.0
    }
if "df_usuario" not in st.session_state:
    st.session_state.df_usuario = None

# 3. Tabelas de Apoio Embarcadas
@st.cache_data
def carregar_tabelas_padrao():
    frete_data = [
        {"cidade_origem": "Curitiba", "cidade_destino": "SÃO PAULO", "uf_destino": "SP", "frete_peso_minimo": 150.0, "frete_excedente_por_kg": 1.2},
        {"cidade_origem": "Curitiba", "cidade_destino": "CAMPINAS", "uf_destino": "SP", "frete_peso_minimo": 180.0, "frete_excedente_por_kg": 1.5},
        {"cidade_origem": "Curitiba", "cidade_destino": "BELO HORIZONTE", "uf_destino": "MG", "frete_peso_minimo": 220.0, "frete_excedente_por_kg": 1.8},
        {"cidade_origem": "Curitiba", "cidade_destino": "RIO DE JANEIRO", "uf_destino": "RJ", "frete_peso_minimo": 250.0, "frete_excedente_por_kg": 2.0},
        {"cidade_origem": "Curitiba", "cidade_destino": "PALMAS", "uf_destino": "TO", "frete_peso_minimo": 350.0, "frete_excedente_por_kg": 3.2},
        {"cidade_origem": "Curitiba", "cidade_destino": "MACEIO", "uf_destino": "AL", "frete_peso_minimo": 420.0, "frete_excedente_por_kg": 4.1},
        {"cidade_origem": "Curitiba", "cidade_destino": "RIO LARGO", "uf_destino": "AL", "frete_peso_minimo": 400.0, "frete_excedente_por_kg": 3.9},
    ]
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

# ==========================================
# GESTÃO DE TELAS (FLOW CONTROLLER)
# ==========================================

# --- TELA DE LOGIN ---
if st.session_state.tela_atual == "LOGIN":
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    # Caixa centralizada de login
    col_l1, col_l2, col_l3 = st.columns([1, 2, 1])
    with col_l2:
        st.markdown("<h1 style='text-align: center;'>🚛 Portal de Precificação</h1>", unsafe_allow_html=True)
        st.write(" ")
        
        with st.form("login_form"):
            st.subheader("Entrar na sua conta Jamef")
            usuario = st.text_input("Usuário (e-mail corporativo)", placeholder="ex: vitor.dutra@jamef.com.br")
            senha = st.text_input("Senha", type="password", placeholder="••••••••")
            
            botao_entrar = st.form_submit_button("Acessar Simulador")
            
            if botao_entrar:
                # Validação simples para o MVP (Aceita qualquer usuário Jamef para testes)
                if "@jamef.com.br" in usuario and len(senha) >= 4:
                    st.session_state.autenticado = True
                    st.session_state.usuario_nome = usuario.split("@")[0].title()
                    st.session_state.tela_atual = "PASSO_1"
                    st.rerun()
                else:
                    st.error("Credenciais inválidas. Use um e-mail @jamef.com.br e senha com mais de 4 caracteres.")

# --- SE ESTIVER AUTENTICADO, MOSTRA O MENU E AS PÁGINAS ---
if st.session_state.autenticado:
    
    # Header unificado pós-login
    col_h1, col_h2 = st.columns([8, 2])
    with col_h1:
        st.title("Simulador de Custos e Fretes — Jamef")
    with col_h2:
        st.write(" ")
        st.write(f"👤 Olá, **{st.session_state.usuario_nome}**")
        if st.button("Sair/Logout"):
            st.session_state.autenticado = False
            st.session_state.tela_atual = "LOGIN"
            st.session_state.df_usuario = None
            st.rerun()
            
    # Stepper Visual (Barra de Progresso do Fluxo)
    passos = ["1. Parâmetros", "2. Importação", "3. Cálculo Frete", "4. Atribuição Custo", "5. Dashboard"]
    passo_map = {"PASSO_1": 0, "PASSO_2": 1, "PASSO_3": 2, "PASSO_4": 3, "PASSO_5": 4}
    idx_atual = passo_map.get(st.session_state.tela_atual, 0)
    
    # Renderiza o indicador visual das páginas no topo
    cols_stepper = st.columns(5)
    for idx, nome_passo in enumerate(passos):
        with cols_stepper[idx]:
            if idx == idx_atual:
                st.markdown(f"<p style='text-align: center; border-bottom: 4px solid #E30613; font-weight: bold; color: #002855;'>{nome_passo}</p>", unsafe_allow_html=True)
            elif idx < idx_atual:
                st.markdown(f"<p style='text-align: center; border-bottom: 4px solid #28A745; color: #666;'>✓ {nome_passo}</p>", unsafe_allow_html=True)
            else:
                st.markdown(f"<p style='text-align: center; border-bottom: 4px solid #CCC; color: #999;'>{nome_passo}</p>", unsafe_allow_html=True)
                
    st.markdown("<br>", unsafe_allow_html=True)

    # ------------------------------------------
    # TELA 1 — PARÂMETROS
    # ------------------------------------------
    if st.session_state.tela_atual == "PASSO_1":
        st.subheader("⚙️ Configuração Geral da Simulação")
        st.write("Insira as premissas comerciais que servirão de base para analisar a carteira de embarques.")
        
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            cidade_orig_sel = st.selectbox("Cidade de Origem", ["Curitiba", "São Paulo", "Belo Horizonte"])
            st.text_input("Filial Responsável", value=f"Filial {cidade_orig_sel}", disabled=True)
            st.text_input("Sigla da Filial", value="CWB" if cidade_orig_sel == "Curitiba" else "SPO", disabled=True)
            
        with col_p2:
            alcada_sel = st.selectbox(
                "Nível de Alçada do Simulador", 
                ["Vendedor", "Gerente Regional", "Diretor/Pricing"],
                index=["Vendedor", "Gerente Regional", "Diretor/Pricing"].index(st.session_state.params["alcada"])
            )
            
            # Limite dinâmico do desconto baseado no cargo do login
            desconto_limite = 5.0 if alcada_sel == "Vendedor" else (15.0 if alcada_sel == "Gerente Regional" else 100.0)
            
            desconto_sel = st.slider(
                "Desconto Comercial a ser Aplicado (%)", 
                min_value=0.0, 
                max_value=float(desconto_limite), 
                value=float(st.session_state.params["desconto"]),
                step=0.5
            )
            margem_sel = st.number_input("Margem de Contribuição Alvo (%)", min_value=1.0, max_value=100.0, value=float(st.session_state.params["margem_alvo"]))

        # Salva no estado
        st.session_state.params = {
            "cidade_origem": cidade_orig_sel,
            "alcada": alcada_sel,
            "desconto": desconto_sel,
            "margem_alvo": margem_sel
        }
        
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Avançar para Importação ➔"):
            st.session_state.tela_atual = "PASSO_2"
            st.rerun()

    # ------------------------------------------
    # TELA 2 — IMPORTAÇÃO DE DADOS
    # ------------------------------------------
    elif st.session_state.tela_atual == "PASSO_2":
        st.subheader("📥 Upload do Histórico de Embarques")
        st.write("Insira o arquivo com os embarques que deseja cotar e calcular margem.")
        
        col_up1, col_p2 = st.columns([2, 1])
        with col_up1:
            uploaded_file = st.file_uploader(
                "Selecione o arquivo de simulação (.csv ou .xlsx)", 
                type=["csv", "xlsx"]
            )
        with col_p2:
            st.write("<br>", unsafe_allow_html=True)
            usar_mock = st.button("💡 Usar Dados de Exemplo (Testar sem arquivo)")

        if usar_mock:
            # Mock dos dados do seu print
            dados_mock = {
                "Cidade Destino": ["PALMAS", "MACEIO", "RIO LARGO"],
                "UF": ["TO", "AL", "AL"],
                "Peso Real": [84.00, 234.00, 93.00],
                "Peso Cubado": [193.08, 459.03, 202.44],
                "Volume": [2, 4, 2],
                "Data Movimento": ["21/10/2025", "23/10/2025", "31/10/2025"],
                "CNPJ_Destinatario": ["06057223037504", "06057223037504", "06057223037504"],
                "Valor Mercadoria": [9178.41, 17853.74, 9620.00]
            }
            st.session_state.df_usuario = pd.DataFrame(dados_mock)
            st.success("✓ Dados de exemplo carregados!")
            
        elif uploaded_file is not None:
            try:
                if uploaded_file.name.endswith('.csv'):
                    st.session_state.df_usuario = pd.read_csv(uploaded_file, sep=None, engine='python')
                else:
                    st.session_state.df_usuario = pd.read_excel(uploaded_file)
                st.success("✓ Arquivo carregado e validado!")
            except Exception as e:
                st.error(f"Erro ao ler arquivo: {e}")

        # Mostrar preview do arquivo carregado
        if st.session_state.df_usuario is not None:
            st.markdown("##### Preview do Arquivo Carregado")
            st.dataframe(st.session_state.df_usuario.head(5), use_container_width=True)

        # Navegação
        st.markdown("<br>", unsafe_allow_html=True)
        col_nav1, col_nav2 = st.columns([1, 1])
        with col_nav1:
            if st.button("⬅ Voltar para Parâmetros"):
                st.session_state.tela_atual = "PASSO_1"
                st.rerun()
        with col_nav2:
            # Só deixa avançar se tiver dados
            desativado = st.session_state.df_usuario is None
            if st.button("Calcular Frete Padrão ➔", disabled=desativado):
                st.session_state.tela_atual = "PASSO_3"
                st.rerun()

    # ------------------------------------------
    # TELA 3 — CÁLCULO DE FRETE
    # ------------------------------------------
    elif st.session_state.tela_atual == "PASSO_3":
        st.subheader("🧮 Processamento do Frete Comercial")
        st.write(f"Cálculo realizado aplicando **desconto de {st.session_state.params['desconto']}%** (Alçada: {st.session_state.params['alcada']})")
        
        # Realiza os cálculos de frete baseados nas premissas
        df_calc = st.session_state.df_usuario.copy()
        df_calc.columns = df_calc.columns.str.strip()
        
        fretes_calculados = []
        for idx, row in df_calc.iterrows():
            destino = str(row["Cidade Destino"]).strip().upper()
            uf = str(row["UF"]).strip().upper()
            peso_real = float(row["Peso Real"])
            peso_cubado = float(row["Peso Cubado"])
            
            peso_considerado = max(peso_real, peso_cubado)
            
            match_frete = df_frete_padrao[
                (df_frete_padrao["cidade_destino"].str.upper() == destino) & 
                (df_frete_padrao["uf_destino"].str.upper() == uf)
            ]
            
            if not match_frete.empty:
                p_min = match_frete.iloc[0]["frete_peso_minimo"]
                p_exc = match_frete.iloc[0]["frete_excedente_por_kg"]
                frete_peso = p_min + (max(0.0, peso_considerado - 100.0) * p_exc)
            else:
                frete_peso = 150.0 + (peso_considerado * 1.5)
                
            frete_com_desconto = frete_peso * (1 - (st.session_state.params["desconto"] / 100.0))
            fretes_calculados.append(frete_com_desconto)
            
        df_calc["Frete Calculado (R$)"] = fretes_calculados
        st.session_state.df_calculado = df_calc # Salva cálculo de frete
        
        st.dataframe(df_calc[["Cidade Destino", "UF", "Peso Real", "Peso Cubado", "Valor Mercadoria", "Frete Calculado (R$)"]].style.format({
            "Peso Real": "{:,.2f} kg",
            "Peso Cubado": "{:,.2f} kg",
            "Valor Mercadoria": "R$ {:,.2f}",
            "Frete Calculado (R$)": "R$ {:,.2f}"
        }), use_container_width=True)

        # Navegação
        st.markdown("<br>", unsafe_allow_html=True)
        col_nav1, col_nav2 = st.columns(2)
        with col_nav1:
            if st.button("⬅ Voltar para Importação"):
                st.session_state.tela_atual = "PASSO_2"
                st.rerun()
        with col_nav2:
            if st.button("Aplicar Custos da Operação ➔"):
                st.session_state.tela_atual = "PASSO_4"
                st.rerun()

    # ------------------------------------------
    # TELA 4 — ATRIBUIÇÃO DE CUSTO
    # ------------------------------------------
    elif st.session_state.tela_atual == "PASSO_4":
        st.subheader("🚛 Cruzamento com Tabela de Custo e Rateio")
        st.write("Nesta etapa o sistema aplica o de-para de custos por rota (Coleta, Transferência e Entrega).")
        
        df_calc = st.session_state.df_calculado.copy()
        custos_calculados = []
        
        for idx, row in df_calc.iterrows():
            destino = str(row["Cidade Destino"]).strip().upper()
            uf = str(row["UF"]).strip().upper()
            peso_real = float(row["Peso Real"])
            
            match_custo = df_custo_padrao[
                (df_custo_padrao["cidade_destino"].str.upper() == destino) & 
                (df_custo_padrao["uf_destino"].str.upper() == uf)
            ]
            
            if not match_custo.empty:
                c_fixo = match_custo.iloc[0]["custo_fixo_por_viagem"]
                c_var = match_custo.iloc[0]["custo_variavel_por_kg"]
                custo_total = c_fixo + (peso_real * c_var)
            else:
                custo_total = 100.0 + (peso_real * 0.5)
                
            custos_calculados.append(custo_total)
            
        df_calc["Custo Total (R$)"] = custos_calculados
        st.session_state.df_calculado = df_calc # Atualiza dados com o custo
        
        st.dataframe(df_calc[["Cidade Destino", "UF", "Peso Real", "Frete Calculado (R$)", "Custo Total (R$)"]].style.format({
            "Peso Real": "{:,.2f} kg",
            "Frete Calculado (R$)": "R$ {:,.2f}",
            "Custo Total (R$)": "R$ {:,.2f}"
        }), use_container_width=True)

        # Navegação
        st.markdown("<br>", unsafe_allow_html=True)
        col_nav1, col_nav2 = st.columns(2)
        with col_nav1:
            if st.button("⬅ Voltar para Frete"):
                st.session_state.tela_atual = "PASSO_3"
                st.rerun()
        with col_nav2:
            if st.button("Gerar Painel de Resultados ➔"):
                st.session_state.tela_atual = "PASSO_5"
                st.rerun()

    # ------------------------------------------
    # TELA 5 — DASHBOARD FINAL
    # ------------------------------------------
    elif st.session_state.tela_atual == "PASSO_5":
        st.subheader("📊 Dashboard de Margem da Simulação")
        
        df_final = st.session_state.df_calculado.copy()
        
        # Consolidação Financeira
        receita_total = df_final["Frete Calculado (R$)"].sum()
        custo_total = df_final["Custo Total (R$)"].sum()
        margem_nominal = receita_total - custo_total
        margem_percentual = (margem_nominal / receita_total) * 100 if receita_total > 0 else 0
        margem_alvo = st.session_state.params["margem_alvo"]
        
        k1, k2, k3, k4 = st.columns(4)
        with k1:
            st.markdown(f"<div class='metric-card'><p style='color:#666; margin:0;'>Frete Cobrado</p><h2 style='margin:0; color:#002855;'>R$ {receita_total:,.2f}</h2></div>", unsafe_allow_html=True)
        with k2:
            st.markdown(f"<div class='metric-card'><p style='color:#666; margin:0;'>Custo Total</p><h2 style='margin:0; color:#002855;'>R$ {custo_total:,.2f}</h2></div>", unsafe_allow_html=True)
        with k3:
            st.markdown(f"<div class='metric-card'><p style='color:#666; margin:0;'>Margem Nominal</p><h2 style='margin:0; color:#002855;'>R$ {margem_nominal:,.2f}</h2></div>", unsafe_allow_html=True)
        with k4:
            cor = "#28A745" if margem_percentual >= margem_alvo else "#DC3545"
            st.markdown(f"<div class='metric-card' style='border-left: 5px solid {cor};'><p style='color:#666; margin:0;'>Margem Real (% vs Alvo)</p><h2 style='margin:0; color:{cor};'>{margem_percentual:.1f}%</h2><small>Alvo: {margem_alvo}%</small></div>", unsafe_allow_html=True)

        # Gráfico por Rota
        df_rotas = df_final.groupby("Cidade Destino").agg({
            "Frete Calculado (R$)": "sum",
            "Custo Total (R$)": "sum"
        }).reset_index()
        df_rotas["Margem (%)"] = ((df_rotas["Frete Calculado (R$)"] - df_rotas["Custo Total (R$)"]) / df_rotas["Frete Calculado (R$)"]) * 100.0
        
        fig = px.bar(df_rotas, x="Cidade Destino", y="Margem (%)", text="Margem (%)", color_discrete_sequence=["#002855"])
        fig.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
        fig.add_hline(y=margem_alvo, line_dash="dash", line_color="#E30613", annotation_text="Margem Alvo")
        st.plotly_chart(fig, use_container_width=True)

        # Tabela
        st.subheader("📋 Visão Consolidada")
        st.dataframe(df_final.style.format({
            "Peso Real": "{:,.1f} kg",
            "Valor Mercadoria": "R$ {:,.2f}",
            "Frete Calculado (R$)": "R$ {:,.2f}",
            "Custo Total (R$)": "R$ {:,.2f}"
        }), use_container_width=True)

        # Navegação
        st.markdown("<br>", unsafe_allow_html=True)
        col_nav1, col_nav2 = st.columns(2)
        with col_nav1:
            if st.button("⬅ Voltar para Custos"):
                st.session_state.tela_atual = "PASSO_4"
                st.rerun()
        with col_nav2:
            if st.button("🔄 Nova Simulação"):
                st.session_state.df_usuario = None
                st.session_state.tela_atual = "PASSO_1"
                st.rerun()

