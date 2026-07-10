import pandas as pd
import streamlit as st

from repositories.file_repository import FileRepository
from services.cost_service import CostService
from services.export_service import ExportService
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
export_service = ExportService()


@st.cache_data(show_spinner=False)
def load_reference_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    cities = repository.load_cities()
    costs = repository.load_costs()
    return cities, costs


with st.sidebar:
    st.subheader("Controles")
    if st.button("Limpar cache"):
        st.cache_data.clear()
        st.session_state.pop("batch_result", None)
        st.session_state.pop("batch_summary", None)
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

manual_tab, batch_tab = st.tabs(
    [
        "Cálculo manual",
        "Cálculo em lote",
    ]
)


with manual_tab:
    with st.form("shipment_form"):
        st.subheader("Dados do embarque")

        col1, col2, col3 = st.columns(3)

        with col1:
            origin = st.selectbox("Origem", origins)
            destination_city = st.text_input(
                "Cidade de destino",
                value="MACEIÓ",
            )
            destination_state = st.text_input(
                "UF de destino",
                value="AL",
                max_chars=2,
            )

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
            c1.metric(
                "Peso de custeio",
                f"{format_number(result['PESO_CUSTEIO'])} kg",
            )
            c2.metric(
                "Custo por peso",
                format_currency(result["CUSTO_PESO"]),
            )
            c3.metric(
                "Custo variável",
                format_currency(result["CUSTO_VARIAVEL"]),
            )
            c4.metric(
                "Custo total",
                format_currency(result["CUSTO_TOTAL"]),
            )
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
            column
            for column in display_columns
            if column in result_df.columns
        ]

        st.dataframe(
            result_df[existing_columns],
            use_container_width=True,
        )


with batch_tab:
    st.subheader("Cálculo de volumetria")

    st.write(
        "Envie uma planilha XLSX com a aba `Volumetria` "
        "ou um arquivo CSV com as colunas obrigatórias."
    )

    uploaded_file = st.file_uploader(
        "Selecionar arquivo de volumetria",
        type=["xlsx", "csv"],
        key="batch_upload",
    )

    if uploaded_file is not None:
        try:
            shipment_batch = repository.load_uploaded_shipments(
                uploaded_file=uploaded_file,
                file_name=uploaded_file.name,
            )

            st.success(
                f"Arquivo carregado com {len(shipment_batch):,} embarques."
            )

            st.write("### Prévia da volumetria")
            st.dataframe(
                shipment_batch.head(20),
                use_container_width=True,
            )

            calculate_batch = st.button(
                "Calcular volumetria",
                type="primary",
                key="calculate_batch",
            )

            if calculate_batch:
                with st.spinner(
                    "Calculando os custos da volumetria..."
                ):
                    batch_result = cost_service.calculate_batch(
                        shipments=shipment_batch,
                        cities=cities_df,
                        costs=costs_df,
                    )

                    batch_summary = cost_service.create_summary(
                        batch_result
                    )

                st.session_state["batch_result"] = batch_result
                st.session_state["batch_summary"] = batch_summary

        except Exception as error:
            st.error("Não foi possível processar o arquivo.")
            st.exception(error)

    if "batch_result" in st.session_state:
        batch_result = st.session_state["batch_result"]
        batch_summary = st.session_state["batch_summary"]
        summary = batch_summary.iloc[0]

        st.write("## Resumo da simulação")

        row1_col1, row1_col2, row1_col3 = st.columns(3)
        row1_col1.metric(
            "Embarques",
            f"{int(summary['QTD_EMBARQUES']):,}",
        )
        row1_col2.metric(
            "Calculados",
            f"{int(summary['QTD_CALCULADOS']):,}",
        )
        row1_col3.metric(
            "Com erro",
            f"{int(summary['QTD_ERROS']):,}",
        )

        row2_col1, row2_col2, row2_col3 = st.columns(3)
        row2_col1.metric(
            "Peso real",
            f"{format_number(summary['PESO_REAL_TOTAL'])} kg",
        )
        row2_col2.metric(
            "Peso de custeio",
            f"{format_number(summary['PESO_CUSTEIO_TOTAL'])} kg",
        )
        row2_col3.metric(
            "Mercadoria",
            format_currency(summary["VALOR_MERCADORIA_TOTAL"]),
        )

        row3_col1, row3_col2, row3_col3 = st.columns(3)
        row3_col1.metric(
            "Custo por peso",
            format_currency(summary["CUSTO_PESO_TOTAL"]),
        )
        row3_col2.metric(
            "Custo variável",
            format_currency(summary["CUSTO_VARIAVEL_TOTAL"]),
        )
        row3_col3.metric(
            "Custo total",
            format_currency(summary["CUSTO_TOTAL"]),
        )

        st.write("## Resultado detalhado")

        status_filter = st.multiselect(
            "Filtrar por status",
            options=["OK", "ERRO"],
            default=["OK", "ERRO"],
        )

        filtered_result = batch_result[
            batch_result["STATUS"].isin(status_filter)
        ].copy()

        st.dataframe(
            filtered_result,
            use_container_width=True,
            hide_index=True,
        )

        errors = batch_result[
            batch_result["STATUS"] == "ERRO"
        ]

        if not errors.empty:
            st.warning(
                f"{len(errors):,} embarque(s) não foram calculados. "
                "Consulte a coluna MENSAGEM."
            )

        excel_output = export_service.to_excel(
            result_dataframe=batch_result,
            summary_dataframe=batch_summary,
        )

        st.download_button(
            label="Baixar resultado em Excel",
            data=excel_output,
            file_name="resultado_simulacao_custos.xlsx",
            mime=(
                "application/vnd.openxmlformats-officedocument."
                "spreadsheetml.sheet"
            ),
        )
