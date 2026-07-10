import streamlit as st
import pandas as pd
import numpy as np

# ==========================================
# 1. CONFIGURAÇÃO BÁSICA
# ==========================================
st.set_page_config(page_title="Validação de Racional - Simulador", layout="wide")

origens_dict = {
    "Curitiba - PR (CWB)": "CWB", "São Paulo - SP (SAO)": "SAO", "Belo Horizonte - MG (BHZ)": "BHZ",
    "Goiania - GO (GYN)": "GYN", "Uberlândia - MG (UDI)": "UDI", "Divinópolis - MG (DIV)": "DIV",
    "Belém - PA (BEL)": "BEL", "Fortaleza - CE (FOR)": "FOR", "Feira de Santana - BA (FES)": "FES",
    "Salvador - BA (SSA)": "SSA", "Florianópolis - SC (FLN)": "FLN", "Brasilia - DF (BSB)": "BSB",
    "Recife - PE (REC)": "REC", "São Luis - MA (SLZ)": "SLZ", "Natal - RN (NAT)": "NAT",
    "Teresina - PI (THE)": "THE", "Porto Alegre - RS (POA)": "POA", "Campinas - SP (CPQ)": "CPQ",
    "Maceio - AL (MCZ)": "MCZ", "Rio de Janeiro - RJ (RIO)": "RIO" # Lista reduzida para focar no teste
}

# ==========================================
# 2. INICIALIZAÇÃO DE SESSÃO
# ==========================================
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False
if "tela_atual" not in st.session_state:
    st.session_state.tela_atual = "LOGIN"
if "params" not in st.session_state:
    st.session_state.params = {"sigla_origem": "CWB", "desconto": 0.0, "margem_alvo": 15.0}
if "df_usuario" not in st.session_state:
    st.session_state.df_usuario = None
if "df_calculado" not in st.session_state:
    st.session_state.df_calculado = None

# ==========================================
# 3. FUNÇÕES DE DADOS (LIMPEZA E CARREGAMENTO)
# ==========================================
def padronizar_colunas(df):
    if df is None: return None
    df.columns = (df.columns.astype(str).str.strip().str.upper()
                  .str.replace(' ', '_', regex=False)
                  .str.replace('/', '_', regex=False)
                  .str.replace('.', '_', regex=False)
                  .str.normalize('NFKD').str.encode('ascii', errors='ignore').str.decode('utf-8'))
    return df

@st.cache_data
def carregar_arquivos():
    try:
        df_cidades = pd.read_excel("db_Cidades_Atendimento.xlsx")
        df_custo = pd.read_excel("db_Custo_Padrão.xlsx")
        
        df_cidades = padronizar_colunas(df_cidades)
        df_custo = padronizar_colunas(df_custo)
        
        # Limpa os dados das colunas chave
        if 'CIDADE' in df_cidades.columns:
            df_cidades['CIDADE'] = df_cidades['CIDADE'].astype(str).str.strip().str.upper()
        if 'UF' in df_cidades.columns:
            df_cidades['UF'] = df_cidades['UF'].astype(str).str.strip().str.upper()

        # REGRA CAPITAL / INTERIOR (Lendo da coluna C_I do Excel)
        if 'C__I' in df_cidades.columns:
            df_cidades['TIPO_REGIAO_CALC'] = np.where(df_cidades['C__I'].str.contains('C', case=False, na=False), 'CAPITAL', 'INTERIOR')
        else:
            df_cidades['TIPO_REGIAO_CALC'] = 'INTERIOR' # Fallback caso a coluna mude de nome
            
        return df_cidades, df_custo
    except Exception as e:
        return None, None

df_cidades_ref, df_custo_ref = carregar_arquivos()

# ==========================================
# 4. TELA DE LOGIN SIMPLES
# ==========================================
if st.session_state.tela_atual == "LOGIN":
    st.title("Acesso ao Simulador (Modo Validação)")
    usuario = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")
    
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
elif st.session_state.autenticado:
    st.sidebar.title("Navegação")
    st.sidebar.write(f"**Etapa Atual:** {st.session_state.tela_atual}")
    if st.sidebar.button("Sair"):
        st.session_state.autenticado = False
        st.session_state.tela_atual = "LOGIN"
        st.rerun()

    # --- PASSO 1: PARÂMETROS ---
    if st.session_state.tela_atual == "PASSO_1":
        st.header("Passo 1: Parâmetros Comerciais")
        
        cidade_sel = st.selectbox("Selecione a Origem", list(origens_dict.keys()))
        sigla_sel = origens_dict[cidade_sel]
        st.write(f"**Sigla de Origem Base para Custo:** {sigla_sel}")
        
        desc_sel = st.number_input("Desconto Comercial (%)", value=0.0)
        margem_sel = st.number_input("Margem Alvo (%)", value=15.0)

        if st.button("Avançar para Passo 2"):
            st.session_state.params = {"sigla_origem": sigla_sel, "desconto": desc_sel, "margem_alvo": margem_sel}
            st.session_state.tela_atual = "PASSO_2"
            st.rerun()

    # --- PASSO 2: UPLOAD ---
    elif st.session_state.tela_atual == "PASSO_2":
        st.header("Passo 2: Dados de Embarque")
        
        if st.button("💡 Usar Dados de Teste (Palmas, Maceio, Rio Largo)"):
            st.session_state.df_usuario = pd.DataFrame({
                "CIDADE DESTINO": ["PALMAS", "MACEIO", "RIO LARGO"], 
                "UF": ["TO", "AL", "AL"],
                "PESO REAL": [84.00, 234.00, 93.00], 
                "PESO CUBADO": [193.08, 459.03, 202.44], 
                "VALOR MERCADORIA": [9178.41, 17853.74, 9620.00]
            })
            st.success("Dados carregados!")
            
        uploaded_file = st.file_uploader("Ou suba um arquivo Excel/CSV", type=["csv", "xlsx"])
        if uploaded_file:
            df_up = pd.read_excel(uploaded_file) if uploaded_file.name.endswith('.xlsx') else pd.read_csv(uploaded_file)
            st.session_state.df_usuario = df_up
            st.success("Arquivo lido com sucesso!")

        if st.session_state.df_usuario is not None:
            st.dataframe(st.session_state.df_usuario.head())
            
        if st.button("Avançar para Passo 3", disabled=st.session_state.df_usuario is None):
            st.session_state.tela_atual = "PASSO_3"
            st.rerun()

    # --- PASSO 3: FRETE ESTIMADO ---
    elif st.session_state.tela_atual == "PASSO_3":
        st.header("Passo 3: Frete Base (Mock)")
        
        df_calc = padronizar_colunas(st.session_state.df_usuario.copy())
        
        # Garante que as colunas necessárias existam
        if 'PESO_REAL' not in df_calc.columns: df_calc['PESO_REAL'] = 0.0
        if 'PESO_CUBADO' not in df_calc.columns: df_calc['PESO_CUBADO'] = 0.0
        
        fretes = []
        for idx, row in df_calc.iterrows():
            peso = max(float(row['PESO_REAL']), float(row['PESO_CUBADO']))
            frete_bruto = 150.0 + (peso * 1.5)
            fretes.append(frete_bruto * (1 - (st.session_state.params["desconto"] / 100.0)))
            
        df_calc["FRETE_SIMULADO"] = fretes
        st.session_state.df_calculado = df_calc
        
        st.dataframe(df_calc)
        
        if st.button("Avançar para Passo 4 (Custos Reais)"):
            st.session_state.tela_atual = "PASSO_4"
            st.rerun()

    # --- PASSO 4: CÁLCULO DE CUSTO ---
    elif st.session_state.tela_atual == "PASSO_4":
        st.header("Passo 4: Validação do Racional de Custo")
        
        if df_cidades_ref is None or df_custo_ref is None:
            st.error("Erro ao carregar arquivos de Excel. Verifique se db_Cidades_Atendimento.xlsx e db_Custo_Padrão.xlsx estão no repositório.")
            st.stop()
            
        df_calc = st.session_state.df_calculado.copy()
        
        # Limpeza para cruzamento
        df_calc['CIDADE_DESTINO'] = df_calc['CIDADE_DESTINO'].astype(str).str.strip().str.upper()
        df_calc['UF'] = df_calc['UF'].astype(str).str.strip().str.upper()

        # 1. Encontra Filial e Região
        df_enriquecido = pd.merge(df_calc, df_cidades_ref[['CIDADE', 'UF', 'FILIAL_ATENDIMENTO', 'TIPO_REGIAO_CALC']],
                                  left_on=['CIDADE_DESTINO', 'UF'], right_on=['CIDADE', 'UF'], how='left')

        # 2. Cria Rota
        origem = st.session_state.params["sigla_origem"]
        df_enriquecido['COD_ROTA'] = origem + '-' + df_enriquecido['FILIAL_ATENDIMENTO']
        
        # 3. Busca Custo
        df_final_custo = pd.merge(df_enriquecido, df_custo_ref, on='COD_ROTA', how='left')

        # 4. Cálculo
        custos_totais = []
        logs_calculo = [] # Para visualizar como a matemática foi feita
        
        for idx, row in df_final_custo.iterrows():
            if pd.isna(row.get('PM')): 
                custos_totais.append(0.0)
                logs_calculo.append("Rota não encontrada")
                continue

            peso_real = float(row.get('PESO_REAL', 0))
            valor_merc = float(row.get('VALOR_MERCADORIA', 0))
            regiao = str(row.get('TIPO_REGIAO_CALC', 'INTERIOR')).upper()
            pm = float(row.get('PM', 0))
            
            peso_calculo = max(peso_real, pm)
            
            if regiao == 'CAPITAL':
                custo_kg = float(row.get('CUSTO_KG_CAP', 0))
                perc_nf = float(row.get('PERC_NF_CAP', 0))
            else:
                custo_kg = float(row.get('CUSTO_KG_INT', 0))
                perc_nf = float(row.get('PERC_NF_INT', 0))
                
            custo_fixo = peso_calculo * custo_kg
            custo_var = valor_merc * (perc_nf / 100.0)
            custo_total = custo_fixo + custo_var
            
            custos_totais.append(custo_total)
            logs_calculo.append(f"Região: {regiao} | PM: {pm} | Peso Calc: {peso_calculo} | R$/kg: {custo_kg} | Var: {perc_nf}% | Fixo: R${custo_fixo:.2f} | Var: R${custo_var:.2f}")

        df_final_custo['CUSTO_TOTAL'] = custos_totais
        df_final_custo['LOG_CALCULO'] = logs_calculo
        st.session_state.df_calculado = df_final_custo
        
        st.write("### Tabela Analítica (Resultados)")
        colunas_mostrar = ['CIDADE_DESTINO', 'UF', 'FILIAL_ATENDIMENTO', 'TIPO_REGIAO_CALC', 'COD_ROTA', 'PESO_REAL', 'CUSTO_TOTAL', 'LOG_CALCULO']
        colunas_presentes = [c for c in colunas_mostrar if c in df_final_custo.columns]
        st.dataframe(df_final_custo[colunas_presentes])

        if st.button("Avançar para Passo 5 (Dashboard)"):
            st.session_state.tela_atual = "PASSO_5"
            st.rerun()

    # --- PASSO 5: DASHBOARD ---
    elif st.session_state.tela_atual == "PASSO_5":
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
        
        st.dataframe(df_final[['CIDADE_DESTINO', 'UF', 'FRETE_SIMULADO', 'CUSTO_TOTAL']])
        
        if st.button("Reiniciar Simulação"):
            st.session_state.tela_atual = "PASSO_1"
            st.rerun()
