import streamlit as st
import pandas as pd
import numpy as np
import os

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
        df_cidades = pd.read_csv("CIDADES.csv", sep=None, engine='python', encoding='latin1')
        df_custo = pd.read_csv("CUSTOS.csv", sep=None, engine='python', encoding='latin1')
        return df_cidades, df_custo
    except Exception as e:
        return None, None

df_cidades_ref, df_custo_ref = carregar_arquivos()

# ==========================================
# 4. FLUXO DA APLICAÇÃO
# ==========================================
if not st.session_state.get("autenticado", False):
    st.title("Acesso ao Simulador (Modo Validação)")
    if st.button("Entrar como Admin"):
        st.session_state.autenticado = True
        st.session_state.tela_atual = "PASSO_1"
        st.rerun()
else:
    try:
        st.sidebar.title("Navegação")
        if st.sidebar.button("Sair e Reiniciar"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

        tela_atual = st.session_state.get("tela_atual", "PASSO_1")

        if tela_atual == "PASSO_1":
            st.header("Passo 1: Parâmetros")
            cidade_sel = st.selectbox("Selecione a Origem", list(origens_dict.keys()), index=1)
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
            
            if st.session_state.df_usuario is not None:
                st.dataframe(st.session_state.df_usuario.head())
            if st.button("Avançar para Cálculo", disabled=st.session_state.df_usuario is None):
                st.session_state.tela_atual = "PASSO_4" # Pula o Passo 3 (Mock) e vai direto pro custo
                st.session_state.df_calculado = st.session_state.df_usuario.copy()
                st.rerun()

        elif tela_atual == "PASSO_4":
            st.header("Passo 4: Validação do Racional de Custo")
            
            if df_cidades_ref is None or df_custo_ref is None:
                st.error("Arquivos de referência (CIDADES.csv, CUSTOS.csv) não encontrados.")
                st.stop()
            
            df_calc = st.session_state.df_calculado.copy()
            
            # Limpeza e Padronização
            df_calc.columns = [col.strip().upper() for col in df_calc.columns]
            df_cidades_ref.columns = [col.strip().upper() for col in df_cidades_ref.columns]
            df_custo_ref.columns = [col.strip().upper() for col in df_custo_ref.columns]

            # 1. Cruzamento para achar a FILIAL e o TIPO DE REGIÃO
            df_enriquecido = pd.merge(
                df_calc, 
                df_cidades_ref[['CIDADE', 'UF', 'JAMEF', 'CAP_INT']], # USA A COLUNA 'JAMEF'
                left_on=['CIDADE DESTINO', 'UF'], 
                right_on=['CIDADE', 'UF'], 
                how='left'
            )
            
            df_enriquecido['REGIAO_CALC'] = np.where(df_enriquecido['CAP_INT'] == 'C', 'CAPITAL', 'INTERIOR')
            
            # 2. Cria a ROTA_CALC (sem hífen)
            origem = st.session_state.params["sigla_origem"]
            df_enriquecido['ROTA_CALC'] = origem + df_enriquecido['JAMEF'].astype(str)
            
            # 3. Cruzamento para achar o Custo
            df_final_custo = pd.merge(
                df_enriquecido, 
                df_custo_ref, 
                left_on='ROTA_CALC', 
                right_on='ROTA', 
                how='left'
            )

            # 4. Loop de Cálculo
            custos_totais = []
            logs = []
            
            for idx, row in df_final_custo.iterrows():
                if pd.isna(row.get('PM')):
                    custos_totais.append(0.0)
                    logs.append(f"❌ Rota {row.get('ROTA_CALC')} não encontrada")
                    continue
                
                peso_real = float(row.get('PESO REAL', 0))
                valor_merc = float(row.get('VALOR MERCADORIA', 0))
                regiao = str(row.get('REGIAO_CALC'))
                pm = float(row.get('PM', 0))
                
                peso_calculo = max(peso_real, pm)
                
                if regiao == 'CAPITAL':
                    custo_kg = float(str(row.get('R$_CAPITAL', '0')).replace(',', '.'))
                    perc_nf_str = str(row.get('%_CAPITAL', '0')).replace('%', '').replace(',', '.')
                    perc_nf = float(perc_nf_str) / 100.0
                else:
                    custo_kg = float(str(row.get('R$_INTERIOR', '0')).replace(',', '.'))
                    perc_nf_str = str(row.get('%_INTERIOR', '0')).replace('%', '').replace(',', '.')
                    perc_nf = float(perc_nf_str) / 100.0
                
                custo_peso = peso_calculo * custo_kg
                custo_var = valor_merc * perc_nf
                custos_totais.append(custo_peso + custo_var)
                logs.append(f"✅ {regiao} | PM: {pm} | R$/kg: {custo_kg} | %: {perc_nf*100:.2f}%")

            df_final_custo['CUSTO_TOTAL'] = custos_totais
            df_final_custo['DIAGNÓSTICO_CALCULO'] = logs
            
            st.write("### Tabela de Validação")
            st.dataframe(df_final_custo[[
                'CIDADE DESTINO', 'UF', 'JAMEF', 'CAP_INT', 'ROTA_CALC', 'PESO REAL', 'CUSTO_TOTAL', 'DIAGNÓSTICO_CALCULO'
            ]])

    except Exception as e:
        st.error(f"Ocorreu um erro durante a execução: {e}")
        st.exception(e)
