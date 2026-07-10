import pandas as pd
import streamlit as st

from repositories.file_repository import FileRepository
from services.cost_service import CostService
from utils.formatting import format_currency, format_number


st.set_page_config(
    page_title="Simulador de Custos",
    layout="wide",
)

st.title("Validação do racional de custo")

repository = FileRepository(
    cities_path="data/CIDADES.csv",
    costs_path="data/CUSTOS.csv",
)
cost_service = CostService()


@st.cache_data(show_spinner=False)
def load_reference_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    cities = repository.load_cities()
    costs = repository.load_costs()
    return cities, costs


with st.sidebar:
    st.subheader("Controles")
    if st.button("Limpar cache"):
        st.cache_data.clear()
        st.rerun()


try:
    cities_df, costs_df = load_reference_data()
except Exception as error:
    st.error("Falha ao carregar os arquivos de referência.")
    st.exception(error)
    st.stop()


with st.expander("Visualizar diagnóstico dos arquivos"):
    left, right = st.columns(2)

    with left:
        st.write("### CIDADES.csv")
        st.write(f"Linhas: {len(cities_df):,}")
        st.code("\n".join(cities_df.columns))
        st.dataframe(cities_df.head(10), use_container_width=True)

    with right:
        st.write("### CUSTOS.csv")
        st.write(f"Linhas: {len(costs_df):,}")
        st.code("\n".join(costs_df.columns))
        st.dataframe(costs_df.head(10), use_container_width=True)


origins = repository.get_available_origins(costs_df)

with st.form("shipment_form"):
    st.subheader("Dados do embarque")

    col1, col2, col3 = st.columns(3)

    with col1:
        origin = st.selectbox("Origem", origins)
        destination_city = st.text_input("Cidade de destino", value="MACEIÓ")
        destination_state = st.text_input("UF de destino", value="AL", max_chars=2)

    with col2:
        real_weight = st.number_input(
            "Peso real",
            min_value=0.0,
            value=84.0,
            step=1.0,
        )
        cubed_weight = st.number_input(
            "Peso cubado",
            min_value=0.0,
            value=193.08,
            step=1.0,
        )

    with col3:
        merchandise_value = st.number_input(
            "Valor da mercadoria",
            min_value=0.0,
            value=9178.41,
            step=100.0,
        )

    submitted = st.form_submit_button(
        "Calcular custo",
        type="primary",
    )


if submitted:
    shipment_df = pd.DataFrame(
        [
            {
                "CIDADE DESTINO": destination_city,
                "UF": destination_state,
                "PESO REAL": real_weight,
                "PESO CUBADO": cubed_weight,
                "VALOR MERCADORIA": merchandise_value,
                "ORIGEM": origin,
            }
        ]
    )

    result_df = cost_service.calculate_batch(
        shipments=shipment_df,
        cities=cities_df,
        costs=costs_df,
    )

    result = result_df.iloc[0]

    if result["STATUS"] == "OK":
        st.success("Cálculo realizado.")

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Peso de custeio", f"{format_number(result['PESO_CUSTEIO'])} kg")
        c2.metric("Custo por peso", format_currency(result["CUSTO_PESO"]))
        c3.metric("Custo variável", format_currency(result["CUSTO_VARIAVEL"]))
        c4.metric("Custo total", format_currency(result["CUSTO_TOTAL"]))
    else:
        st.error(result["MENSAGEM"])

    st.subheader("Detalhamento do cruzamento")

    display_columns = [
        "ORIGEM",
        "CIDADE DESTINO",
        "UF",
        "JAMEF",
        "CAP_INT",
        "REGIAO_CALC",
        "ROTA_CALC",
        "PM",
        "R$_CAPITAL",
        "%_CAPITAL",
        "R$_INTERIOR",
        "%_INTERIOR",
        "PESO REAL",
        "PESO CUBADO",
        "PESO_CUSTEIO",
        "CUSTO_KG",
        "PERCENTUAL_VARIAVEL",
        "CUSTO_PESO",
        "CUSTO_VARIAVEL",
        "CUSTO_TOTAL",
        "STATUS",
        "MENSAGEM",
    ]

    existing_columns = [
        column for column in display_columns
        if column in result_df.columns
    ]

    st.dataframe(
        result_df[existing_columns],
        use_container_width=True,
    )
