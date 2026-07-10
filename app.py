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
# 3. LEITURA E PREPARAÇÃO DOS DADOS
# ==========================================
@st.cache_data
def carregar_arquivos():
    try:
        df_cidades = pd.read_excel("db_Cidades_Atendimento.xlsx")
        df_custo = pd.read_excel("db_Custo_Padrão.xlsx")
        
        # Apenas tira espaços em branco nas pontas e deixa em maiúsculo
        df_cidades.columns = df_cidades.columns.astype(str).str.strip().str.upper()
        df_custo.columns = df_custo.columns.astype(str).str.strip().str.upper()
        
        # Garante que as cidades e UFs estejam sem espaços nas pontas
        if 'CIDADE' in df_cidades.columns:
            df_cidades['CIDADE'] = df_cidades['CIDADE'].astype(str).str.strip().str.upper()
        if 'UF' in df_cidades.columns:
            df_cidades['UF'] = df_cidades['UF'].astype(str).str.strip().str.upper()
            
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
        
        if st.button("💡 Usar Dados de Teste"):
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
            # Padroniza as colunas do arquivo subido para ficar igual ao mock
            df_up.columns = df_up.columns.astype(str).str.strip().str.upper()
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
        
        df_calc = st.session_state.df_usuario.copy()
        
        fretes = []
        for idx, row in df_calc.iterrows():
            peso = max(float(row.get('PESO REAL', 0)), float(row.get('PESO CUBADO', 0)))
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
            st.error("Erro ao carregar arquivos de Excel. Verifique se db_Cidades_Atendimento.xlsx e db_Custo_Padrão.xlsx estão no repositório com os nomes corretos.")
            st.stop()
            
        df_calc = st.session_state.df_calculado.copy()
        
        # Limpeza das chaves de cruzamento do arquivo do usuário
        if 'CIDADE DESTINO' in df_calc.columns:
            df_calc['CIDADE DESTINO'] = df_calc['CIDADE DESTINO'].astype(str).str.strip().str.upper()
        if 'UF' in df_calc.columns:
            df_calc['UF'] = df_calc['UF'].astype(str).str.strip().str.upper()

        # 1. Cruzamento para achar a FILIAL_ATENDIMENTO e CAP_INT (Baseado no seu print)
        df_enriquecido = pd.merge(df_calc, df_cidades_ref[['CIDADE', 'UF', 'FILIAL_ATENDIMENTO', 'CAP_INT']],
                                  left_on=['CIDADE DESTINO', 'UF'], right_on=['CIDADE', 'UF'], how='left')

        # 2. Definição se é CAPITAL ou INTERIOR
        # Se na coluna CAP_INT tiver 'C', é CAPITAL, senão INTERIOR
        df_enriquecido['REGIAO_CALC'] = np.where(df_enriquecido['CAP_INT'].astype(str).str.strip().str.upper() == 'C', 'CAPITAL', 'INTERIOR')

        # 3. Cria Rota: Origem do parametro + Filial Atendimento
        origem = st.session_state.params["sigla_origem"]
        df_enriquecido['ROTA_CALC'] = origem + '-' + df_enriquecido['FILIAL_ATENDIMENTO'].astype(str)
        
        # 4. Cruzamento para achar o Custo na coluna 'ROTA' (Baseado no seu print)
        df_final_custo = pd.merge(df_enriquecido, df_custo_ref, left_on='ROTA_CALC', right_on='ROTA', how='left')

        # 5. Loop de Cálculo Matemático
        custos_totais = []
        logs_calculo = [] 
        
        for idx, row in df_final_custo.iterrows():
            # Se não encontrou o PM, é porque a Rota não bateu
            if pd.isna(row.get('PM')): 
                custos_totais.append(0.0)
                logs_calculo.append(f"❌ Rota {row.get('ROTA_CALC')} não encontrada")
                continue

            peso_real = float(row.get('PESO REAL', 0))
            valor_merc = float(row.get('VALOR MERCADORIA', 0))
            regiao = str(row.get('REGIAO_CALC'))
            pm = float(row.get('PM', 0))
            
            # Validação do Peso Mínimo
            peso_calculo = max(peso_real, pm)
            
            # Condicionais Capital / Interior (Lendo as colunas exatas do print)
            if regiao == 'CAPITAL':
                custo_kg = float(row.get('R$_CAPITAL', 0))
                perc_nf = float(row.get('%_CAPITAL', 0))
            else:
                custo_kg = float(row.get('R$_INTERIOR', 0))
                perc_nf = float(row.get('%_INTERIOR', 0))
                
            # O Excel geralmente lê 0.15 como 0.15%. Por isso dividimos por 100 na hora de aplicar sobre a NF.
            custo_peso = peso_calculo * custo_kg
            custo_var = valor_merc * (perc_nf / 100.0) 
            custo_total = custo_peso + custo_var
            
            custos_totais.append(custo_total)
            logs_calculo.append(f"✅ {regiao} | PM usado: {pm} | Peso Calc={peso_calculo}kg * R${custo_kg} + R${valor_merc} * {perc_nf}%")

        df_final_custo['CUSTO_TOTAL'] = custos_totais
        df_final_custo['LOG_VALIDACAO'] = logs_calculo
        st.session_state.df_calculado = df_final_custo
        
        st.write("### Tabela de Validação de Racional")
        
        # Seleciona as colunas para mostrar de forma organizada
        colunas_mostrar = ['CIDADE DESTINO', 'UF', 'FILIAL_ATENDIMENTO', 'CAP_INT', 'REGIAO_CALC', 'ROTA_CALC', 'PESO REAL', 'CUSTO_TOTAL', 'LOG_VALIDACAO']
        st.dataframe(df_final_custo[[c for c in colunas_mostrar if c in df_final_custo.columns]])

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
        
        st.dataframe(df_final[['CIDADE DESTINO', 'UF', 'FRETE_SIMULADO', 'CUSTO_TOTAL']])
        
        if st.button("Reiniciar Simulação"):
            st.session_state.tela_atual = "PASSO_1"
            st.rerun()
