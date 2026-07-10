import os
import streamlit as st
import pandas as pd
import numpy as np

# ==========================================
# 1. CONFIGURAÇÃO BÁSICA
# ==========================================
st.set_page_config(page_title="Validação de Racional", layout="wide")

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
if "params" not in st.session_state: st.session_state.params = {"sigla_origem": "CWB", "desconto": 0.0, "margem_alvo": 15.0}
if "df_usuario" not in st.session_state: st.session_state.df_usuario = None
if "df_calculado" not in st.session_state: st.session_state.df_calculado = None

# ==========================================
# 3. LEITURA DE DADOS (À PROVA DE FALHAS)
# ==========================================
def padronizar_colunas(df):
    if df is None: return None
    df.columns = df.columns.astype(str).str.strip().str.upper().str.replace(' ', '_', regex=False)
    return df

@st.cache_data
def carregar_arquivos():
    arquivos_no_diretorio = os.listdir('.')
    
    def encontrar_arquivo(nomes_possiveis):
        for arq in arquivos_no_diretorio:
            for nome in nomes_possiveis:
                if arq.lower() == nome.lower():
                    return arq
        return None

    arq_cidades = encontrar_arquivo(['cidades.csv', 'cidades.xlsx', 'db_cidades_atendimento.xlsx', 'db_cidades_atendimento.csv'])
    arq_custos = encontrar_arquivo(['custos.csv', 'custos.xlsx', 'db_custo_padrão.xlsx', 'db_custo_padrao.xlsx', 'db_custo_padrao.csv', 'db_custo_padrão.csv'])
    
    df_cidades, df_custo = None, None
    
    try:
        if arq_cidades:
            df_cidades = pd.read_csv(arq_cidades, sep=None, engine='python', encoding_errors='ignore') if arq_cidades.endswith('.csv') else pd.read_excel(arq_cidades)
        if arq_custos:
            df_custo = pd.read_csv(arq_custos, sep=None, engine='python', encoding_errors='ignore') if arq_custos.endswith('.csv') else pd.read_excel(arq_custos)

        df_cidades = padronizar_colunas(df_cidades)
        df_custo = padronizar_colunas(df_custo)

        return df_cidades, df_custo, arquivos_no_diretorio
    except Exception:
        return None, None, arquivos_no_diretorio

df_cidades_ref, df_custo_ref, arquivos_locais = carregar_arquivos()

# ==========================================
# 4. TELA DE LOGIN SIMPLES
# ==========================================
if not st.session_state.get("autenticado", False):
    st.title("Acesso ao Simulador (Modo Limpo)")
    
    with st.expander("🛠️ Arquivos Lidos no Servidor (Diagnóstico)", expanded=True):
        st.code(arquivos_locais)
        
    if st.button("Entrar (Bypass Login)"):
        st.session_state.autenticado = True
        st.session_state.tela_atual = "PASSO_1"
        st.rerun()

# ==========================================
# 5. FLUXO PRINCIPAL DO SIMULADOR
# ==========================================
else:
    st.sidebar.title("Navegação")
    if st.sidebar.button("Sair e Reiniciar"):
        for key in st.session_state.keys():
            del st.session_state[key]
        st.rerun()

    tela_atual = st.session_state.get("tela_atual", "PASSO_1")

    # --- PASSO 1 ---
    if tela_atual == "PASSO_1":
        st.header("Passo 1: Parâmetros")
        cidade_sel = st.selectbox("Selecione a Origem", list(origens_dict.keys()))
        if st.button("Avançar"):
            st.session_state.params["sigla_origem"] = origens_dict[cidade_sel]
            st.session_state.tela_atual = "PASSO_2"
            st.rerun()

    # --- PASSO 2 ---
    elif tela_atual == "PASSO_2":
        st.header("Passo 2: Dados de Embarque")
        if st.button("💡 Usar Dados de Teste"):
            st.session_state.df_usuario = pd.DataFrame({
                "CIDADE_DESTINO": ["PALMAS", "MACEIO", "RIO LARGO"], "UF": ["TO", "AL", "AL"],
                "PESO_REAL": [84.00, 234.00, 93.00], "PESO_CUBADO": [193.08, 459.03, 202.44], 
                "VALOR_MERCADORIA": [9178.41, 17853.74, 9620.00]
            })
        
        uploaded_file = st.file_uploader("Ou suba um arquivo Excel/CSV", type=["csv", "xlsx"])
        if uploaded_file:
            df_up = pd.read_excel(uploaded_file) if uploaded_file.name.endswith('.xlsx') else pd.read_csv(uploaded_file, sep=None, engine='python')
            df_up = padronizar_colunas(df_up)
            st.session_state.df_usuario = df_up
            st.success("Arquivo lido!")

        if st.session_state.df_usuario is not None:
            st.dataframe(st.session_state.df_usuario.head())
        
        if st.button("Avançar", disabled=st.session_state.df_usuario is None):
            st.session_state.tela_atual = "PASSO_3"
            st.rerun()

    # --- PASSO 3 ---
    elif tela_atual == "PASSO_3":
        st.header("Passo 3: Frete (Mock)")
        df_calc = st.session_state.df_usuario.copy()
        df_calc["FRETE_SIMULADO"] = 150.0
        st.session_state.df_calculado = df_calc
        
        st.dataframe(df_calc)
        if st.button("Avançar para Custos"):
            st.session_state.tela_atual = "PASSO_4"
            st.rerun()

    # --- PASSO 4 ---
    elif tela_atual == "PASSO_4":
        st.header("Passo 4: Validação do Racional de Custo")
        
        if df_cidades_ref is None or df_custo_ref is None:
            st.error("Arquivos de referência não encontrados. Verifique se subiu os arquivos corretamente.")
            st.stop()

        with st.expander("Diagnóstico das Colunas Encontradas (Para conferência)", expanded=False):
            st.write("**db_Cidades_Atendimento:**", df_cidades_ref.columns.tolist())
            st.write("**db_Custo_Padrão:**", df_custo_ref.columns.tolist())

        try:
            df_calc = st.session_state.df_calculado.copy()
            
            # Identifica as colunas dinamicamente (CAP_INT, C_I ou C__I)
            col_cap_int = 'CAP_INT'
            if col_cap_int not in df_cidades_ref.columns:
                if 'C_I' in df_cidades_ref.columns: col_cap_int = 'C_I'
                elif 'C__I' in df_cidades_ref.columns: col_cap_int = 'C__I'

            # 1. Merge Cidades (Cruza o embarque com a tabela de cidades)
            df_enriquecido = pd.merge(df_calc, df_cidades_ref[['CIDADE', 'UF', 'FILIAL_ATENDIMENTO', col_cap_int]], 
                                      left_on=['CIDADE_DESTINO', 'UF'], right_on=['CIDADE', 'UF'], how='left')

            # 2. Capital vs Interior
            df_enriquecido['REGIAO_CALC'] = np.where(df_enriquecido[col_cap_int].astype(str).str.upper() == 'C', 'CAPITAL', 'INTERIOR')

            # 3. Rota
            origem = st.session_state.params["sigla_origem"]
            df_enriquecido['ROTA_CALC'] = origem + '-' + df_enriquecido['FILIAL_ATENDIMENTO'].astype(str)
            
            # 4. Merge Custos (Cruza a Rota com a Tabela de Custos)
            df_final_custo = pd.merge(df_enriquecido, df_custo_ref, left_on='ROTA_CALC', right_on='ROTA', how='left')

            # 5. Cálculo Matemático da Jamef
            custos_totais = []
            logs = []
            
            for idx, row in df_final_custo.iterrows():
                if pd.isna(row.get('PM')):
                    custos_totais.append(0.0)
                    logs.append("❌ Rota não localizada")
                    continue
                
                peso_real = float(row.get('PESO_REAL', 0))
                valor_merc = float(row.get('VALOR_MERCADORIA', 0))
                regiao = str(row.get('REGIAO_CALC'))
                pm = float(row.get('PM', 0))
                peso_calculo = max(peso_real, pm)
                
                if regiao == 'CAPITAL':
                    custo_kg = float(row.get('R$_CAPITAL', 0))
                    perc_nf = float(row.get('%_CAPITAL', 0))
                else:
                    custo_kg = float(row.get('R$_INTERIOR', 0))
                    perc_nf = float(row.get('%_INTERIOR', 0))
                
                custo_peso = peso_calculo * custo_kg
                custo_var = valor_merc * (perc_nf / 100.0) 
                custos_totais.append(custo_peso + custo_var)
                logs.append(f"{regiao} | PM: {pm} | R$/kg: {custo_kg} | %: {perc_nf}")

            df_final_custo['CUSTO_TOTAL'] = custos_totais
            df_final_custo['DIAGNÓSTICO_CALCULO'] = logs
            
            # Exibe as colunas que importam para a validação
            colunas_ver_na_tela = ['CIDADE_DESTINO', 'UF', 'FILIAL_ATENDIMENTO', col_cap_int, 'REGIAO_CALC', 'ROTA_CALC', 'PM', 'PESO_REAL', 'CUSTO_TOTAL', 'DIAGNÓSTICO_CALCULO']
            st.dataframe(df_final_custo[[c for c in colunas_ver_na_tela if c in df_final_custo.columns]])

            if st.button("Avançar para Passo 5"):
                st.session_state.tela_atual = "PASSO_5"
                st.rerun()

        except Exception as e:
            st.error(f"Erro durante o cruzamento: {e}")

    # --- PASSO 5 ---
    elif tela_atual == "PASSO_5":
        st.header("Passo 5: Resumo Financeiro")
        
        df_final = st.session_state.df_calculado
        receita = df_final["FRETE_SIMULADO"].sum()
        custo = df_final["CUSTO_TOTAL"].sum()
        margem = receita - custo
        perc = (margem / receita) * 100 if receita > 0 else 0
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Frete Total", f"R$ {receita:,.2f}")
        col2.metric("Custo Total", f"R$ {custo:,.2f}")
        col3.metric("Margem Nominal", f"R$ {margem:,.2f}")
        col4.metric("Margem %", f"{perc:.1f}%")
        
        if st.button("Reiniciar"):
            st.session_state.tela_atual = "PASSO_1"
            st.rerun()
