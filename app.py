import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# 1. Configuração de Página Jamef
st.set_page_config(
    page_title="Simulador de Fretes Jamef",
    page_icon="🚛",
    layout="wide",
)

# 2. Inicialização das Variáveis de Estado (Memória da Sessão)
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False
if "tela_atual" not in st.session_state:
    st.session_state.tela_atual = "LOGIN"
if "usuario_nome" not in st.session_state:
    st.session_state.usuario_nome = ""

# Memória das premissas comerciais
if "params" not in st.session_state:
    st.session_state.params = {
        "cidade_origem": "Curitiba",
        "alcada": "Vendedor",
        "desconto": 0.0,
        "margem_alvo": 15.0
    }
if "df_usuario" not in st.session_state:
    st.session_state.df_usuario = None

# ==========================================
# 3. ESTILIZAÇÃO E IDENTIDADE VISUAL JAMEF
# ==========================================

# Se for tela de LOGIN, aplicamos o layout de tela cheia e o estilo customizado enviado
if st.session_state.tela_atual == "LOGIN":
    st.markdown("""
        <style>
        /* Oculta componentes padrão do Streamlit na tela de Login */
        [data-testid="collapsedControl"] {display: none !important;}
        [data-testid="stHeader"] {display: none !important;}
        footer {visibility: hidden !important;}
        #MainMenu {visibility: hidden !important;}
        
        /* Remove paddings e margens para expandir em tela cheia */
        div.block-container {
            padding-top: 0rem !important;
            padding-bottom: 0rem !important;
            padding-left: 0rem !important;
            padding-right: 0rem !important;
            max-width: 100% !important;
        }
        div[data-testid="stHorizontalBlock"] {
            gap: 0px !important;
            margin: 0px !important;
            padding: 0px !important;
            width: 100% !important;
        }
        div[data-testid="column"] {
            padding: 0px !important;
            margin: 0px !important;
        }
        .stApp {
            background-color: #f4f5f7;
        }
        
        /* Estilo Customizado Baseado no seu HTML */
        :root {
          --jamef-red: #e30613;
          --jamef-red-dark: #b8000d;
          --jamef-black: #151515;
          --jamef-gray: #f4f5f7;
          --jamef-gray-2: #d9dde3;
          --white: #ffffff;
        }
        
        /* Lado Esquerdo - Brand Panel */
        .brand-area {
          position: relative;
          background:
            linear-gradient(135deg, rgba(227, 6, 19, 0.98), rgba(120, 0, 8, 0.95)),
            radial-gradient(circle at top left, rgba(255,255,255,0.18), transparent 35%);
          color: var(--white);
          padding: 64px;
          display: flex;
          flex-direction: column;
          justify-content: center;
          overflow: hidden;
          height: 100vh;
          width: 100%;
        }
        .brand-area::before,
        .brand-area::after {
          content: "";
          position: absolute;
          border: 1px solid rgba(255, 255, 255, 0.16);
          border-radius: 50%;
          width: 520px;
          height: 520px;
          right: -160px;
          top: -120px;
        }
        .brand-area::after {
          width: 360px;
          height: 360px;
          right: 80px;
          top: 280px;
          border-color: rgba(255, 255, 255, 0.10);
        }
        .route-lines {
          position: absolute;
          inset: 0;
          opacity: 0.18;
          background-image:
            linear-gradient(120deg, transparent 0%, transparent 42%, rgba(255,255,255,0.6) 43%, transparent 44%),
            linear-gradient(35deg, transparent 0%, transparent 50%, rgba(255,255,255,0.45) 51%, transparent 52%);
          background-size: 180px 180px;
        }
        .brand-content {
          position: relative;
          max-width: 560px;
          z-index: 2;
        }
        .system-badge {
          display: inline-flex;
          align-items: center;
          gap: 10px;
          background: rgba(255, 255, 255, 0.14);
          border: 1px solid rgba(255, 255, 255, 0.22);
          border-radius: 999px;
          padding: 10px 16px;
          font-size: 13px;
          font-weight: 700;
          letter-spacing: 0.4px;
          text-transform: uppercase;
          margin-bottom: 28px;
        }
        .system-badge span {
          width: 9px;
          height: 9px;
          background: var(--white);
          border-radius: 50%;
          display: block;
        }
        .brand-content h1 {
          font-size: 48px;
          line-height: 1.05;
          margin-bottom: 22px;
          letter-spacing: -1.5px;
          color: white !important;
          font-weight: bold;
        }
        .brand-content p {
          font-size: 18px;
          line-height: 1.55;
          color: rgba(255, 255, 255, 0.88) !important;
          max-width: 500px;
          margin-bottom: 36px;
        }
        .info-grid {
          display: grid;
          grid-template-columns: repeat(3, 1fr);
          gap: 14px;
          max-width: 560px;
        }
        .info-card {
          background: rgba(255, 255, 255, 0.13);
          border: 1px solid rgba(255, 255, 255, 0.18);
          border-radius: 18px;
          padding: 18px;
          backdrop-filter: blur(6px);
        }
        .info-card strong {
          display: block;
          font-size: 18px;
          margin-bottom: 6px;
          color: white !important;
        }
        .info-card small {
          font-size: 12px;
          color: rgba(255, 255, 255, 0.82) !important;
        }
        
        /* Lado Direito - Painel de Login */
        .login-area-container {
          background: var(--white);
          padding: 64px;
          height: 100vh;
          display: flex;
          flex-direction: column;
          justify-content: center;
          width: 100%;
        }
        .login-card-container {
          width: 100%;
          max-width: 430px;
          margin: 0 auto;
        }
        .logo-img {
          width: 200px;
          margin-bottom: 32px;
        }
        .login-card-container h2 {
          font-size: 28px;
          color: var(--jamef-black);
          margin-bottom: 8px;
          letter-spacing: -0.5px;
          font-weight: bold;
        }
        .login-card-container .subtitle {
          color: #6b7280;
          font-size: 14px;
          margin-bottom: 28px;
          line-height: 1.5;
        }
        
        /* Sobrescrita de inputs nativos do Streamlit */
        div[data-testid="stForm"] {
            border: none !important;
            padding: 0 !important;
            background-color: transparent !important;
        }
        div[data-baseweb="input"] {
            border-radius: 12px !important;
            background: #fbfbfc !important;
            border: 1px solid var(--jamef-gray-2) !important;
            height: 52px !important;
            font-size: 15px !important;
            transition: 0.2s ease !important;
        }
        div[data-baseweb="input"]:focus-within {
            border-color: var(--jamef-red) !important;
            box-shadow: 0 0 0 4px rgba(227, 6, 19, 0.10) !important;
            background: var(--white) !important;
        }
        input[type="text"], input[type="password"] {
            background-color: transparent !important;
            color: #333 !important;
        }
        div[data-testid="stWidgetLabel"] p {
            font-size: 13px !important;
            font-weight: 700 !important;
            color: #333 !important;
            margin-bottom: 8px !important;
        }
        
        /* Botão Vermelho de Login */
        div.stButton > button:first-child {
          width: 100% !important;
          height: 54px !important;
          border: none !important;
          border-radius: 14px !important;
          background: var(--jamef-red) !important;
          color: var(--white) !important;
          font-size: 16px !important;
          font-weight: 800 !important;
          cursor: pointer !important;
          transition: 0.2s ease !important;
          box-shadow: 0 14px 28px rgba(227, 6, 19, 0.24) !important;
          margin-top: 15px !important;
        }
        div.stButton > button:first-child:hover {
          background: var(--jamef-red-dark) !important;
          transform: translateY(-1px) !important;
        }
        
        .security-note {
          margin-top: 24px;
          padding: 16px;
          background: #f8f9fb;
          border: 1px solid #edf0f3;
          border-radius: 14px;
          color: #6b7280;
          font-size: 13px;
          line-height: 1.45;
        }
        .footer-text {
          margin-top: 34px;
          color: #9ca3af;
          font-size: 12px;
          text-align: center;
        }
        </style>
    """, unsafe_allow_html=True)

# Se já estiver autenticado e nas páginas internas, aplicamos o CSS clássico do Dashboard
else:
    st.markdown("""
        <style>
        .stApp {
            background-color: #F8F9FA;
        }
        h1, h2, h3 {
            color: #002855 !important;
            font-family: 'Helvetica Neue', sans-serif;
        }
        /* Botões Jamef */
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

# 4. Tabelas de Apoio Embarcadas (Mock de Carga)
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
# 5. EXECUÇÃO DO FLUXO DO SITE
# ==========================================

# --- TELA DE LOGIN ---
if st.session_state.tela_atual == "LOGIN":
    # Grid principal (1.1fr 0.9fr) mapeada em duas colunas Streamlit
    col_esquerda, col_direita = st.columns([1.1, 0.9])
    
    with col_esquerda:
        st.markdown("""
            <div class="brand-area">
              <div class="route-lines"></div>
              <div class="brand-content">
                <div class="system-badge">
                  <span></span>
                  Plataforma Comercial
                </div>
                <h1>Simulador de Fretes Jamef</h1>
                <p>
                  Uma solução para apoiar decisões comerciais com agilidade,
                  padronização e inteligência na formação de preços.
                </p>
                <div class="info-grid">
                  <div class="info-card">
                    <strong>Frete</strong>
                    <small>Simulação estruturada por rota e perfil de operação.</small>
                  </div>
                  <div class="info-card">
                    <strong>Margem</strong>
                    <small>Análise de viabilidade comercial e financeira.</small>
                  </div>
                  <div class="info-card">
                    <strong>Dados</strong>
                    <small>Base analítica para decisões mais consistentes.</small>
                  </div>
                </div>
              </div>
            </div>
        """, unsafe_allow_html=True)
        
    with col_direita:
        st.markdown("""
            <div class="login-area-container">
              <div class="login-card-container">
                <img src="https://www.jamef.com.br/wp-content/uploads/2021/04/Logo_Jamef.png" alt="Logo Jamef" class="logo-img" />
                <h2>Acesse sua conta</h2>
                <p class="subtitle">
                  Entre com seu usuário corporativo para acessar o ambiente do simulador.
                </p>
              </div>
            </div>
        """, unsafe_allow_html=True)
        
        # O formulário nativo do Streamlit inserido exatamente no container visual
        with st.container():
            # Margem para ajustar posição do form
            st.markdown("<div style='max-width: 430px; margin: -120px auto 0;'>", unsafe_allow_html=True)
            with st.form("login_form"):
                usuario = st.text_input("E-mail corporativo", placeholder="nome.sobrenome@jamef.com.br")
                senha = st.text_input("Senha", type="password", placeholder="Digite sua senha")
                botao_entrar = st.form_submit_button("Entrar no simulador")
                
                if botao_entrar:
                    # VALIDACAO ADMIN E CORPORATIVO SOLICITADA
                    if usuario == "admin" and senha == "admin":
                        st.session_state.autenticado = True
                        st.session_state.usuario_nome = "Admin"
                        st.session_state.tela_atual = "PASSO_1"
                        st.rerun()
                    elif "@jamef.com.br" in usuario and len(senha) >= 4:
                        st.session_state.autenticado = True
                        st.session_state.usuario_nome = usuario.split("@")[0].title()
                        st.session_state.tela_atual = "PASSO_1"
                        st.rerun()
                    else:
                        st.error("Credenciais inválidas. Use 'admin' ou um e-mail @jamef.com.br.")
                        
            st.markdown("""
                <div class="security-note" style='max-width: 430px; margin: 0 auto;'>
                  Ambiente de uso interno. O acesso é restrito a usuários autorizados
                  para consulta, simulação e análise de condições comerciais.
                </div>
                <div class="footer-text" style='max-width: 430px; margin: 0 auto;'>
                  © 2026 Jamef Transportes | Simulador de Fretes
                </div>
              </div>
            """, unsafe_allow_html=True)

# --- SESSÃO AUTENTICADA: APRESENTAÇÃO DE CONTEÚDO ---
if st.session_state.autenticado:
    
    # Header do App
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
            
    # Stepper Indicador de Etapas
    passos = ["1. Parâmetros", "2. Importação", "3. Cálculo Frete", "4. Atribuição Custo", "5. Dashboard"]
    passo_map = {"PASSO_1": 0, "PASSO_2": 1, "PASSO_3": 2, "PASSO_4": 3, "PASSO_5": 4}
    idx_atual = passo_map.get(st.session_state.tela_atual, 0)
    
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

    # --- PASSO 1: CONFIGURAÇÃO DE PARAMETROS ---
    if st.session_state.tela_atual == "PASSO_1":
        st.subheader("⚙️ Configuração Geral da Simulação")
        st.write("Defina as regras comerciais de margem e alçada de desconto.")
        
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
            
            desconto_limite = 5.0 if alcada_sel == "Vendedor" else (15.0 if alcada_sel == "Gerente Regional" else 100.0)
            
            desconto_sel = st.slider(
                "Desconto Comercial a ser Aplicado (%)", 
                min_value=0.0, 
                max_value=float(desconto_limite), 
                value=float(st.session_state.params["desconto"]),
                step=0.5
            )
            margem_sel = st.number_input("Margem de Contribuição Alvo (%)", min_value=1.0, max_value=100.0, value=float(st.session_state.params["margem_alvo"]))

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

    # --- PASSO 2: IMPORTAÇÃO DE HISTÓRICO ---
    elif st.session_state.tela_atual == "PASSO_2":
        st.subheader("📥 Upload do Histórico de Embarques")
        st.write("Forneça a volumetria de dados reais que deseja testar na simulação.")
        
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

        if st.session_state.df_usuario is not None:
            st.markdown("##### Preview do Arquivo Carregado")
            st.dataframe(st.session_state.df_usuario.head(5), use_container_width=True)

        st.markdown("<br>", unsafe_allow_html=True)
        col_nav1, col_nav2 = st.columns(2)
        with col_nav1:
            if st.button("⬅ Voltar para Parâmetros"):
                st.session_state.tela_atual = "PASSO_1"
                st.rerun()
        with col_nav2:
            desativado = st.session_state.df_usuario is None
            if st.button("Calcular Frete Padrão ➔", disabled=desativado):
                st.session_state.tela_atual = "PASSO_3"
                st.rerun()

    # --- PASSO 3: CÁLCULO DE FRETE COM ALÇADA ---
    elif st.session_state.tela_atual == "PASSO_3":
        st.subheader("🧮 Processamento do Frete Comercial")
        st.write(f"Cálculo baseado no desconto aplicado de **{st.session_state.params['desconto']}%**")
        
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
        st.session_state.df_calculado = df_calc
        
        st.dataframe(df_calc[["Cidade Destino", "UF", "Peso Real", "Peso Cubado", "Valor Mercadoria", "Frete Calculado (R$)"]].style.format({
            "Peso Real": "{:,.2f} kg",
            "Peso Cubado": "{:,.2f} kg",
            "Valor Mercadoria": "R$ {:,.2f}",
            "Frete Calculado (R$)": "R$ {:,.2f}"
        }), use_container_width=True)

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

    # --- PASSO 4: ATRIBUIÇÃO DE CUSTO OPERACIONAL ---
    elif st.session_state.tela_atual == "PASSO_4":
        st.subheader("🚛 Atribuição dos Custos das Rotas")
        st.write("Cruzamento do histórico com o rateio de custos de transporte consolidado.")
        
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
        st.session_state.df_calculado = df_calc
        
        st.dataframe(df_calc[["Cidade Destino", "UF", "Peso Real", "Frete Calculado (R$)", "Custo Total (R$)"]].style.format({
            "Peso Real": "{:,.2f} kg",
            "Frete Calculado (R$)": "R$ {:,.2f}",
            "Custo Total (R$)": "R$ {:,.2f}"
        }), use_container_width=True)

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

    # --- PASSO 5: DASHBOARD FINANCEIRO ---
    elif st.session_state.tela_atual == "PASSO_5":
        st.subheader("📊 Dashboard de Resultados da Simulação")
        
        df_final = st.session_state.df_calculado.copy()
        
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

        # Tabela Detalhada
        st.subheader("📋 Visão Consolidada")
        st.dataframe(df_final.style.format({
            "Peso Real": "{:,.1f} kg",
            "Valor Mercadoria": "R$ {:,.2f}",
            "Frete Calculado (R$)": "R$ {:,.2f}",
            "Custo Total (R$)": "R$ {:,.2f}"
        }), use_container_width=True)

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

