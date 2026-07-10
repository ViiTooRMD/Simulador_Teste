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
# 3. LEITURA DOS ARQUIVOS (AGORA EM CSV)
# ==========================================
@st.cache_data
def carregar_arquivos():
    try:
        # Lê os arquivos CSV usando o separador padrão de vírgula ou ponto-e-vírgula do Excel brasileiro
        df_cidades = pd.read_csv("db_Cidades_Atendimento.csv", sep=None, engine='python')
        df_custo = pd.read_csv("db_Custo_Padrão.csv", sep=None, engine='python')
        
        # Limpa os cabeçalhos das planilhas
        df_cidades.columns = df_cidades.columns.str.strip().str.upper()
        df_custo.columns = df_custo.columns.str.strip().str.upper()
        
        if 'C / I' in df_cidades.columns:
            df_cidades.rename(columns={'C / I': 'C_I'}, inplace=True)
            
        return df_cidades, df_custo
    except Exception as e:
        return None, None

df_cidades_ref, df_custo_ref = carregar_arquivos()

# ==========================================
# 4. TELA DE LOGIN SIMPLES
# ==========================================
if not st.session_state.get("autenticado", False):
    st.title("Acesso ao Simulador (Modo Validação)")
    if st.button("Entrar como Admin"):
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
            sigla_sel = origens_dict[cidade_sel]
            if st.button("Avançar"):
                st.session_state.params["sigla_origem"] = sigla_sel
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
                st.error("Arquivos CSV de referência não encontrados no GitHub. Suba db_Cidades_Atendimento.csv e db_Custo_Padrão.csv.")
                st.stop()

            st.success("✅ Arquivos CSV lidos com sucesso!")
            
            df_calc = st.session_state.df_calculado.copy()
            
            df_calc['CIDADE DESTINO'] = df_calc['CIDADE DESTINO'].astype(str).str.strip().str.upper()
            df_calc['UF'] = df_calc['UF'].astype(str).str.strip().str.upper()
            
            df_cidades_ref['CIDADE'] = df_cidades_ref['CIDADE'].astype(str).str.strip().str.upper()
            df_cidades_ref['UF'] = df_cidades_ref['UF'].astype(str).str.strip().str.upper()

            # 1. Cruzamento para achar FILIAL e C_I
            df_enriquecido = pd.merge(df_calc, df_cidades_ref[['CIDADE', 'UF', 'FILIAL DE ATENDIMENTO', 'C_I']], 
                                      left_on=['CIDADE DESTINO', 'UF'], right_on=['CIDADE', 'UF'], how='left')
            
            # 2. Definição se é CAPITAL ou INTERIOR
            df_enriquecido['REGIAO_CALC'] = np.where(df_enriquecido['C_I'] == 'C', 'CAPITAL', 'INTERIOR')
            
            # 3. Cria Rota
            origem = st.session_state.params["sigla_origem"]
            df_enriquecido['ROTA_CALC'] = origem + '-' + df_enriquecido['FILIAL DE ATENDIMENTO'].astype(str)
            
            # 4. Cruzamento para achar Custo
            df_final_custo = pd.merge(df_enriquecido, df_custo_ref, left_on='ROTA_CALC', right_on='ROTA', how='left')

            # 5. Cálculo Matemático
            custos_totais = []
            logs = []
            
            for idx, row in df_final_custo.iterrows():
                if pd.isna(row.get('PM')):
                    custos_totais.append(0.0)
                    logs.append("❌ Rota não localizada")
                    continue
                
                peso_real = float(row.get('PESO REAL', 0))
                valor_merc = float(row.get('VALOR MERCADORIA', 0))
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
                custo_var = valor_merc * perc_nf 
                custo_total_linha = custo_peso + custo_var
                
                custos_totais.append(custo_total_linha)
                logs.append(f"{regiao} | PM: {pm} | R$/kg: {custo_kg} | %: {perc_nf}")

            df_final_custo['CUSTO_TOTAL'] = custos_totais
            df_final_custo['DIAGNÓSTICO_CALCULO'] = logs
            
            colunas_visiveis = ['CIDADE DESTINO', 'UF', 'FILIAL DE ATENDIMENTO', 'C_I', 'REGIAO_CALC', 'ROTA_CALC', 'PM', 'PESO REAL', 'CUSTO_TOTAL', 'DIAGNÓSTICO_CALCULO']
            st.dataframe(df_final_custo[[c for c in colunas_visiveis if c in df_final_custo.columns]])

    except Exception as e:
        st.error(f"Erro durante a execução: {e}")
