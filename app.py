import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# ==========================================
# 1. CONFIGURAÇÃO DE PÁGINA
# ==========================================
st.set_page_config(page_title="Simulador de Fretes Jamef", page_icon="🚛", layout="wide")

# ==========================================
# 2. LISTA OFICIAL DE FILIAIS DE ORIGEM
# ==========================================
origens_dict = {
    "Goiania - GO (GYN)": "GYN", "Uberlândia - MG (UDI)": "UDI", "Divinópolis - MG (DIV)": "DIV",
    "Belém - PA (BEL)": "BEL", "Fortaleza - CE (FOR)": "FOR", "Feira de Santana - BA (FES)": "FES",
    "Salvador - BA (SSA)": "SSA", "Curitiba - PR (CWB)": "CWB", "Florianópolis - SC (FLN)": "FLN",
    "Brasilia - DF (BSB)": "BSB", "Belo Horizonte - MG (BHZ)": "BHZ", "Recife - PE (REC)": "REC",
    "São Luis - MA (SLZ)": "SLZ", "Natal - RN (NAT)": "NAT", "Teresina - PI (THE)": "THE",
    "Porto Alegre - RS (POA)": "POA", "Brasilia - DF (CGB)": "CGB", "São José do Rio Preto - SP (SJP)": "SJP",
    "Espirito Santo - ES (VIX)": "VIX", "Campinas - SP (CPQ)": "CPQ", "Caxias do Sul - RS (CXJ)": "CXJ",
    "Blumenau - SC (BNU)": "BNU", "Itajai - SC (ITJ)": "ITJ", "Maceio - AL (MCZ)": "MCZ",
    "João Pessoa - PB (JPA)": "JPA", "Brasilia - DF (CGR)": "CGR", "Bauru - SP (BAU)": "BAU",
    "Londrina - PR (LDB)": "LDB", "Ribeirão Preto - SP (RAO)": "RAO", "Maringa - PR (MGF)": "MGF",
    "Aracaju - SE (AJU)": "AJU", "Rio de Janeiro - RJ (RIO)": "RIO", "Joinville - SC (JOI)": "JOI",
    "São Paulo - SP (SAO)": "SAO", "Campo dos Goytacazes - RJ (CAW)": "CAW", "Cascavel - PR (CAC)": "CAC",
    "Chapecó - SC (XAP)": "XAP", "Criciúma - SC (CCM)": "CCM", "Itabuna - BA (ITN)": "ITN",
    "Juiz de Fora - MG (JDF)": "JDF", "Lages - SC (LAG)": "LAG", "Pouso Alegre - MG (PSA)": "PSA", 
    "Presidente Prudente - SP (PPB)": "PPB", "Santos - SP (SSZ)": "SSZ", "São José dos Campos - SP (SJK)": "SJK",
    "Sorocaba - SP (SOD)": "SOD", "Vitoria da Conquista - BA (VDC)": "VDC"
}

# ==========================================
# 3. INICIALIZAÇÃO DO ESTADO (SESSÃO)
# ==========================================
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False
if "tela_atual" not in st.session_state:
    st.session_state.tela_atual = "LOGIN"
if "usuario_nome" not in st.session_state:
    st.session_state.usuario_nome = ""

if "params" not in st.session_state:
    st.session_state.params = {"cidade_origem": "São Paulo - SP (SAO)", "sigla_origem": "SAO", "alcada": "Vendedor", "desconto": 0.0, "margem_alvo": 15.0}
if "df_usuario" not in st.session_state:
    st.session_state.df_usuario = None
if "df_calculado" not in st.session_state:
    st.session_state.df_calculado = None

# ==========================================
# 4. FUNÇÕES DE CARREGAMENTO & FAXINA DE DADOS
# ==========================================
def padronizar_colunas(df):
    """Limpa cabeçalhos para evitar erros (KeyError) no cruzamento de dados"""
    if df is None: return None
    df.columns = (df.columns.astype(str).str.strip().str.upper()
                  .str.replace(' ', '_', regex=False)
                  .str.replace('/', '_', regex=False)
                  .str.replace('.', '_', regex=False)
                  .str.normalize('NFKD').str.encode('ascii', errors='ignore').str.decode('utf-8'))
    return df

@st.cache_data
def carregar_arquivos_referencia():
    try:
        df_cidades = pd.read_excel("db_Cidades_Atendimento.xlsx")
        df_custo = pd.read_excel("db_Custo_Padrão.xlsx")
        
        df_cidades = padronizar_colunas(df_cidades)
        df_custo = padronizar_colunas(df_custo)
        
        # --- LÓGICA DA REGRA C/I ---
        # Cria a coluna TIPO_REGIAO_CALC baseada na regra que você definiu
        # A função .str.contains('CAPITAL') encontra a palavra 'CAPITAL' no texto da coluna C_I
        df_cidades['TIPO_REGIAO_CALC'] = np.where(df_cidades['C_I'].str.contains('CAPITAL', case=False, na=False), 'CAPITAL', 'INTERIOR')
            
        return df_cidades, df_custo
    except Exception as e:
        return None, None

df_cidades_ref, df_custo_ref = carregar_arquivos_referencia()

# ==========================================
# 5. TELA DE LOGIN (CSS E HTML PRESERVADOS)
# ==========================================
if st.session_state.tela_atual == "LOGIN":
    # ... (código da tela de login - mantido igual)
    # Para encurtar, não vou repetir todo o HTML aqui. Mantenha o que já está no seu app.py
    st.markdown("<h1>Login...</h1>", unsafe_allow_html=True) # Exemplo
    # Lógica do formulário de login
    with st.form("login_form"):
        usuario = st.text_input("E-mail corporativo", placeholder="admin ou @jamef.com.br")
        senha = st.text_input("Senha", type="password")
        if st.form_submit_button("Entrar no simulador"):
            if (usuario == "admin" and senha == "admin") or ("@jamef.com.br" in usuario and len(senha) > 3):
                st.session_state.autenticado = True
                st.session_state.usuario_nome = "Admin" if usuario == "admin" else usuario.split("@")[0].title()
                st.session_state.tela_atual = "PASSO_1"
                st.rerun()
            else:
                st.error("Credenciais inválidas.")

# ==========================================
# 6. TELAS DO SIMULADOR (AUTENTICADO)
# ==========================================
elif st.session_state.autenticado:
    # (CSS e Header interno permanecem os mesmos)
    st.title("Simulador de Custos e Fretes — Jamef")
    # ... (Resto do Header e Stepper)

    # --- PASSO 1: PARÂMETROS ---
    if st.session_state.tela_atual == "PASSO_1":
        # (Código do Passo 1 permanece o mesmo)
        st.subheader("⚙️ Configuração Geral da Simulação")
        if st.button("Avançar para Importação ➔"):
            st.session_state.tela_atual = "PASSO_2"
            st.rerun()
    
    # --- PASSO 2: IMPORTAÇÃO ---
    elif st.session_state.tela_atual == "PASSO_2":
        # (Código do Passo 2 permanece o mesmo)
        st.subheader("📥 Upload do Histórico")
        if st.button("Calcular Frete ➔", disabled=st.session_state.df_usuario is None):
            st.session_state.tela_atual = "PASSO_3"
            st.rerun()

    # --- PASSO 3: FRETE MOCK ---
    elif st.session_state.tela_atual == "PASSO_3":
        # (Código do Passo 3 permanece o mesmo)
        st.subheader("🧮 Processamento de Frete (Mock)")
        if st.button("Atribuir Custos Reais ➔"):
            st.session_state.tela_atual = "PASSO_4"
            st.rerun()

    # --- PASSO 4: CUSTO REAL JAMEF (COM CORREÇÃO FINAL) ---
    elif st.session_state.tela_atual == "PASSO_4":
        st.subheader("🚛 Atribuição Inteligente de Custos")
        
        if df_cidades_ref is None or df_custo_ref is None:
            st.error("⚠️ Falha ao carregar 'db_Cidades_Atendimento.xlsx' ou 'db_Custo_Padrão.xlsx' do repositório.")
            st.stop()

        with st.spinner("Analisando Filiais e Regiões..."):
            try:
                df_calc = st.session_state.df_calculado.copy()
                df_calc = padronizar_colunas(df_calc)
                
                # Garante que as colunas de join no df_calc estejam limpas
                df_calc['CIDADE_DESTINO'] = df_calc['CIDADE_DESTINO'].astype(str).str.strip().str.upper()
                df_calc['UF'] = df_calc['UF'].astype(str).str.strip().str.upper()
                
                # Colunas esperadas para o merge
                colunas_cidades_necessarias = ['CIDADE', 'UF', 'FILIAL_ATENDIMENTO', 'TIPO_REGIAO_CALC']

                # 1. Encontra Filial e Região
                df_enriquecido = pd.merge(
                    df_calc, 
                    df_cidades_ref[colunas_cidades_necessarias],
                    left_on=['CIDADE_DESTINO', 'UF'], 
                    right_on=['CIDADE', 'UF'], 
                    how='left'
                )

                # 2. Cria a Rota
                origem = st.session_state.params["sigla_origem"]
                df_enriquecido['COD_ROTA'] = origem + '-' + df_enriquecido['FILIAL_ATENDimento']
                
                # 3. Busca Custos na tabela
                df_final_custo = pd.merge(df_enriquecido, df_custo_ref, on='COD_ROTA', how='left')

                # 4. Cálculo da Lógica Jamef (PM, Capital x Interior)
                custos_totais = []
                for idx, row in df_final_custo.iterrows():
                    if pd.isna(row.get('PM', np.nan)): 
                        custos_totais.append(0.0) 
                        continue

                    peso_real = float(row.get('PESO_REAL', 0))
                    valor_merc = float(row.get('VALOR_MERCADORIA', 0))
                    # USA A NOVA COLUNA CALCULADA
                    regiao = str(row.get('TIPO_REGIAO_CALC', 'INTERIOR')).strip().upper()
                    pm = float(row.get('PM', 0))
                    
                    peso_calculo = max(peso_real, pm)
                    
                    if regiao == 'CAPITAL':
                        custo_kg = float(row.get('CUSTO_KG_CAP', 0))
                        perc_nf = float(row.get('PERC_NF_CAP', 0))
                    else: # INTERIOR
                        custo_kg = float(row.get('CUSTO_KG_INT', 0))
                        perc_nf = float(row.get('PERC_NF_INT', 0))
                    
                    custo_fixo = peso_calculo * custo_kg
                    custo_var = valor_merc * (perc_nf / 100.0) 
                    custos_totais.append(custo_fixo + custo_var)

                df_final_custo['CUSTO_TOTAL'] = custos_totais
                st.session_state.df_calculado = df_final_custo
                
                st.dataframe(df_final_custo)

            except Exception as e:
                st.error(f"Ocorreu um erro inesperado durante o processamento dos custos: {e}")

    # --- PASSO 5: DASHBOARD ---
    elif st.session_state.tela_atual == "PASSO_5":
        # (Código do Passo 5 permanece o mesmo)
        st.subheader("📊 Dashboard Final da Simulação")
