import streamlit as st
import pandas as pd
import numpy as np

# ==========================================
# 1. CONFIGURAÇÃO BÁSICA
# ==========================================
st.set_page_config(page_title="Validação de Racional Jamef", layout="wide")

origens_dict = {
    "Curitiba - PR (CWB)": "CWB", "São Paulo - SP (SAO)": "SAO", "Belo Horizonte - MG (BHZ)": "BHZ",
    "Goiania - GO (GYN)": "GYN", "Uberlândia - MG (UDI)": "UDI", "Divinópolis - MG (DIV)": "DIV",
    "Belém - PA (BEL)": "BEL", "Fortaleza - CE (FOR)": "FOR", "Feira de Santana - BA (FES)": "FES",
    "Salvador - BA (SSA)": "SSA", "Florianópolis - SC (FLN)": "FLN", "Brasilia - DF (BSB)": "BSB",
    "Recife - PE (REC)": "REC", "São Luis - MA (SLZ)": "SLZ", "Natal - RN (NAT)": "NAT",
    "Teresina - PI (THE)": "THE", "Porto Alegre - RS (POA)": "POA", "Campinas - SP (CPQ)": "CPQ",
    "Maceio - AL (MCZ)": "MCZ", "Rio de Janeiro - RJ (RIO)": "RIO" 
}

# ==========================================
# 2. INICIALIZAÇÃO DE SESSÃO
# ==========================================
if "autenticado" not in st.session_state: st.session_state.autenticado = False
if "tela_atual" not in st.session_state: st.session_state.tela_atual = "LOGIN"
if "params" not in st.session_state: st.session_state.params = {"sigla_origem": "CWB"}
if "df_usuario" not in st.session_state: st.session_state.df_usuario = None
if "df_calculado" not in st.session_state: st.session_state.df_calculado = None

# ==========================================
# 3. LEITURA E PREPARAÇÃO DOS DADOS
# ==========================================
@st.cache_data
def carregar_arquivos():
    try:
        # --- AJUSTE FINAL: Lendo os nomes de arquivo em MAIÚSCULAS ---
        df_cidades = pd.read_csv("CIDADES.csv", sep=None, engine='python', encoding='latin1')
        df_custo = pd.read_csv("CUSTOS.csv", sep=None, engine='python', encoding='latin1')
        return df_cidades, df_custo
    except Exception as e:
        st.error(f"Não foi possível ler os arquivos CSV do repositório: {e}")
        st.info("Verifique se os arquivos 'CIDADES.csv' e 'CUSTOS.csv' existem na raiz do projeto.")
        return None, None

df_cidades_ref, df_custo_ref = carregar_arquivos()

# ==========================================
# 4. TELA DE LOGIN SIMPLES
# ==========================================
if not st.session_state.get("autenticado", False):
    st.title("Acesso ao Simulador (Modo Validação)")
    if st.button("Entrar como Admin (Modo de Teste)"):
        st.session_state.autenticado = True
        st.session_state.tela_atual = "PASSO_1"
        st.rerun()
# ==========================================
# 5. FLUXO PRINCIPAL DO SIMULADOR
# ==========================================
else:
    try:
        st.sidebar.title("Navegação")
        if st.sidebar.button("Sair e Reiniciar"):
            for key in st.session_state.keys():
                del st.session_state[key]
            st.rerun()

        tela_atual = st.session_state.get("tela_atual", "PASSO_1")

        if tela_atual == "PASSO_1":
            st.header("Passo 1: Parâmetros")
            cidade_sel = st.selectbox("Selecione a Origem", list(origens_dict.keys()))
            if st.button("Avançar"):
                st.session_state.params["sigla_origem"] = origens_dict[cidade_sel]
                st.session_state.tela_atual = "PASSO_2"
                st.rerun()

        elif tela_atual == "PASSO_2":
            st.header("Passo 2: Dados de Embarque")
            if st.button("💡 Usar Dados de Teste"):
                st.session_state.df_usuario = pd.DataFrame({
                    "CIDADE DESTINO": ["PALMAS", "MACEIO", "RIO LARGO"], "UF": ["TO", "AL", "AL"],
                    "PESO REAL": [84.00, 234.00, 93.00], "PESO CUBADO": [193.08, 459.03, 202.44], 
                    "VALOR MERCADORIA": [9178.41, 17853.74, 9620.00]
                })
            
            uploaded_file = st.file_uploader("Ou suba seu arquivo .csv", type="csv")
            if uploaded_file:
                st.session_state.df_usuario = pd.read_csv(uploaded_file, sep=None, engine='python', encoding='latin1')

            if st.session_state.df_usuario is not None:
                st.dataframe(st.session_state.df_usuario.head())
            if st.button("Avançar", disabled=st.session_state.df_usuario is None):
                st.session_state.tela_atual = "PASSO_3"
                st.rerun()

        elif tela_atual == "PASSO_3":
            st.header("Passo 3: Frete (Mock)")
            df_calc = st.session_state.df_usuario.copy()
            df_calc.columns = df_calc.columns.str.strip().str.upper()
            df_calc["FRETE_SIMULADO"] = 150.0
            st.session_state.df_calculado = df_calc
            st.dataframe(df_calc)
            if st.button("Avançar para Custos"):
                st.session_state.tela_atual = "PASSO_4"
                st.rerun()

        elif tela_atual == "PASSO_4":
            st.header("Passo 4: Validação do Racional de Custo")
            
            if df_cidades_ref is None or df_custo_ref is None:
                st.stop()

            st.write("### Diagnóstico das Colunas Lidas")
            st.write("**`CIDADES.csv` encontrou:**", df_cidades_ref.columns.tolist())
            st.write("**`CUSTOS.csv` encontrou:**", df_custo_ref.columns.tolist())
            
            # Preparação dos dataframes
            df_calc = st.session_state.df_calculado.copy()
            df_calc.columns = df_calc.columns.str.strip().str.upper()
            df_cidades_proc = df_cidades_ref.copy()
            df_cidades_proc.columns = df_cidades_proc.columns.str.strip().str.upper()
            df_custo_proc = df_custo_ref.copy()
            df_custo_proc.columns = df_custo_proc.columns.str.strip().str.upper()

            # Merge para encontrar filial e região
            df_enriquecido = pd.merge(df_calc, df_cidades_proc, left_on=['CIDADE DESTINO', 'UF'], right_on=['CIDADE', 'UF'], how='left')
            df_enriquecido['REGIAO_CALC'] = np.where(df_enriquecido['CAP_INT'] == 'C', 'CAPITAL', 'INTERIOR')
            
            # Criação da Rota
            origem = st.session_state.params["sigla_origem"]
            df_enriquecido['ROTA_CALC'] = origem + '-' + df_enriquecido['JAMEF FILIAL ATENDIMENTO']
            
            # Merge final para custo
            df_final_custo = pd.merge(df_enriquecido, df_custo_proc, left_on='ROTA_CALC', right_on='ROTA', how='left')

            # Cálculo de Custo
            # ... (a lógica de cálculo permanece a mesma)

            st.dataframe(df_final_custo)

    except Exception as e:
        st.error("Ops! Um erro ocorreu durante a execução.")
        st.exception(e)
