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
# 3. LEITURA DOS ARQUIVOS CSV
# ==========================================
@st.cache_data
def carregar_arquivos():
    try:
        # Tenta ler como latin1 (padrão Excel BR) ou utf-8
        try:
            df_cidades = pd.read_csv("CIDADES.csv", sep=';', encoding='latin1')
            df_custo = pd.read_csv("CUSTOS.csv", sep=';', encoding='latin1')
        except:
            df_cidades = pd.read_csv("CIDADES.csv", sep=';', encoding='utf-8')
            df_custo = pd.read_csv("CUSTOS.csv", sep=';', encoding='utf-8')
            
        return df_cidades, df_custo
    except Exception as e:
        return None, None

df_cidades_ref, df_custo_ref = carregar_arquivos()

# ==========================================
# 4. NORMALIZAÇÃO DE TEXTO (REMOVER ACENTOS)
# ==========================================
def normalizar_texto(coluna):
    """Remove acentos, espaços extras e deixa tudo maiúsculo"""
    return coluna.astype(str).str.normalize('NFKD').str.encode('ascii', errors='ignore').str.decode('utf-8').str.strip().str.upper()

# ==========================================
# 5. FLUXO DA APLICAÇÃO
# ==========================================
if not st.session_state.get("autenticado", False):
    st.title("Acesso ao Simulador (Modo Validação)")
    if st.button("Entrar como Admin"):
        st.session_state.autenticado = True
        st.session_state.tela_atual = "PASSO_1"
        st.experimental_rerun()
else:
    try:
        st.sidebar.title("Navegação")
        if st.sidebar.button("Sair e Reiniciar"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.experimental_rerun()

        tela_atual = st.session_state.get("tela_atual", "PASSO_1")

        if tela_atual == "PASSO_1":
            st.header("Passo 1: Parâmetros")
            cidade_sel = st.selectbox("Selecione a Origem", list(origens_dict.keys()), index=1)
            if st.button("Avançar"):
                st.session_state.params["sigla_origem"] = origens_dict[cidade_sel]
                st.session_state.tela_atual = "PASSO_2"
                st.experimental_rerun()

        elif tela_atual == "PASSO_2":
            st.header("Passo 2: Dados de Embarque")
            if st.button("💡 Usar Dados de Teste"):
                st.session_state.df_usuario = pd.DataFrame({
                    "CIDADE DESTINO": ["PALMAS", "MACEIÓ", "RIO LARGO"], # Coloquei MACEIÓ com acento para provar que a limpeza funciona
                    "UF": ["TO", "AL", "AL"],
                    "PESO REAL": [84.00, 234.00, 93.00], 
                    "PESO CUBADO": [193.08, 459.03, 202.44], 
                    "VALOR MERCADORIA": [9178.41, 17853.74, 9620.00]
                })
            
            if st.session_state.df_usuario is not None:
                st.dataframe(st.session_state.df_usuario.head())
            if st.button("Avançar para Cálculo", disabled=st.session_state.df_usuario is None):
                st.session_state.tela_atual = "PASSO_4"
                st.session_state.df_calculado = st.session_state.df_usuario.copy()
                st.experimental_rerun()

        elif tela_atual == "PASSO_4":
            st.header("Passo 4: Validação do Racional de Custo")
            
            if df_cidades_ref is None or df_custo_ref is None:
                st.error("Arquivos de referência (CIDADES.csv, CUSTOS.csv) não encontrados.")
                st.stop()
            
            # Copia os dados do usuário e das tabelas de referência
            df_calc = st.session_state.df_calculado.copy()
            df_calc.columns = [col.strip().upper() for col in df_calc.columns]
            
            # Limpa os cabeçalhos de referência
            df_cidades_ref.columns = [col.strip().upper() for col in df_cidades_ref.columns]
            df_custo_ref.columns = [col.strip().upper() for col in df_custo_ref.columns]

            # ==============================================================
            # O SEGREDO DO SUCESSO: CRIAR CHAVES DE CRUZAMENTO LIMPAS
            # ==============================================================
            df_calc['CHAVE_CIDADE'] = normalizar_texto(df_calc['CIDADE DESTINO'])
            df_calc['CHAVE_UF'] = normalizar_texto(df_calc['UF'])
            
            df_cidades_ref['CHAVE_CIDADE'] = normalizar_texto(df_cidades_ref['CIDADE'])
            df_cidades_ref['CHAVE_UF'] = normalizar_texto(df_cidades_ref['UF'])

            # 1. Cruzamento para achar a FILIAL e o TIPO DE REGIÃO (Usando as chaves limpas)
            df_enriquecido = pd.merge(
                df_calc, 
                df_cidades_ref[['CHAVE_CIDADE', 'CHAVE_UF', 'JAMEF', 'CAP_INT']], 
                on=['CHAVE_CIDADE', 'CHAVE_UF'], 
                how='left'
            )
            
            # 2. Verifica se houve falha no cruzamento
            linhas_sem_filial = df_enriquecido[df_enriquecido['JAMEF'].isna()]
            if not linhas_sem_filial.empty:
                st.warning(f"⚠️ Atenção: {len(linhas_sem_filial)} cidades não foram encontradas na sua base 'CIDADES.csv'. Verifique a aba abaixo.")
                with st.expander("Ver cidades não encontradas"):
                    st.dataframe(linhas_sem_filial[['CIDADE DESTINO', 'UF']])
            
            # 3. Definições de Rota e Região
            df_enriquecido['REGIAO_CALC'] = np.where(df_enriquecido['CAP_INT'].astype(str).str.strip().str.upper() == 'C', 'CAPITAL', 'INTERIOR')
            
            origem = st.session_state.params["sigla_origem"]
            # Monta a rota e substitui 'nan' caso a filial não tenha sido encontrada
            df_enriquecido['ROTA_CALC'] = origem + df_enriquecido['JAMEF'].astype(str).replace('nan', '')
            
            # 4. Cruzamento para achar o Custo
            df_final_custo = pd.merge(df_enriquecido, df_custo_ref, left_on='ROTA_CALC', right_on='ROTA', how='left')

            # 5. Loop de Cálculo
            custos_totais, logs = [], []
            
            for idx, row in df_final_custo.iterrows():
                # Se não tem Rota, ou PM está vazio
                if pd.isna(row.get('PM')) or row.get('ROTA_CALC') == origem:
                    custos_totais.append(np.nan)
                    logs.append(f"❌ Rota {row.get('ROTA_CALC')} não encontrada no CUSTOS.csv")
                    continue
                
                peso_real = float(row.get('PESO REAL', 0))
                valor_merc = float(row.get('VALOR MERCADORIA', 0))
                regiao = str(row.get('REGIAO_CALC'))
                pm = float(str(row.get('PM', '0')).replace(',', '.'))
                
                peso_calculo = max(peso_real, pm)
                
                if regiao == 'CAPITAL':
                    custo_kg = float(str(row.get('R$_CAPITAL', '0')).replace(',', '.'))
                    perc_nf_str = str(row.get('%_CAPITAL', '0')).replace('%', '').replace(',', '.')
                else:
                    custo_kg = float(str(row.get('R$_INTERIOR', '0')).replace(',', '.'))
                    perc_nf_str = str(row.get('%_INTERIOR', '0')).replace('%', '').replace(',', '.')
                
                perc_nf = float(perc_nf_str) / 100.0 if perc_nf_str else 0.0
                
                custo_peso = peso_calculo * custo_kg
                custo_var = valor_merc * perc_nf
                custos_totais.append(custo_peso + custo_var)
                logs.append(f"✅ {regiao} | Rota: {row.get('ROTA_CALC')} | PM: {pm} | R$/kg: {custo_kg} | %: {perc_nf*100:.2f}%")

            df_final_custo['CUSTO_TOTAL'] = custos_totais
            df_final_custo['DIAGNÓSTICO_CALCULO'] = logs
            
            st.write("### Tabela de Validação")
            st.dataframe(df_final_custo[['CIDADE DESTINO', 'UF', 'JAMEF', 'ROTA_CALC', 'CUSTO_TOTAL', 'DIAGNÓSTICO_CALCULO']])

    except Exception as e:
        st.error(f"Ocorreu um erro durante a execução.")
        st.exception(e)
