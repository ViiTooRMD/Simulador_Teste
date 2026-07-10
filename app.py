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
if "params" not in st.session_state: st.session_state.params = {"sigla_origem": "CWB", "desconto": 0.0, "margem_alvo": 15.0}
if "df_usuario" not in st.session_state: st.session_state.df_usuario = None
if "df_calculado" not in st.session_state: st.session_state.df_calculado = None

# ==========================================
# 3. LEITURA E PREPARAÇÃO DOS DADOS
# ==========================================
@st.cache_data
def carregar_arquivos():
    try:
        df_cidades = pd.read_excel("db_Cidades_Atendimento.xlsx")
        df_custo = pd.read_excel("db_Custo_Padrão.xlsx")
        
        # Mantém a padronização para garantir consistência
        for col in df_cidades.columns:
            df_cidades[col] = df_cidades[col].astype(str).str.strip().str.upper()
        
        for col in df_custo.columns:
            df_custo[col] = df_custo[col].astype(str).str.strip().str.upper()
            
        return df_cidades, df_custo
    except FileNotFoundError:
        return None, None
    except Exception as e:
        st.error(f"Erro ao ler arquivos: {e}")
        return None, None

df_cidades_ref, df_custo_ref = carregar_arquivos()

# ==========================================
# 4. TELA DE LOGIN SIMPLES
# ==========================================
if not st.session_state.get("autenticado", False):
    st.title("Acesso ao Simulador (Modo Validação)")
    usuario = st.text_input("Usuário", value="admin")
    senha = st.text_input("Senha", type="password", value="admin")
    
    if st.button("Entrar"):
        if usuario == "admin" and senha == "admin":
            st.session_state.autenticado = True
            st.session_state.tela_atual = "PASSO_1"
            st.rerun()
        else:
            st.error("Use admin / admin")
# ==========================================
# 5. FLUXO DO SIMULADOR
# ==========================================
else:
    st.sidebar.title("Navegação")
    if st.sidebar.button("Sair"):
        for key in st.session_state.keys():
            del st.session_state[key]
        st.rerun()

    tela_atual = st.session_state.get("tela_atual", "PASSO_1")

    if tela_atual == "PASSO_1":
        st.header("Passo 1: Parâmetros Comerciais")
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
        st.header("Passo 3: Frete Base (Mock)")
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
            st.error("Erro ao carregar os arquivos Excel do repositório.")
            st.stop()
            
        with st.expander("Clique para Diagnosticar Colunas Lidas do Excel", expanded=True):
            st.write("**Colunas em `db_Cidades_Atendimento.xlsx`:**", df_cidades_ref.columns.tolist())
            st.write("**Colunas em `db_Custo_Padrão.xlsx`:**", df_custo_ref.columns.tolist())

        try:
            df_calc = st.session_state.df_calculado.copy()
            df_calc.columns = df_calc.columns.str.strip().str.upper()
            
            # --- AJUSTE CRÍTICO AQUI ---
            # O código agora procura pela coluna 'JAMEF FILIAL ATENDIMENTO'
            colunas_cidades_necessarias = ['CIDADE', 'UF', 'JAMEF FILIAL ATENDIMENTO', 'CAP_INT']
            
            # 1. Cruzamento para achar FILIAL e CAP_INT
            df_enriquecido = pd.merge(df_calc, df_cidades_ref[colunas_cidades_necessarias],
                                      left_on=['CIDADE DESTINO', 'UF'], right_on=['CIDADE', 'UF'], how='left')

            # 2. Definição se é CAPITAL ou INTERIOR
            df_enriquecido['REGIAO_CALC'] = np.where(df_enriquecido['CAP_INT'] == 'C', 'CAPITAL', 'INTERIOR')

            # 3. Cria Rota
            origem = st.session_state.params["sigla_origem"]
            # Usa a coluna correta para criar a rota
            df_enriquecido['ROTA_CALC'] = origem + '-' + df_enriquecido['JAMEF FILIAL ATENDIMENTO']
            
            # 4. Cruzamento para achar Custo
            df_final_custo = pd.merge(df_enriquecido, df_custo_ref, left_on='ROTA_CALC', right_on='ROTA', how='left')

            # 5. Loop de Cálculo
            # ... (o resto da lógica de cálculo permanece a mesma)
            custos_totais = []
            for idx, row in df_final_custo.iterrows():
                if pd.isna(row.get('PM')):
                    custos_totais.append(0.0)
                    continue
                peso_real = float(row.get('PESO REAL', 0)); valor_merc = float(row.get('VALOR MERCADORIA', 0))
                regiao = str(row.get('REGIAO_CALC')); pm = float(row.get('PM', 0))
                peso_calculo = max(peso_real, pm)
                
                if regiao == 'CAPITAL':
                    custo_kg = float(row.get('R$_CAPITAL', 0)); perc_nf = float(row.get('%_CAPITAL', 0))
                else:
                    custo_kg = float(row.get('R$_INTERIOR', 0)); perc_nf = float(row.get('%_INTERIOR', 0))
                
                custo_peso = peso_calculo * custo_kg
                custo_var = valor_merc * perc_nf 
                custos_totais.append(custo_peso + custo_var)

            df_final_custo['CUSTO_TOTAL'] = custos_totais
            st.session_state.df_calculado = df_final_custo
            
            st.write("### Tabela de Resultados")
            st.dataframe(df_final_custo)

        except KeyError as e:
            st.error(f"ERRO DE COLUNA: A coluna {e} não foi encontrada.")
            st.info("O nome da coluna no arquivo Excel pode estar diferente do esperado. Verifique a lista de colunas no quadro de diagnóstico acima.")
        
    elif tela_atual == "PASSO_5":
        # ... (código do passo 5)
        st.header("Passo 5: Resumo Financeiro")
