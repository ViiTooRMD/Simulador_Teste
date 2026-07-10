import os
import streamlit as st
import pandas as pd
import numpy as np

# ==========================================
# 1. CONFIGURAÇÃO BÁSICA E DICIONÁRIOS
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
if "params" not in st.session_state: st.session_state.params = {"sigla_origem": "CWB", "desconto": 0.0, "margem_alvo": 15.0}
if "df_usuario" not in st.session_state: st.session_state.df_usuario = None
if "df_calculado" not in st.session_state: st.session_state.df_calculado = None

# ==========================================
# 3. LEITURA INTELIGENTE DE DADOS (À PROVA DE FALHAS)
# ==========================================
@st.cache_data
def carregar_arquivos():
    arquivos_no_diretorio = os.listdir('.')
    
    # Função para achar arquivo ignorando maiúscula/minúscula
    def encontrar_arquivo(nomes_possiveis):
        for arq in arquivos_no_diretorio:
            for nome in nomes_possiveis:
                if arq.lower() == nome.lower():
                    return arq
        return None

    arq_cidades = encontrar_arquivo(['cidades.csv', 'db_cidades_atendimento.xlsx', 'db_cidades_atendimento.csv'])
    arq_custos = encontrar_arquivo(['custos.csv', 'db_custo_padrão.xlsx', 'db_custo_padrao.xlsx', 'db_custo_padrao.csv'])
    
    df_cidades = None
    df_custo = None
    
    try:
        # Lê Cidades
        if arq_cidades:
            if arq_cidades.endswith('.csv'):
                df_cidades = pd.read_csv(arq_cidades, sep=None, engine='python', encoding_errors='ignore')
            else:
                df_cidades = pd.read_excel(arq_cidades)
        
        # Lê Custos
        if arq_custos:
            if arq_custos.endswith('.csv'):
                df_custo = pd.read_csv(arq_custos, sep=None, engine='python', encoding_errors='ignore')
            else:
                df_custo = pd.read_excel(arq_custos)

        # Padroniza as colunas se conseguiu ler
        if df_cidades is not None:
            df_cidades.columns = df_cidades.columns.astype(str).str.strip().str.upper()
        if df_custo is not None:
            df_custo.columns = df_custo.columns.astype(str).str.strip().str.upper()

        return df_cidades, df_custo, arquivos_no_diretorio
    except Exception as e:
        return None, None, arquivos_no_diretorio

df_cidades_ref, df_custo_ref, arquivos_locais = carregar_arquivos()

# ==========================================
# 4. TELA DE LOGIN 
# ==========================================
if not st.session_state.get("autenticado", False):
    st.title("Acesso ao Simulador (Modo Validação)")
    
    # Scanner para ajudar no diagnóstico se algo der errado
    with st.expander("🛠️ Scanner de Arquivos do GitHub (Diagnóstico)", expanded=True):
        st.write("Estes são os arquivos que o servidor está enxergando na sua pasta:")
        st.code(arquivos_locais)
        
    if st.button("Entrar como Admin"):
        st.session_state.autenticado = True
        st.session_state.tela_atual = "PASSO_1"
        st.rerun()

# ==========================================
# 5. FLUXO DO SIMULADOR
# ==========================================
else:
    st.sidebar.title("Navegação")
    if st.sidebar.button("Sair e Reiniciar"):
        for key in st.session_state.keys():
            del st.session_state[key]
        st.rerun()

    tela_atual = st.session_state.get("tela_atual", "PASSO_1")

    # --- PASSO 1: PARÂMETROS ---
    if tela_atual == "PASSO_1":
        st.header("Passo 1: Parâmetros Comerciais")
        cidade_sel = st.selectbox("Selecione a Origem", list(origens_dict.keys()))
        sigla_sel = origens_dict[cidade_sel]
        
        if st.button("Avançar para Passo 2"):
            st.session_state.params["sigla_origem"] = sigla_sel
            st.session_state.tela_atual = "PASSO_2"
            st.rerun()

    # --- PASSO 2: UPLOAD ---
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
        
        if st.button("Avançar para Passo 3", disabled=st.session_state.df_usuario is None):
            st.session_state.tela_atual = "PASSO_3"
            st.rerun()

    # --- PASSO 3: FRETE ESTIMADO ---
    elif tela_atual == "PASSO_3":
        st.header("Passo 3: Frete Base (Mock)")
        df_calc = st.session_state.df_usuario.copy()
        df_calc.columns = df_calc.columns.astype(str).str.strip().str.upper()
        df_calc["FRETE_SIMULADO"] = 150.0
        st.session_state.df_calculado = df_calc
        
        st.dataframe(df_calc)
        
        if st.button("Avançar para Custos"):
            st.session_state.tela_atual = "PASSO_4"
            st.rerun()

    # --- PASSO 4: CÁLCULO DE CUSTO ---
    elif tela_atual == "PASSO_4":
        st.header("Passo 4: Validação do Racional de Custo")
        
        if df_cidades_ref is None or df_custo_ref is None:
            st.error("Arquivos de referência não encontrados.")
            st.stop()

        with st.expander("Clique para Diagnosticar Colunas Lidas do Excel", expanded=False):
            st.write("**Colunas em Cidades Atendimento:**", df_cidades_ref.columns.tolist())
            st.write("**Colunas em Custo Padrão:**", df_custo_ref.columns.tolist())

        try:
            df_calc = st.session_state.df_calculado.copy()
            
            # 1. Encontrar FILIAL DE ATENDIMENTO e CAP_INT
            df_enriquecido = pd.merge(df_calc, df_cidades_ref[['CIDADE', 'UF', 'JAMEF FILIAL ATENDIMENTO', 'CAP_INT']], 
                                      left_on=['CIDADE DESTINO', 'UF'], right_on=['CIDADE', 'UF'], how='left')

            # 2. Definição se é CAPITAL ou INTERIOR
            df_enriquecido['REGIAO_CALC'] = np.where(df_enriquecido['CAP_INT'] == 'C', 'CAPITAL', 'INTERIOR')

            # 3. Cria Rota
            origem = st.session_state.params["sigla_origem"]
            df_enriquecido['ROTA_CALC'] = origem + '-' + df_enriquecido['JAMEF FILIAL ATENDIMENTO'].astype(str)
            
            # 4. Cruzamento para achar Custo
            df_final_custo = pd.merge(df_enriquecido, df_custo_ref, left_on='ROTA_CALC', right_on='ROTA', how='left')

            # 5. O CÁLCULO REAL COMPLETO 
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
                custo_var = valor_merc * (perc_nf / 100.0) 
                custos_totais.append(custo_peso + custo_var)
                logs.append(f"{regiao} | PM: {pm} | R$/kg: {custo_kg} | %: {perc_nf}")

            df_final_custo['CUSTO_TOTAL'] = custos_totais
            df_final_custo['DIAGNÓSTICO_CALCULO'] = logs
            
            st.write("### Tabela Analítica (Resultados)")
            st.dataframe(df_final_custo)

        except KeyError as e:
            st.error(f"ERRO DE COLUNA: A coluna {e} não foi encontrada. O arquivo Excel pode estar com um nome ligeiramente diferente.")
        except Exception as e:
            st.error(f"Erro durante o processamento: {e}")
