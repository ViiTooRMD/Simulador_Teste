import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# 1. Configuração de Página
st.set_page_config(page_title="Simulador de Fretes Jamef", page_icon="🚛", layout="wide")

# 2. Inicialização do Estado (Sessão)
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False
if "tela_atual" not in st.session_state:
    st.session_state.tela_atual = "LOGIN"
if "usuario_nome" not in st.session_state:
    st.session_state.usuario_nome = ""

if "params" not in st.session_state:
    st.session_state.params = {"cidade_origem": "Curitiba", "sigla_origem": "CWB", "alcada": "Vendedor", "desconto": 0.0, "margem_alvo": 15.0}
if "df_usuario" not in st.session_state:
    st.session_state.df_usuario = None
if "df_calculado" not in st.session_state:
    st.session_state.df_calculado = None

# ==========================================
# 3. FUNÇÕES DE CARREGAMENTO (EXCEL E MOCK)
# ==========================================

@st.cache_data
def carregar_arquivos_referencia():
    try:
        # Carrega os arquivos Excel anexados no GitHub
        df_cidades = pd.read_excel("db_Cidades_Atendimento.xlsx")
        df_custo = pd.read_excel("db_Custo_Padrão.xlsx")
        
        # Padroniza as colunas (maiúsculas e sem espaços)
        df_cidades.columns = df_cidades.columns.str.strip().str.upper()
        df_custo.columns = df_custo.columns.str.strip().str.upper()
        
        return df_cidades, df_custo
    except Exception as e:
        return None, None

df_cidades_ref, df_custo_ref = carregar_arquivos_referencia()

# Dicionário fixo de Frete (Será substituído na próxima etapa pelo cálculo real de frete)
@st.cache_data
def carregar_frete_mock():
    frete_data = [
        {"cidade_origem": "CWB", "cidade_destino": "PALMAS", "uf_destino": "TO", "frete_peso_minimo": 350.0, "frete_excedente_por_kg": 3.2},
        {"cidade_origem": "CWB", "cidade_destino": "MACEIO", "uf_destino": "AL", "frete_peso_minimo": 420.0, "frete_excedente_por_kg": 4.1},
        {"cidade_origem": "CWB", "cidade_destino": "RIO LARGO", "uf_destino": "AL", "frete_peso_minimo": 400.0, "frete_excedente_por_kg": 3.9},
    ]
    return pd.DataFrame(frete_data)

df_frete_padrao = carregar_frete_mock()

# ==========================================
# 4. TELA DE LOGIN (CSS E HTML PRESERVADOS)
# ==========================================
if st.session_state.tela_atual == "LOGIN":
    st.markdown("""
        <style>
        [data-testid="collapsedControl"] {display: none !important;}
        [data-testid="stHeader"] {display: none !important;}
        div.block-container {padding: 0 !important; max-width: 100% !important;}
        div[data-testid="stHorizontalBlock"] {gap: 0px !important; margin: 0px !important; width: 100% !important;}
        
        :root {--jamef-red: #e30613; --jamef-red-dark: #b8000d; --jamef-black: #151515; --jamef-gray: #f4f5f7; --jamef-gray-2: #d9dde3; --white: #ffffff;}
        
        .brand-area {
          background: linear-gradient(135deg, rgba(227, 6, 19, 0.98), rgba(120, 0, 8, 0.95)), radial-gradient(circle at top left, rgba(255,255,255,0.18), transparent 35%);
          color: white; padding: 64px; display: flex; flex-direction: column; justify-content: center; height: 100vh; width: 100%; position: relative; overflow: hidden;
        }
        .brand-content {position: relative; max-width: 560px; z-index: 2;}
        .system-badge {display: inline-flex; align-items: center; gap: 10px; background: rgba(255, 255, 255, 0.14); border: 1px solid rgba(255, 255, 255, 0.22); border-radius: 999px; padding: 10px 16px; font-size: 13px; font-weight: 700; text-transform: uppercase; margin-bottom: 28px;}
        .system-badge span {width: 9px; height: 9px; background: white; border-radius: 50%; display: block;}
        .brand-content h1 {font-size: 48px; margin-bottom: 22px; color: white !important; font-weight: bold;}
        .brand-content p {font-size: 18px; color: rgba(255, 255, 255, 0.88) !important; margin-bottom: 36px;}
        
        .login-area-container {background: white; padding: 64px; height: 100vh; display: flex; flex-direction: column; justify-content: center; width: 100%;}
        .login-card-container {width: 100%; max-width: 430px; margin: 0 auto;}
        .login-card-container h2 {font-size: 28px; color: var(--jamef-black); font-weight: bold; margin-bottom: 8px;}
        
        div[data-testid="stForm"] {border: none !important; padding: 0 !important; background-color: transparent !important;}
        div.stButton > button:first-child {width: 100% !important; height: 54px !important; background: var(--jamef-red) !important; color: white !important; font-size: 16px !important; font-weight: 800 !important; border-radius: 14px !important; margin-top: 15px !important;}
        div.stButton > button:first-child:hover {background: var(--jamef-red-dark) !important;}
        </style>
    """, unsafe_allow_html=True)
    
    col_esquerda, col_direita = st.columns([1.1, 0.9])
    with col_esquerda:
        st.markdown("""<div class="brand-area"><div class="brand-content"><div class="system-badge"><span></span>Plataforma Comercial</div><h1>Simulador de Fretes Jamef</h1><p>Uma solução para apoiar decisões comerciais com agilidade, padronização e inteligência na formação de preços.</p></div></div>""", unsafe_allow_html=True)
        
    with col_direita:
        st.markdown("""<div class="login-area-container"><div class="login-card-container"><img src="https://www.jamef.com.br/wp-content/uploads/2021/04/Logo_Jamef.png" width="200" style="margin-bottom: 32px;"/><h2>Acesse sua conta</h2></div></div>""", unsafe_allow_html=True)
        with st.container():
            st.markdown("<div style='max-width: 430px; margin: -120px auto 0;'>", unsafe_allow_html=True)
            with st.form("login_form"):
                usuario = st.text_input("E-mail corporativo", placeholder="admin ou @jamef.com.br")
                senha = st.text_input("Senha", type="password")
                if st.form_submit_button("Entrar no simulador"):
                    if (usuario == "admin" and senha == "admin") or ("@jamef.com.br" in usuario and len(senha)>3):
                        st.session_state.autenticado = True
                        st.session_state.usuario_nome = "Admin" if usuario == "admin" else usuario.split("@")[0].title()
                        st.session_state.tela_atual = "PASSO_1"
                        st.rerun()
                    else:
                        st.error("Credenciais inválidas.")

# ==========================================
# 5. TELAS DO SIMULADOR (AUTENTICADO)
# ==========================================
elif st.session_state.autenticado:
    # CSS Interno
    st.markdown("""
        <style>
        .stApp {background-color: #F8F9FA;}
        h1, h2, h3 {color: #002855 !important; font-family: 'Helvetica Neue', sans-serif;}
        div.stButton > button:first-child {background-color: #E30613 !important; color: white !important; border-radius: 6px !important; border: none !important; font-weight: bold !important; padding: 0.6rem 1.8rem !important;}
        .metric-card {background-color: white; padding: 20px; border-radius: 8px; border-left: 5px solid #E30613; box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-bottom: 15px;}
        </style>
    """, unsafe_allow_html=True)

    # Header Topo
    col_h1, col_h2 = st.columns([8, 2])
    with col_h1: st.title("Simulador de Custos e Fretes — Jamef")
    with col_h2:
        st.write(f"👤 **{st.session_state.usuario_nome}**")
        if st.button("Sair/Logout"):
            st.session_state.autenticado = False
            st.session_state.tela_atual = "LOGIN"
            st.rerun()

    # Stepper
    passos = ["1. Parâmetros", "2. Importação", "3. Cálculo Frete", "4. Atribuição Custo", "5. Dashboard"]
    idx_atual = {"PASSO_1":0, "PASSO_2":1, "PASSO_3":2, "PASSO_4":3, "PASSO_5":4}.get(st.session_state.tela_atual, 0)
    cols_stepper = st.columns(5)
    for idx, nome in enumerate(passos):
        with cols_stepper[idx]:
            if idx == idx_atual: st.markdown(f"<p style='text-align: center; border-bottom: 4px solid #E30613; font-weight: bold; color: #002855;'>{nome}</p>", unsafe_allow_html=True)
            elif idx < idx_atual: st.markdown(f"<p style='text-align: center; border-bottom: 4px solid #28A745; color: #666;'>✓ {nome}</p>", unsafe_allow_html=True)
            else: st.markdown(f"<p style='text-align: center; border-bottom: 4px solid #CCC; color: #999;'>{nome}</p>", unsafe_allow_html=True)
    st.write("---")

    # --- PASSO 1: PARÂMETROS ---
    if st.session_state.tela_atual == "PASSO_1":
        st.subheader("⚙️ Configuração Geral da Simulação")
        
        # Dicionário para de-para da filial de origem
        origens_dict = {"Curitiba": "CWB", "São Paulo": "SPO", "Belo Horizonte": "BHZ"}
        
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            cidade_sel = st.selectbox("Cidade de Origem", list(origens_dict.keys()), index=list(origens_dict.keys()).index(st.session_state.params["cidade_origem"]))
            sigla_sel = origens_dict[cidade_sel]
            st.text_input("Sigla da Filial Origem", value=sigla_sel, disabled=True)
        with col_p2:
            alcada_sel = st.selectbox("Alçada", ["Vendedor", "Gerente Regional", "Diretor/Pricing"], index=["Vendedor", "Gerente Regional", "Diretor/Pricing"].index(st.session_state.params["alcada"]))
            desc_limite = 5.0 if alcada_sel == "Vendedor" else (15.0 if alcada_sel == "Gerente Regional" else 100.0)
            desc_sel = st.slider("Desconto Comercial (%)", 0.0, float(desc_limite), float(st.session_state.params["desconto"]))
            margem_sel = st.number_input("Margem Alvo (%)", 1.0, 100.0, float(st.session_state.params["margem_alvo"]))

        if st.button("Avançar para Importação ➔"):
            st.session_state.params = {"cidade_origem": cidade_sel, "sigla_origem": sigla_sel, "alcada": alcada_sel, "desconto": desc_sel, "margem_alvo": margem_sel}
            st.session_state.tela_atual = "PASSO_2"
            st.rerun()

    # --- PASSO 2: IMPORTAÇÃO ---
    elif st.session_state.tela_atual == "PASSO_2":
        st.subheader("📥 Upload do Histórico")
        col_up1, col_p2 = st.columns([2, 1])
        with col_up1: uploaded_file = st.file_uploader("Arquivo de simulação (.csv ou .xlsx)", type=["csv", "xlsx"])
        with col_p2: 
            st.write("<br>", unsafe_allow_html=True)
            usar_mock = st.button("💡 Usar Dados de Exemplo")

        if usar_mock:
            st.session_state.df_usuario = pd.DataFrame({
                "Cidade Destino": ["PALMAS", "MACEIO", "RIO LARGO"], "UF": ["TO", "AL", "AL"],
                "Peso Real": [84.00, 234.00, 93.00], "Peso Cubado": [193.08, 459.03, 202.44], "Volume": [2, 4, 2],
                "Valor Mercadoria": [9178.41, 17853.74, 9620.00]
            })
            st.success("✓ Dados carregados!")
        elif uploaded_file:
            st.session_state.df_usuario = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
            st.success("✓ Arquivo validado!")

        if st.session_state.df_usuario is not None: st.dataframe(st.session_state.df_usuario.head(3))

        col_nav1, col_nav2 = st.columns(2)
        with col_nav1:
            if st.button("⬅ Voltar"): st.session_state.tela_atual = "PASSO_1"; st.rerun()
        with col_nav2:
            if st.button("Calcular Frete ➔", disabled=st.session_state.df_usuario is None): st.session_state.tela_atual = "PASSO_3"; st.rerun()

    # --- PASSO 3: FRETE MOCK ---
    elif st.session_state.tela_atual == "PASSO_3":
        st.subheader("🧮 Processamento de Frete (Mock)")
        st.info("O cálculo oficial do frete comercial será inserido na próxima etapa. Estamos usando uma estimativa genérica.")
        
        df_calc = st.session_state.df_usuario.copy()
        df_calc.columns = df_calc.columns.str.strip().str.upper()
        
        fretes = []
        for idx, row in df_calc.iterrows():
            peso = max(float(row.get("PESO REAL", 0)), float(row.get("PESO CUBADO", 0)))
            frete_bruto = 150.0 + (peso * 1.5) # Simulação Genérica
            fretes.append(frete_bruto * (1 - (st.session_state.params["desconto"] / 100.0)))
            
        df_calc["FRETE_SIMULADO"] = fretes
        st.session_state.df_calculado = df_calc
        st.dataframe(df_calc[["CIDADE DESTINO", "UF", "PESO REAL", "VALOR MERCADORIA", "FRETE_SIMULADO"]])

        col_nav1, col_nav2 = st.columns(2)
        with col_nav1:
            if st.button("⬅ Voltar"): st.session_state.tela_atual = "PASSO_2"; st.rerun()
        with col_nav2:
            if st.button("Atribuir Custos Reais ➔"): st.session_state.tela_atual = "PASSO_4"; st.rerun()

    # --- PASSO 4: CUSTO REAL JAMEF ---
    elif st.session_state.tela_atual == "PASSO_4":
        st.subheader("🚛 Atribuição Inteligente de Custos")
        
        if df_cidades_ref is None or df_custo_ref is None:
            st.error("⚠️ Os arquivos 'db_Cidades_Atendimento.xlsx' e 'db_Custo_Padrão.xlsx' não foram encontrados no GitHub!")
            st.stop()

        with st.spinner("Analisando Filiais de Atendimento e Tipo de Região (Capital/Interior)..."):
            df_calc = st.session_state.df_calculado.copy()
            
            # 1. Encontra a Filial de Destino e Região
            df_enriquecido = pd.merge(df_calc, df_cidades_ref[['CIDADE', 'UF', 'FILIAL_ATENDIMENTO', 'TIPO_REGIAO']],
                                      left_on=['CIDADE DESTINO', 'UF'], right_on=['CIDADE', 'UF'], how='left')

            # 2. Cria a Rota de Custo (Origem - Destino)
            origem = st.session_state.params["sigla_origem"]
            df_enriquecido['COD_ROTA'] = origem + '-' + df_enriquecido['FILIAL_ATENDIMENTO']
            
            # 3. Busca os Custos da Rota
            df_final_custo = pd.merge(df_enriquecido, df_custo_ref, on='COD_ROTA', how='left')

            # 4. Cálculo da Lógica Jamef (PM, Capital x Interior)
            custos_totais = []
            
            for idx, row in df_final_custo.iterrows():
                if pd.isna(row['PM']): 
                    custos_totais.append(0.0) # Caso a rota não exista
                    continue

                peso_real = float(row['PESO REAL'])
                valor_merc = float(row['VALOR MERCADORIA'])
                regiao = str(row['TIPO_REGIAO']).strip().upper()
                pm = float(row['PM'])
                
                # Validação do Peso Mínimo
                peso_calculo = max(peso_real, pm)
                
                # Regras de Região
                if regiao == 'CAPITAL':
                    custo_kg = float(row['CUSTO_KG_CAP'])
                    perc_nf = float(row['PERC_NF_CAP'])
                else: # INTERIOR
                    custo_kg = float(row['CUSTO_KG_INT'])
                    perc_nf = float(row['PERC_NF_INT'])
                
                # Matemática Financeira (Assumindo que perc_nf no excel está como 0.15 para 0.15%)
                custo_fixo = peso_calculo * custo_kg
                custo_var = valor_merc * (perc_nf / 100.0) 
                
                custos_totais.append(custo_fixo + custo_var)

            df_final_custo['CUSTO_TOTAL'] = custos_totais
            st.session_state.df_calculado = df_final_custo
            
            st.dataframe(df_final_custo[['CIDADE DESTINO', 'UF', 'FILIAL_ATENDIMENTO', 'TIPO_REGIAO', 'PESO REAL', 'FRETE_SIMULADO', 'CUSTO_TOTAL']].style.format({
                "PESO REAL": "{:,.1f} kg", "FRETE_SIMULADO": "R$ {:,.2f}", "CUSTO_TOTAL": "R$ {:,.2f}"
            }))

        col_nav1, col_nav2 = st.columns(2)
        with col_nav1:
            if st.button("⬅ Voltar"): st.session_state.tela_atual = "PASSO_3"; st.rerun()
        with col_nav2:
            if st.button("Gerar Dashboard ➔"): st.session_state.tela_atual = "PASSO_5"; st.rerun()

    # --- PASSO 5: DASHBOARD ---
    elif st.session_state.tela_atual == "PASSO_5":
        st.subheader("📊 Dashboard Final da Simulação")
        
        df_final = st.session_state.df_calculado
        
        receita = df_final["FRETE_SIMULADO"].sum()
        custo = df_final["CUSTO_TOTAL"].sum()
        margem = receita - custo
        perc = (margem / receita) * 100 if receita > 0 else 0
        alvo = st.session_state.params["margem_alvo"]
        
        k1, k2, k3, k4 = st.columns(4)
        k1.markdown(f"<div class='metric-card'>Frete Bruto<h2 style='color:#002855;'>R$ {receita:,.2f}</h2></div>", unsafe_allow_html=True)
        k2.markdown(f"<div class='metric-card'>Custo Total<h2 style='color:#002855;'>R$ {custo:,.2f}</h2></div>", unsafe_allow_html=True)
        k3.markdown(f"<div class='metric-card'>Margem Nominal<h2 style='color:#002855;'>R$ {margem:,.2f}</h2></div>", unsafe_allow_html=True)
        cor = "#28A745" if perc >= alvo else "#DC3545"
        k4.markdown(f"<div class='metric-card' style='border-left: 5px solid {cor};'>Margem %<h2 style='color:{cor};'>{perc:.1f}%</h2></div>", unsafe_allow_html=True)

        if st.button("🔄 Iniciar Nova Simulação"):
            st.session_state.df_usuario = None
            st.session_state.tela_atual = "PASSO_1"
            st.rerun()
