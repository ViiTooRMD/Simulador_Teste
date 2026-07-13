import pandas as pd
import streamlit as st

from repositories.file_repository import FileRepository
from repositories.freight_repository import FreightRepository
from services.cost_service import CostService
from services.export_service import ExportService
from services.freight_service import FreightService
from services.simulation_service import SimulationService
from utils.formatting import format_currency, format_number


st.set_page_config(
    page_title="Simulador de Custos e Fretes",
    layout="wide",
)

st.title("Simulador de Custos e Fretes")

file_repository = FileRepository(
    cities_path="data/CIDADES.csv",
    costs_path="data/CUSTOS.csv",
)

freight_repository = FreightRepository(
    freight_table_path="data/TABELA_PADRAO.csv",
)

cost_service = CostService()
freight_service = FreightService()
simulation_service = SimulationService(
    cost_service=cost_service,
    freight_service=freight_service,
)
export_service = ExportService()


@st.cache_data(show_spinner=False)
def load_reference_data() -> tuple[
    pd.DataFrame,
    pd.DataFrame,
    pd.DataFrame,
]:
    cities = file_repository.load_cities()
    costs = file_repository.load_costs()
    freight_table = freight_repository.load_freight_table()

    return cities, costs, freight_table


with st.sidebar:
    st.subheader("Controles")

    if st.button("Limpar cache"):
        st.cache_data.clear()
        st.session_state.pop("batch_result", None)
        st.session_state.pop("batch_summary_cost", None)
        st.session_state.pop("batch_summary_freight", None)
        st.rerun()


try:
    cities_df, costs_df, freight_table_df = load_reference_data()
except Exception as error:
    st.error("Falha ao carregar os arquivos de referência.")
    st.exception(error)
    st.stop()


with st.expander("Visualizar diagnóstico dos arquivos"):
    col1, col2, col3 = st.columns(3)

    with col1:
        st.write("### CIDADES.csv")
        st.write(f"Linhas: {len(cities_df):,}")
        st.code("\n".join(cities_df.columns))
        st.dataframe(cities_df.head(10), use_container_width=True)

    with col2:
        st.write("### CUSTOS.csv")
        st.write(f"Linhas: {len(costs_df):,}")
        st.code("\n".join(costs_df.columns))
        st.dataframe(costs_df.head(10), use_container_width=True)

    with col3:
        st.write("### TABELA_PADRAO.csv")
        st.write(f"Linhas: {len(freight_table_df):,}")
        st.code("\n".join(freight_table_df.columns))
        st.dataframe(
            freight_table_df.head(10),
            use_container_width=True,
        )


origins = file_repository.get_available_origins(costs_df)

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
                value="CURITIBA",
            )
            destination_state = st.text_input(
                "UF de destino",
                value="PR",
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
            "Calcular simulação",
            type="primary",
        )

    if submitted:
        shipment_df = pd.DataFrame(
            [
                {
                    "ID_EMBARQUE": "MANUAL-001",
                    "ORIGEM": origin,
                    "CIDADE DESTINO": destination_city,
                    "UF": destination_state,
                    "PESO REAL": real_weight,
                    "PESO CUBADO": cubed_weight,
                    "VALOR MERCADORIA": merchandise_value,
                }
            ]
        )

        result_df = simulation_service.calculate_batch(
            shipments=shipment_df,
            cities=cities_df,
            costs=costs_df,
            freight_table=freight_table_df,
        )

        result = result_df.iloc[0]

        st.write("## Resultado do custo")

        if result["STATUS_CUSTO"] == "OK":
            st.success("Custo calculado.")

            c1, c2, c3, c4, c5 = st.columns(5)
            c1.metric(
                "Peso base do custo",
                f"{format_number(result['PESO_BASE_CUSTO'])} kg",
            )
            c2.metric(
                "Peso de custeio",
                f"{format_number(result['PESO_CUSTEIO'])} kg",
            )
            c3.metric(
                "Custo por peso",
                format_currency(result["CUSTO_PESO"]),
            )
            c4.metric(
                "Custo variável",
                format_currency(result["CUSTO_VARIAVEL"]),
            )
            c5.metric(
                "Custo total",
                format_currency(result["CUSTO_TOTAL"]),
            )
        else:
            st.error(result["MENSAGEM_CUSTO"])

        st.write("## Resultado do frete")

        if result["STATUS_FRETE"] == "OK":
            st.success("Frete calculado.")

            f1, f2, f3, f4, f5 = st.columns(5)
            f1.metric(
                "Peso tarifado",
                f"{format_number(result['PESO_TARIFADO'])} kg",
            )
            f2.metric(
                "Faixa",
                str(result["FAIXA_PESO"]),
            )
            f3.metric(
                "Frete-peso",
                format_currency(result["FRETE_PESO"]),
            )
            f4.metric(
                "Ad valorem",
                format_currency(result["AD_VALOREM"]),
            )
            f5.metric(
                "Frete parcial",
                format_currency(result["FRETE_PARCIAL"]),
            )
        else:
            st.error(result["MENSAGEM_FRETE"])

        st.write("## Detalhamento")

        display_columns = [
            "ID_EMBARQUE",
            "ORIGEM",
            "CIDADE DESTINO",
            "UF",
            "PESO REAL",
            "PESO CUBADO",
            "VALOR MERCADORIA",
            "JAMEF",
            "CAP_INT",
            "REGIAO_CALC",
            "ROTA_CUSTO",
            "PM",
            "PESO_BASE_CUSTO",
            "PESO_CUSTEIO",
            "CUSTO_KG",
            "PERCENTUAL_VARIAVEL",
            "CUSTO_PESO",
            "CUSTO_VARIAVEL",
            "CUSTO_TOTAL",
            "STATUS_CUSTO",
            "MENSAGEM_CUSTO",
            "BUSCA_DESTINO",
            "REF_DESTINO",
            "ROTA_FRETE",
            "PESO_TARIFADO",
            "FAIXA_PESO",
            "VALOR_FAIXA",
            "FRETE_PESO",
            "PERCENTUAL_AD_VALOREM",
            "AD_VALOREM",
            "FRETE_PARCIAL",
            "STATUS_FRETE",
            "MENSAGEM_FRETE",
        ]

        existing_columns = [
            column
            for column in display_columns
            if column in result_df.columns
        ]

        st.dataframe(
            result_df[existing_columns],
            use_container_width=True,
            hide_index=True,
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
            shipment_batch = (
                file_repository.load_uploaded_shipments(
                    uploaded_file=uploaded_file,
                    file_name=uploaded_file.name,
                )
            )

            st.success(
                f"Arquivo carregado com "
                f"{len(shipment_batch):,} embarques."
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
                    "Calculando custos e fretes..."
                ):
                    batch_result = (
                        simulation_service.calculate_batch(
                            shipments=shipment_batch,
                            cities=cities_df,
                            costs=costs_df,
                            freight_table=freight_table_df,
                        )
                    )

                    batch_summary_cost = (
                        cost_service.create_summary(
                            batch_result
                        )
                    )

                    batch_summary_freight = (
                        freight_service.create_summary(
                            batch_result
                        )
                    )

                st.session_state["batch_result"] = batch_result
                st.session_state[
                    "batch_summary_cost"
                ] = batch_summary_cost
                st.session_state[
                    "batch_summary_freight"
                ] = batch_summary_freight

        except Exception as error:
            st.error("Não foi possível processar o arquivo.")
            st.exception(error)

    if "batch_result" in st.session_state:
        batch_result = st.session_state["batch_result"]
        summary_cost = st.session_state[
            "batch_summary_cost"
        ].iloc[0]
        summary_freight = st.session_state[
            "batch_summary_freight"
        ].iloc[0]

        st.write("## Resumo do custo")

        c1, c2, c3 = st.columns(3)
        c1.metric(
            "Embarques",
            f"{int(summary_cost['QTD_EMBARQUES']):,}",
        )
        c2.metric(
            "Custos calculados",
            f"{int(summary_cost['QTD_CALCULADOS_CUSTO']):,}",
        )
        c3.metric(
            "Erros de custo",
            f"{int(summary_cost['QTD_ERROS_CUSTO']):,}",
        )

        c4, c5, c6 = st.columns(3)
        c4.metric(
            "Peso de custeio",
            f"{format_number(summary_cost['PESO_CUSTEIO_TOTAL'])} kg",
        )
        c5.metric(
            "Custo por peso",
            format_currency(summary_cost["CUSTO_PESO_TOTAL"]),
        )
        c6.metric(
            "Custo total",
            format_currency(summary_cost["CUSTO_TOTAL"]),
        )

        st.write("## Resumo do frete")

        f1, f2, f3 = st.columns(3)
        f1.metric(
            "Fretes calculados",
            f"{int(summary_freight['QTD_CALCULADOS_FRETE']):,}",
        )
        f2.metric(
            "Erros de frete",
            f"{int(summary_freight['QTD_ERROS_FRETE']):,}",
        )
        f3.metric(
            "Peso tarifado",
            f"{format_number(summary_freight['PESO_TARIFADO_TOTAL'])} kg",
        )

        f4, f5, f6 = st.columns(3)
        f4.metric(
            "Frete-peso",
            format_currency(
                summary_freight["FRETE_PESO_TOTAL"]
            ),
        )
        f5.metric(
            "Ad valorem",
            format_currency(
                summary_freight["AD_VALOREM_TOTAL"]
            ),
        )
        f6.metric(
            "Frete parcial",
            format_currency(
                summary_freight["FRETE_PARCIAL_TOTAL"]
            ),
        )

        st.write("## Resultado detalhado")

        freight_status_filter = st.multiselect(
            "Filtrar por status do frete",
            options=["OK", "ERRO"],
            default=["OK", "ERRO"],
        )

        filtered_result = batch_result[
            batch_result["STATUS_FRETE"].isin(
                freight_status_filter
            )
        ].copy()

        st.dataframe(
            filtered_result,
            use_container_width=True,
            hide_index=True,
        )

        errors = batch_result[
            (
                batch_result["STATUS_CUSTO"] == "ERRO"
            )
            | (
                batch_result["STATUS_FRETE"] == "ERRO"
            )
        ].copy()

        if not errors.empty:
            st.warning(
                f"{len(errors):,} embarque(s) possuem erro "
                "de custo ou frete."
            )

        excel_output = export_service.to_excel(
            result_dataframe=batch_result,
            cost_summary_dataframe=(
                st.session_state["batch_summary_cost"]
            ),
            freight_summary_dataframe=(
                st.session_state["batch_summary_freight"]
            ),
            errors_dataframe=errors,
        )

        st.download_button(
            label="Baixar resultado em Excel",
            data=excel_output,
            file_name=(
                "resultado_simulacao_custos_fretes.xlsx"
            ),
            mime=(
                "application/vnd.openxmlformats-officedocument."
                "spreadsheetml.sheet"
            ),
        )
