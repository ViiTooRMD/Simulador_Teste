from pathlib import Path

import pandas as pd
import streamlit as st

from repositories.cost_representation_repository import (
    CostRepresentationRepository,
)
from repositories.file_repository import FileRepository
from repositories.freight_repository import FreightRepository
from services.cost_service import CostService
from services.dashboard_service import DashboardService
from services.export_service import ExportService
from services.freight_service import FreightService
from services.margin_service import MarginService
from services.simulation_service import SimulationService
from utils.formatting import format_currency, format_number


st.set_page_config(
    page_title="Simulador de Fretes | JAMEF",
    page_icon="🚚",
    layout="wide",
    initial_sidebar_state="expanded",
)


def load_css() -> None:
    css_path = Path("assets/styles.css")

    if css_path.exists():
        st.markdown(
            f"<style>{css_path.read_text(encoding='utf-8')}</style>",
            unsafe_allow_html=True,
        )


def format_percentage(value: float) -> str:
    if value is None or pd.isna(value):
        return "-"

    return f"{value:.2%}".replace(".", ",")


def render_hero(
    eyebrow: str,
    title: str,
    subtitle: str,
) -> None:
    st.markdown(
        f"""
        <div class="jamef-hero">
            <div class="jamef-eyebrow">{eyebrow}</div>
            <h1>{title}</h1>
            <p>{subtitle}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_section_title(
    kicker: str,
    title: str,
) -> None:
    st.markdown(
        f"<div class='section-kicker'>{kicker}</div>",
        unsafe_allow_html=True,
    )
    st.subheader(title)


load_css()

file_repository = FileRepository(
    cities_path="data/CIDADES.csv",
    costs_path="data/CUSTOS.csv",
)
freight_repository = FreightRepository(
    freight_table_path="data/TABELA_PADRAO.csv",
)
cost_representation_repository = (
    CostRepresentationRepository(
        representation_path="data/db_Reprsent_Custos.csv",
    )
)

cost_service = CostService()
freight_service = FreightService()
margin_service = MarginService()
dashboard_service = DashboardService()
simulation_service = SimulationService(
    cost_service=cost_service,
    freight_service=freight_service,
    margin_service=margin_service,
)
export_service = ExportService()


@st.cache_data(show_spinner=False)
def load_reference_data() -> tuple[
    pd.DataFrame,
    pd.DataFrame,
    pd.DataFrame,
    pd.DataFrame,
]:
    cities = file_repository.load_cities()
    costs = file_repository.load_costs()
    freight_table = freight_repository.load_freight_table()
    cost_representations = (
        cost_representation_repository.load_representations()
    )

    return (
        cities,
        costs,
        freight_table,
        cost_representations,
    )


def store_result(
    result: pd.DataFrame,
    source: str,
) -> None:
    st.session_state["active_result"] = result
    st.session_state["result_source"] = source
    st.session_state["summary_cost"] = (
        cost_service.create_summary(result)
    )
    st.session_state["summary_freight"] = (
        freight_service.create_summary(result)
    )
    st.session_state["summary_margin"] = (
        margin_service.create_summary(result)
    )


def clear_results() -> None:
    for key in (
        "active_result",
        "result_source",
        "summary_cost",
        "summary_freight",
        "summary_margin",
        "uploaded_preview",
    ):
        st.session_state.pop(key, None)


def get_active_result() -> pd.DataFrame | None:
    return st.session_state.get("active_result")


def render_result_status(
    result: pd.Series,
    status_column: str,
    message_column: str,
    success_message: str,
) -> bool:
    if result.get(status_column) == "OK":
        st.success(success_message)
        return True

    st.error(str(result.get(message_column, "Erro não identificado.")))
    return False


def margin_chart(
    result: pd.DataFrame,
) -> pd.DataFrame:
    summary = dashboard_service.create_executive_summary(result)
    chart_data = pd.DataFrame(
        {
            "MARGEM": [
                "Margem Bruta",
                "Operacional sem Fixo",
                "Margem Operacional",
                "LAJIR",
            ],
            "PERCENTUAL": [
                summary["MARGEM_BRUTA_PCT"],
                summary["MARGEM_OPERACIONAL_SEM_FIXO_PCT"],
                summary["MARGEM_OPERACIONAL_PCT"],
                summary["LAJIR_PCT"],
            ],
        }
    )

    return chart_data.set_index("MARGEM")[[
        "PERCENTUAL"
    ]]


def cost_stage_chart(
    result: pd.DataFrame,
) -> pd.DataFrame:
    stage_data = dashboard_service.create_cost_stage_summary(
        result
    )

    return stage_data.set_index("ETAPA")[["CUSTO"]]


def render_simulation_result(
    result_dataframe: pd.DataFrame,
) -> None:
    result = result_dataframe.iloc[0]
    executive = dashboard_service.create_executive_summary(
        result_dataframe
    )

    render_section_title(
        "Resumo da proposta",
        "Resultado consolidado",
    )
    k1, k2, k3, k4 = st.columns(4)
    k1.metric(
        "Frete bruto",
        format_currency(executive["FRETE_BRUTO"]),
    )
    k2.metric(
        "Custo total",
        format_currency(executive["CUSTO_TOTAL"]),
    )
    k3.metric(
        "LAJIR",
        format_currency(executive["LAJIR_RS"]),
    )
    k4.metric(
        "LAJIR %",
        format_percentage(executive["LAJIR_PCT"]),
    )

    cost_tab, freight_tab, margin_tab = st.tabs(
        [
            "Custos",
            "Frete",
            "Rentabilidade",
        ]
    )

    with cost_tab:
        if render_result_status(
            result,
            "STATUS_CUSTO",
            "MENSAGEM_CUSTO",
            "Custo calculado com sucesso.",
        ):
            c1, c2, c3, c4, c5 = st.columns(5)
            c1.metric(
                "Peso base",
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

    with freight_tab:
        if render_result_status(
            result,
            "STATUS_FRETE",
            "MENSAGEM_FRETE",
            "Frete calculado com sucesso.",
        ):
            st.caption(
                "Regra aplicada: "
                f"{result['REGRA_CALCULO_FRETE']}"
            )
            f1, f2, f3, f4, f5 = st.columns(5)
            f1.metric(
                "Peso tarifado",
                f"{format_number(result['PESO_TARIFADO'])} kg",
            )
            f2.metric("Faixa", str(result["FAIXA_PESO"]))
            f3.metric(
                "Frete-peso",
                format_currency(result["FRETE_PESO"]),
            )
            f4.metric(
                "Ad valorem",
                format_currency(result["AD_VALOREM"]),
            )
            f5.metric(
                "Frete bruto",
                format_currency(result["FRETE_PARCIAL"]),
            )

    with margin_tab:
        if render_result_status(
            result,
            "STATUS_MARGEM",
            "MENSAGEM_MARGEM",
            "Margens calculadas com sucesso.",
        ):
            m1, m2, m3, m4 = st.columns(4)
            m1.metric(
                "Margem Bruta",
                format_currency(result["MARGEM_BRUTA_RS"]),
                format_percentage(result["MARGEM_BRUTA_PCT"]),
                delta_color="off",
            )
            m2.metric(
                "Operacional sem Fixo",
                format_currency(
                    result["MARGEM_OPERACIONAL_SEM_FIXO_RS"]
                ),
                format_percentage(
                    result["MARGEM_OPERACIONAL_SEM_FIXO_PCT"]
                ),
                delta_color="off",
            )
            m3.metric(
                "Margem Operacional",
                format_currency(result["MARGEM_OPERACIONAL_RS"]),
                format_percentage(
                    result["MARGEM_OPERACIONAL_PCT"]
                ),
                delta_color="off",
            )
            m4.metric(
                "LAJIR",
                format_currency(result["LAJIR_RS"]),
                format_percentage(result["LAJIR_PCT"]),
                delta_color="off",
            )

            chart_col1, chart_col2 = st.columns(2)
            with chart_col1:
                st.markdown("#### Evolução das margens")
                st.bar_chart(
                    margin_chart(result_dataframe),
                    use_container_width=True,
                    color="#C00D1E",
                )
            with chart_col2:
                st.markdown("#### Composição do custo")
                st.bar_chart(
                    cost_stage_chart(result_dataframe),
                    use_container_width=True,
                    color="#2E2D2C",
                )


def render_simulation_page() -> None:
    render_hero(
        "JAMEF • Pricing Intelligence",
        "Nova simulação",
        "Calcule custos, fretes e rentabilidade em uma única visão.",
    )

    with st.container(border=True):
        rule_col1, rule_col2 = st.columns([2, 3])
        with rule_col1:
            st.markdown("#### Regra de frete")
            use_excess_rule = st.toggle(
                "Aplicar excedente acima de 100 kg",
                key="use_excess_rule",
                help=(
                    "Desativado: peso total × R$/kg. "
                    "Ativado: faixa de 100 kg + excedente × R$/kg."
                ),
            )
        with rule_col2:
            if use_excess_rule:
                st.info(
                    "Regra ativa: faixa de 100 kg somada ao "
                    "peso excedente multiplicado pelo R$/kg."
                )
            else:
                st.info(
                    "Regra ativa: peso tarifado total "
                    "multiplicado pelo R$/kg."
                )

    manual_tab, batch_tab = st.tabs(
        ["Cálculo manual", "Cálculo em lote"]
    )

    with manual_tab:
        with st.form("shipment_form"):
            st.markdown("#### Dados do embarque")
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
                    "Peso real (kg)",
                    min_value=0.0,
                    value=84.0,
                    step=1.0,
                )
                cubed_weight = st.number_input(
                    "Peso cubado (kg)",
                    min_value=0.0,
                    value=193.08,
                    step=1.0,
                )
                volumes = st.number_input(
                    "Quantidade de volumes",
                    min_value=0,
                    value=1,
                    step=1,
                )

            with col3:
                merchandise_value = st.number_input(
                    "Valor da mercadoria",
                    min_value=0.0,
                    value=9178.41,
                    step=100.0,
                )
                st.caption(
                    "A filial e a região serão identificadas "
                    "automaticamente pelo destino."
                )

            submitted = st.form_submit_button(
                "Calcular simulação",
                type="primary",
                use_container_width=True,
            )

        if submitted:
            shipment_dataframe = pd.DataFrame(
                [
                    {
                        "ID_EMBARQUE": "MANUAL-001",
                        "ORIGEM": origin,
                        "CIDADE DESTINO": destination_city,
                        "UF": destination_state,
                        "PESO REAL": real_weight,
                        "PESO CUBADO": cubed_weight,
                        "QTD VOLUMES": volumes,
                        "VALOR MERCADORIA": merchandise_value,
                    }
                ]
            )

            with st.spinner("Calculando proposta..."):
                result = simulation_service.calculate_batch(
                    shipments=shipment_dataframe,
                    cities=cities_df,
                    costs=costs_df,
                    freight_table=freight_table_df,
                    cost_representations=cost_representations_df,
                    use_excess_rule=use_excess_rule,
                )
            store_result(result, "Cálculo manual")

        active_result = get_active_result()
        if (
            active_result is not None
            and st.session_state.get("result_source")
            == "Cálculo manual"
        ):
            render_simulation_result(active_result)

    with batch_tab:
        st.markdown("#### Importação de volumetria")
        st.caption(
            "Envie XLSX com aba Volumetria ou CSV. "
            "A coluna QTD VOLUMES é opcional."
        )
        uploaded_file = st.file_uploader(
            "Selecionar volumetria",
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
                    f"{len(shipment_batch):,} embarques carregados."
                )
                st.dataframe(
                    shipment_batch.head(20),
                    use_container_width=True,
                    hide_index=True,
                )

                if st.button(
                    "Calcular volumetria",
                    type="primary",
                    use_container_width=True,
                ):
                    with st.spinner(
                        "Calculando custos, fretes e margens..."
                    ):
                        result = simulation_service.calculate_batch(
                            shipments=shipment_batch,
                            cities=cities_df,
                            costs=costs_df,
                            freight_table=freight_table_df,
                            cost_representations=(
                                cost_representations_df
                            ),
                            use_excess_rule=use_excess_rule,
                        )
                    store_result(result, "Cálculo em lote")
                    st.success(
                        "Simulação concluída. Acesse o "
                        "Dashboard Executivo para analisar."
                    )
            except Exception as error:
                st.error("Não foi possível processar o arquivo.")
                st.exception(error)


def render_executive_dashboard() -> None:
    render_hero(
        "JAMEF • Visão Executiva",
        "Dashboard da simulação",
        "Indicadores de receita, custo, produtividade e rentabilidade.",
    )
    result = get_active_result()

    if result is None:
        st.info(
            "Realize uma simulação manual ou em lote para "
            "habilitar o dashboard."
        )
        return

    summary = dashboard_service.create_executive_summary(result)
    st.caption(
        "Fonte ativa: "
        f"{st.session_state.get('result_source', 'Simulação')}"
    )

    render_section_title("Resultado", "Indicadores executivos")
    r1, r2, r3, r4, r5, r6 = st.columns(6)
    r1.metric("Frete bruto", format_currency(summary["FRETE_BRUTO"]))
    r2.metric("Custo total", format_currency(summary["CUSTO_TOTAL"]))
    r3.metric(
        "Margem Bruta",
        format_percentage(summary["MARGEM_BRUTA_PCT"]),
    )
    r4.metric(
        "GM sem Fixo",
        format_percentage(
            summary["MARGEM_OPERACIONAL_SEM_FIXO_PCT"]
        ),
    )
    r5.metric(
        "Margem Operacional",
        format_percentage(summary["MARGEM_OPERACIONAL_PCT"]),
    )
    r6.metric("LAJIR", format_percentage(summary["LAJIR_PCT"]))

    p1, p2, p3, p4, p5, p6 = st.columns(6)
    p1.metric("Embarques", f"{int(summary['EMBARQUES']):,}")
    p2.metric("Volumes", f"{int(summary['VOLUMES']):,}")
    p3.metric("R$/kg", format_currency(summary["R$_KG"]))
    p4.metric("Custo/kg", format_currency(summary["CUSTO_KG"]))
    p5.metric(
        "Ticket médio",
        format_currency(summary["TICKET_MEDIO"]),
    )
    p6.metric(
        "% sobre NF",
        format_percentage(summary["PERCENTUAL_SOBRE_NF"]),
    )

    chart1, chart2 = st.columns(2)
    with chart1:
        render_section_title("Rentabilidade", "Evolução das margens")
        st.bar_chart(
            margin_chart(result),
            use_container_width=True,
            color="#C00D1E",
        )
    with chart2:
        render_section_title("Custos", "Composição por etapa")
        st.bar_chart(
            cost_stage_chart(result),
            use_container_width=True,
            color="#2E2D2C",
        )

    render_section_title("Decisão", "Pontos de atenção")
    prepared = dashboard_service.prepare_result(result)
    error_count = int(
        (
            (prepared.get("STATUS_CUSTO") == "ERRO")
            | (prepared.get("STATUS_FRETE") == "ERRO")
            | (prepared.get("STATUS_MARGEM") == "ERRO")
        ).sum()
    )
    negative_count = int((prepared["LAJIR_RS"] < 0).sum())
    stage_summary = dashboard_service.create_cost_stage_summary(
        result
    )
    largest_stage = stage_summary.iloc[0]

    insights = [
        (
            "Qualidade do cálculo",
            f"{error_count:,} embarque(s) com erro de referência.",
        ),
        (
            "Rentabilidade",
            f"{negative_count:,} embarque(s) com LAJIR negativo.",
        ),
        (
            "Maior concentração de custo",
            f"{largest_stage['ETAPA']}: "
            f"{format_currency(largest_stage['CUSTO'])}.",
        ),
    ]

    insight_columns = st.columns(3)
    for column, (title, description) in zip(
        insight_columns,
        insights,
    ):
        with column:
            st.markdown(
                f"""
                <div class="decision-alert">
                    <strong>{title}</strong><br>
                    <span>{description}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_analysis_page() -> None:
    render_hero(
        "JAMEF • Analytics",
        "Análises por segmento",
        "Compare volumetria, receita, custos e margens por dimensão.",
    )
    result = get_active_result()

    if result is None:
        st.info("Realize uma simulação para habilitar as análises.")
        return

    control1, control2 = st.columns([1, 3])
    with control1:
        grouping = st.selectbox(
            "Visão da análise",
            list(DashboardService.GROUPING_COLUMNS),
        )

    summary = dashboard_service.create_grouped_summary(
        result,
        grouping,
    )
    group_column = DashboardService.GROUPING_COLUMNS[grouping]

    with control2:
        available_groups = summary[group_column].astype(str).tolist()
        selected_groups = st.multiselect(
            "Filtrar grupos",
            available_groups,
            default=available_groups,
        )

    filtered = summary[
        summary[group_column].astype(str).isin(selected_groups)
    ].copy()

    chart_data = filtered.head(20)
    revenue_chart = chart_data.set_index(group_column)[[
        "FRETE_BRUTO"
    ]]
    margin_segment_chart = chart_data.set_index(
        group_column
    )[["LAJIR_%"]]

    chart_col1, chart_col2 = st.columns(2)
    with chart_col1:
        st.markdown("#### Frete bruto")
        st.bar_chart(
            revenue_chart,
            use_container_width=True,
            color="#C00D1E",
        )
    with chart_col2:
        st.markdown("#### LAJIR por segmento")
        st.bar_chart(
            margin_segment_chart,
            use_container_width=True,
            color="#2E2D2C",
        )

    render_section_title("Resumo", f"Visão por {grouping.lower()}")
    display_table = filtered.copy()
    percentage_columns = [
        "PESO_%",
        "EMBARQUES_%",
        "MARGEM_BRUTA_%",
        "MARGEM_OPERACIONAL_SEM_FIXO_%",
        "MARGEM_OPERACIONAL_%",
        "LAJIR_%",
        "%_SOBRE_NF",
    ]
    for column in percentage_columns:
        display_table[column] = display_table[column] * 100

    st.dataframe(
        display_table,
        use_container_width=True,
        hide_index=True,
        column_config={
            "PESO_%": st.column_config.NumberColumn(format="%.2f%%"),
            "EMBARQUES_%": st.column_config.NumberColumn(format="%.2f%%"),
            "MARGEM_BRUTA_%": st.column_config.NumberColumn(
                format="%.2f%%"
            ),
            "MARGEM_OPERACIONAL_SEM_FIXO_%": (
                st.column_config.NumberColumn(format="%.2f%%")
            ),
            "MARGEM_OPERACIONAL_%": st.column_config.NumberColumn(
                format="%.2f%%"
            ),
            "LAJIR_%": st.column_config.NumberColumn(format="%.2f%%"),
            "%_SOBRE_NF": st.column_config.NumberColumn(
                format="%.2f%%"
            ),
        },
    )


def render_detail_page() -> None:
    render_hero(
        "JAMEF • Auditoria",
        "Detalhamento da simulação",
        "Consulte cada embarque, valide exceções e exporte os resultados.",
    )
    result = get_active_result()

    if result is None:
        st.info("Realize uma simulação para consultar o detalhamento.")
        return

    filter1, filter2, filter3 = st.columns(3)
    with filter1:
        cost_status = st.multiselect(
            "Status do custo",
            ["OK", "ERRO"],
            default=["OK", "ERRO"],
        )
    with filter2:
        freight_status = st.multiselect(
            "Status do frete",
            ["OK", "ERRO"],
            default=["OK", "ERRO"],
        )
    with filter3:
        margin_status = st.multiselect(
            "Status da margem",
            ["OK", "ERRO"],
            default=["OK", "ERRO"],
        )

    filtered = result[
        result["STATUS_CUSTO"].isin(cost_status)
        & result["STATUS_FRETE"].isin(freight_status)
        & result["STATUS_MARGEM"].isin(margin_status)
    ].copy()

    st.caption(
        f"Exibindo {len(filtered):,} de {len(result):,} embarques."
    )
    st.dataframe(
        filtered,
        use_container_width=True,
        hide_index=True,
    )

    errors = result[
        (result["STATUS_CUSTO"] == "ERRO")
        | (result["STATUS_FRETE"] == "ERRO")
        | (result["STATUS_MARGEM"] == "ERRO")
    ].copy()

    excel_output = export_service.to_excel(
        result_dataframe=result,
        cost_summary_dataframe=st.session_state["summary_cost"],
        freight_summary_dataframe=st.session_state[
            "summary_freight"
        ],
        margin_summary_dataframe=st.session_state[
            "summary_margin"
        ],
        errors_dataframe=errors,
    )

    st.download_button(
        "Baixar resultado completo em Excel",
        data=excel_output,
        file_name="resultado_simulacao_custos_fretes.xlsx",
        mime=(
            "application/vnd.openxmlformats-officedocument."
            "spreadsheetml.sheet"
        ),
        use_container_width=True,
    )


def render_reference_page() -> None:
    render_hero(
        "JAMEF • Governança",
        "Arquivos de referência",
        "Acompanhe as bases utilizadas pelo motor de cálculo.",
    )
    reference_tabs = st.tabs(
        [
            "Cidades",
            "Custos",
            "Tabela padrão",
            "Representatividade",
        ]
    )
    datasets = [
        ("CIDADES.csv", cities_df),
        ("CUSTOS.csv", costs_df),
        ("TABELA_PADRAO.csv", freight_table_df),
        ("db_Reprsent_Custos.csv", cost_representations_df),
    ]

    for tab, (name, dataframe) in zip(reference_tabs, datasets):
        with tab:
            col1, col2 = st.columns([1, 4])
            col1.metric("Registros", f"{len(dataframe):,}")
            col2.caption(
                f"{name} • {len(dataframe.columns)} colunas"
            )
            st.dataframe(
                dataframe,
                use_container_width=True,
                hide_index=True,
            )


try:
    (
        cities_df,
        costs_df,
        freight_table_df,
        cost_representations_df,
    ) = load_reference_data()
except Exception as error:
    st.error("Falha ao carregar os arquivos de referência.")
    st.exception(error)
    st.stop()

origins = file_repository.get_available_origins(costs_df)

with st.sidebar:
    st.markdown("## JAMEF")
    st.caption("Simulador de Fretes")
    st.markdown(
        """
        <div class="jamef-user-card">
            <div class="jamef-user-title">Ambiente interno</div>
            <div class="jamef-user-subtitle">
                Autenticação será adicionada em uma próxima etapa
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    page = st.radio(
        "Navegação",
        [
            "Nova Simulação",
            "Dashboard Executivo",
            "Análises por Segmento",
            "Detalhamento",
            "Arquivos de Referência",
        ],
        label_visibility="collapsed",
    )

    st.divider()
    source = st.session_state.get("result_source")
    if source:
        st.success(f"Resultado ativo: {source}")
    else:
        st.info("Nenhuma simulação ativa")

    if st.button("Limpar cache e resultados"):
        st.cache_data.clear()
        clear_results()
        st.rerun()


if page == "Nova Simulação":
    render_simulation_page()
elif page == "Dashboard Executivo":
    render_executive_dashboard()
elif page == "Análises por Segmento":
    render_analysis_page()
elif page == "Detalhamento":
    render_detail_page()
else:
    render_reference_page()
