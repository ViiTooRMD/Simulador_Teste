from pathlib import Path

import pandas as pd
import streamlit as st

from repositories.cost_representation_repository import (
    CostRepresentationRepository,
)
from repositories.discount_repository import DiscountRepository
from repositories.file_repository import FileRepository
from repositories.freight_repository import FreightRepository
from repositories.user_repository import UserRepository
from services.auth_service import AuthService
from services.cost_service import CostService
from services.dashboard_service import DashboardService
from services.discount_service import DiscountService
from services.export_service import ExportService
from services.financial_service import FinancialService
from services.freight_service import FreightService
from services.margin_service import MarginService
from services.parameter_service import ParameterService
from services.simulation_service import SimulationService
from services.table_discount_service import TableDiscountService
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
user_repository = UserRepository(
    users_path="data/db_Usuarios.csv",
)
discount_repository = DiscountRepository(
    authorities_path="data/db_Alcadas_Desconto.csv",
    policies_path="data/db_Politicas_Desconto.csv",
)

cost_service = CostService()
freight_service = FreightService()
discount_service = DiscountService()
margin_service = MarginService()
financial_service = FinancialService()
parameter_service = ParameterService()
table_discount_service = TableDiscountService()
dashboard_service = DashboardService()
auth_service = AuthService()
simulation_service = SimulationService(
    cost_service=cost_service,
    freight_service=freight_service,
    discount_service=discount_service,
    margin_service=margin_service,
    financial_service=financial_service,
)
export_service = ExportService()


@st.cache_data(show_spinner=False)
def load_reference_data() -> tuple[
    pd.DataFrame,
    pd.DataFrame,
    pd.DataFrame,
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
    users = user_repository.load_users()
    authorities = discount_repository.load_authorities()
    policies = discount_repository.load_policies()

    return (
        cities,
        costs,
        freight_table,
        cost_representations,
        users,
        authorities,
        policies,
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
    st.session_state["summary_discount"] = (
        discount_service.create_summary(result)
    )
    st.session_state["summary_margin"] = (
        margin_service.create_summary(result)
    )
    st.session_state["summary_financial"] = (
        financial_service.create_summary(result)
    )


def clear_results() -> None:
    for key in (
        "active_result",
        "result_source",
        "summary_cost",
        "summary_freight",
        "summary_discount",
        "summary_margin",
        "summary_financial",
        "uploaded_preview",
    ):
        st.session_state.pop(key, None)


def get_current_user() -> dict[str, object]:
    return st.session_state["authenticated_user"]


def advance_to(page: str) -> None:
    st.session_state["pending_navigation"] = page
    st.rerun()


def get_active_policies() -> pd.DataFrame:
    return st.session_state.get(
        "discount_policies",
        discount_policies_df,
    )


def render_login() -> None:
    left, center, right = st.columns([1, 1.25, 1])
    with center:
        st.markdown(
            """
            <div class="login-brand">
                <div class="login-brand-mark">JAMEF</div>
                <h1>Simulador de Fretes</h1>
                <p>Acesse o ambiente de pricing e rentabilidade.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        with st.form("login_form"):
            email = st.text_input(
                "E-mail corporativo",
                placeholder="nome@jamef.com.br",
            )
            password = st.text_input(
                "Senha",
                type="password",
            )
            login_submitted = st.form_submit_button(
                "Entrar",
                type="primary",
                use_container_width=True,
            )

        if login_submitted:
            user = auth_service.authenticate(
                email=email,
                password=password,
                users=users_df,
                authorities=authorities_df,
            )
            if user is None:
                st.error("E-mail ou senha inválidos.")
            else:
                st.session_state["authenticated_user"] = user
                st.rerun()

        with st.expander("Acesso de demonstração"):
            st.code(
                "vendedor.interno@jamef.local\nJamef@2026",
                language=None,
            )


def render_authority_status(result: pd.Series) -> None:
    status = result.get("STATUS_ALCADA")
    message = str(result.get("MENSAGEM_ALCADA", ""))

    if status == "APROVADO":
        st.success(message)
    elif status == "BLOQUEADO":
        st.error(message)
        st.caption(
            "A simulação permanece disponível para análise, "
            "mas não pode seguir como proposta aprovada."
        )
    else:
        st.error(message or "Não foi possível validar a alçada.")


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
                "LAJIR após Financeiro",
            ],
            "PERCENTUAL": [
                summary["MARGEM_BRUTA_PCT"],
                summary["MARGEM_OPERACIONAL_SEM_FIXO_PCT"],
                summary["MARGEM_OPERACIONAL_PCT"],
                summary["LAJIR_PCT"],
                summary["LAJIR_APOS_FINANCEIRO_PCT"],
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


def render_margin_ladder(summary: dict[str, float]) -> None:
    stages = [
        ("Receita simulada", summary["FRETE_BRUTO"], 1.0),
        (
            "Margem bruta",
            summary["MARGEM_BRUTA_RS"],
            summary["MARGEM_BRUTA_PCT"],
        ),
        (
            "Operacional sem fixo",
            summary["MARGEM_OPERACIONAL_SEM_FIXO_RS"],
            summary["MARGEM_OPERACIONAL_SEM_FIXO_PCT"],
        ),
        (
            "Margem operacional",
            summary["MARGEM_OPERACIONAL_RS"],
            summary["MARGEM_OPERACIONAL_PCT"],
        ),
        (
            "Resultado após financeiro",
            summary["LAJIR_APOS_FINANCEIRO_RS"],
            summary["LAJIR_APOS_FINANCEIRO_PCT"],
        ),
    ]
    rows = []
    for label, value, percentage in stages:
        safe_percentage = 0.0 if pd.isna(percentage) else float(percentage)
        width = max(6.0, min(100.0, abs(safe_percentage) * 100))
        state = "negative" if value < 0 else "positive"
        rows.append(
            f'<div class="margin-ladder-row">'
            f'<div class="margin-ladder-label">{label}</div>'
            f'<div class="margin-ladder-track">'
            f'<div class="margin-ladder-fill {state}" '
            f'style="width:{width:.2f}%">'
            f'<span>{format_currency(value)} • '
            f'{format_percentage(percentage)}</span>'
            f'</div></div></div>'
        )
    st.markdown(
        "<div class='margin-ladder'>" + "".join(rows) + "</div>",
        unsafe_allow_html=True,
    )


def render_cycle_header(active_step: int) -> None:
    steps = ["1. Parâmetros", "2. Fluxo", "3. Descontos", "4. Decisão"]
    columns = st.columns(4)
    for index, (column, label) in enumerate(zip(columns, steps), start=1):
        state = "cycle-step-active" if index == active_step else "cycle-step"
        column.markdown(
            f"<div class='{state}'>{label}</div>",
            unsafe_allow_html=True,
        )


def render_parameters_page() -> None:
    render_hero(
        "JAMEF • Ciclo da Simulação",
        "Parâmetros",
        "Defina as premissas comerciais e operacionais do cenário.",
    )
    render_cycle_header(1)
    saved = st.session_state.get("simulation_parameters", {})

    with st.form("parameters_form"):
        col1, col2, col3 = st.columns(3)
        with col1:
            default_origin = saved.get("origin", origins[0])
            origin = st.selectbox(
                "Origem / filial",
                origins,
                index=origins.index(default_origin)
                if default_origin in origins
                else 0,
            )
            customer_pays_cubage = st.toggle(
                "O cliente pagará cubagem?",
                value=saved.get("customer_pays_cubage", False),
            )
        with col2:
            cubage_density = st.number_input(
                "Densidade da cubagem (kg/m³)",
                min_value=1.0,
                value=float(saved.get("cubage_density", 168.0)),
                step=1.0,
                disabled=not customer_pays_cubage,
            )
            payment_days = st.number_input(
                "Prazo de pagamento (dias)",
                min_value=0,
                value=int(saved.get("payment_days", 30)),
                step=1,
            )
        with col3:
            simulated_months = st.number_input(
                "Meses simulados",
                min_value=1,
                value=int(saved.get("simulated_months", 3)),
                step=1,
                help="Informativo nesta versão; será usado no BC futuro.",
            )
            use_excess_rule = st.toggle(
                "Aplicar excedente acima de 100 kg",
                value=saved.get("use_excess_rule", False),
            )

        submitted = st.form_submit_button(
            "Salvar parâmetros e avançar",
            type="primary",
            use_container_width=True,
        )

    if submitted:
        st.session_state["simulation_parameters"] = {
            "origin": origin,
            "customer_pays_cubage": customer_pays_cubage,
            "cubage_density": cubage_density,
            "payment_days": payment_days,
            "simulated_months": simulated_months,
            "use_excess_rule": use_excess_rule,
        }
        for key in (
            "pending_shipments",
            "discount_matrix",
        ):
            st.session_state.pop(key, None)
        st.session_state["discount_matrix_version"] = (
            st.session_state.get("discount_matrix_version", 0) + 1
        )
        clear_results()
        advance_to("Fluxo")

    monthly_rate = financial_service.monthly_rate
    st.caption(
        "Referência financeira: SELIC anual de 14,25% • "
        f"taxa mensal efetiva de {format_percentage(monthly_rate)}."
    )


def render_flow_page() -> None:
    render_hero(
        "JAMEF • Ciclo da Simulação",
        "Fluxo",
        "Escolha uma cotação individual ou carregue a volumetria completa.",
    )
    render_cycle_header(2)
    parameters = st.session_state.get("simulation_parameters")
    if not parameters:
        st.warning("Salve os parâmetros antes de cadastrar o fluxo.")
        return

    quotation_mode = st.toggle(
        "Modelo de cotação (simulação única)",
        value=st.session_state.get("quotation_mode", False),
        help="Desative para trabalhar com a volumetria completa.",
    )
    st.session_state["quotation_mode"] = quotation_mode

    if quotation_mode:
        with st.form("quotation_form"):
            city_options = cities_df[["CIDADE", "UF"]].drop_duplicates()
            labels = (
                city_options["CIDADE"].astype(str)
                + " / "
                + city_options["UF"].astype(str)
            ).tolist()
            col1, col2, col3 = st.columns(3)
            with col1:
                selected_label = st.selectbox("Destino", labels)
                selected_index = labels.index(selected_label)
                destination = city_options.iloc[selected_index]
                real_weight = st.number_input(
                    "Peso real (kg)", min_value=0.0, value=60.0
                )
                cubed_weight = st.number_input(
                    "Peso cubado informado (kg)",
                    min_value=0.0,
                    value=52.0,
                    disabled=parameters["customer_pays_cubage"],
                )
            with col2:
                m3 = st.number_input(
                    "Volume cúbico (m³)",
                    min_value=0.0,
                    value=1.0,
                    step=0.1,
                    disabled=not parameters["customer_pays_cubage"],
                )
                merchandise = st.number_input(
                    "Valor da mercadoria",
                    min_value=0.0,
                    value=9178.41,
                )
                volumes = st.number_input(
                    "Quantidade de volumes", min_value=0, value=1
                )
            with col3:
                if parameters["customer_pays_cubage"]:
                    calculated = m3 * parameters["cubage_density"]
                    st.metric("Peso cubado recalculado", f"{calculated:.2f} kg")
                st.info(
                    f"Origem: {parameters['origin']} • "
                    f"Prazo: {parameters['payment_days']} dias • "
                    f"Horizonte: {parameters['simulated_months']} meses"
                )
            submitted = st.form_submit_button(
                "Salvar cotação e avançar",
                type="primary",
                use_container_width=True,
            )

        if submitted:
            shipment = pd.DataFrame([{
                "ID_EMBARQUE": "COTACAO-001",
                "CIDADE DESTINO": destination["CIDADE"],
                "UF": destination["UF"],
                "PESO REAL": real_weight,
                "PESO CUBADO": cubed_weight,
                "M3": m3,
                "QTD VOLUMES": volumes,
                "VALOR MERCADORIA": merchandise,
            }])
            try:
                prepared = parameter_service.prepare_shipments(
                    shipment,
                    parameters["origin"],
                    parameters["customer_pays_cubage"],
                    parameters["cubage_density"],
                    parameters["payment_days"],
                    parameters["simulated_months"],
                )
                st.session_state["pending_shipments"] = prepared
                st.session_state.pop("discount_matrix", None)
                st.session_state["discount_matrix_version"] = (
                    st.session_state.get("discount_matrix_version", 0) + 1
                )
                clear_results()
                advance_to("Tabela e Descontos")
            except Exception as error:
                st.error(str(error))
    else:
        uploaded_file = st.file_uploader(
            "Carregar volumetria",
            type=["xlsx", "csv"],
            help="ORIGEM é opcional; o parâmetro da simulação prevalece.",
        )
        if uploaded_file is not None:
            try:
                uploaded = file_repository.load_uploaded_shipments(
                    uploaded_file,
                    uploaded_file.name,
                )
                prepared = parameter_service.prepare_shipments(
                    uploaded,
                    parameters["origin"],
                    parameters["customer_pays_cubage"],
                    parameters["cubage_density"],
                    parameters["payment_days"],
                    parameters["simulated_months"],
                )
                st.dataframe(prepared.head(30), use_container_width=True)
                if st.button(
                    "Confirmar fluxo e avançar",
                    type="primary",
                    use_container_width=True,
                ):
                    st.session_state["pending_shipments"] = prepared
                    st.session_state.pop("discount_matrix", None)
                    st.session_state["discount_matrix_version"] = (
                        st.session_state.get("discount_matrix_version", 0) + 1
                    )
                    clear_results()
                    advance_to("Tabela e Descontos")
            except Exception as error:
                st.error(str(error))

    saved_flow = st.session_state.get("pending_shipments")
    if saved_flow is not None:
        st.caption(f"Fluxo ativo: {len(saved_flow):,} embarque(s).")


def render_discount_table_page() -> None:
    render_hero(
        "JAMEF • Ciclo da Simulação",
        "Tabela e descontos",
        "Construa a proposta por UF e faixa, respeitando sua alçada.",
    )
    render_cycle_header(3)
    parameters = st.session_state.get("simulation_parameters")
    shipments = st.session_state.get("pending_shipments")
    if not parameters or shipments is None:
        st.warning("Conclua Parâmetros e Fluxo antes de definir descontos.")
        return

    if "discount_matrix" not in st.session_state:
        try:
            st.session_state["discount_matrix"] = (
                table_discount_service.create_matrix(
                    shipments,
                    cities_df,
                    freight_table_df,
                    parameters["origin"],
                )
            )
            st.session_state.setdefault("discount_matrix_version", 0)
        except Exception as error:
            st.error(str(error))
            return

    matrix = st.session_state["discount_matrix"].copy()
    ufs = sorted(
        matrix.get("UF_DESTINO", pd.Series(dtype=str))
        .dropna()
        .astype(str)
        .unique()
    )
    st.markdown("#### Condições comerciais por UF")
    st.caption(
        "Os valores das faixas abaixo já são os valores efetivos que "
        "alimentarão o cálculo. Edite as duas últimas células de cada linha."
    )
    edited = matrix.copy()
    for state in ufs:
        state_mask = edited["UF_DESTINO"].astype(str) == state
        route_count = int(state_mask.sum())
        weight_columns = list(
            TableDiscountService.RANGE_DISCOUNT_COLUMNS.values()
        )
        current_weight_discount = float(
            edited.loc[state_mask, weight_columns].max().max()
        )
        current_fv_discount = float(
            edited.loc[state_mask, "DESC_FV"].max()
        )

        with st.container(border=True):
            st.markdown(
                f"<div class='uf-pricing-title'>"
                f"<span>UF {state}</span>"
                f"<small>{route_count} destino(s)</small>"
                f"</div>",
                unsafe_allow_html=True,
            )
            a1, a2, a3 = st.columns([1, 1, 1])
            weight_discount = a1.number_input(
                "Desconto em todas as faixas (%)",
                min_value=0.0,
                max_value=100.0,
                value=current_weight_discount,
                key=f"weight_discount_{state}_{st.session_state['discount_matrix_version']}",
            )
            fv_discount = a2.number_input(
                "Desconto FV (%)",
                min_value=0.0,
                max_value=100.0,
                value=current_fv_discount,
                key=f"fv_discount_{state}_{st.session_state['discount_matrix_version']}",
            )
            if a3.button(
                f"Aplicar diretamente em {state}",
                key=f"apply_discount_{state}",
                use_container_width=True,
            ):
                st.session_state["discount_matrix"] = (
                    table_discount_service.apply_to_uf(
                        edited,
                        state,
                        weight_discount,
                        fv_discount,
                    )
                )
                st.session_state["discount_matrix_version"] += 1
                st.rerun()

            commercial_table = table_discount_service.to_commercial_table(
                edited,
                state,
            )
            effective_columns = [
                column
                for column in commercial_table.columns
                if column not in {
                    "ROTA",
                    "UF",
                    "DESTINO",
                    "DESCONTO FRETE PESO (%)",
                    "DESCONTO FV (%)",
                }
            ]
            edited_commercial = st.data_editor(
                commercial_table,
                use_container_width=True,
                hide_index=True,
                disabled=[
                    "ROTA",
                    "UF",
                    "DESTINO",
                    *effective_columns,
                ],
                column_config={
                    **{
                        column: st.column_config.NumberColumn(
                            column,
                            format=(
                                "%.3f%%"
                                if column == "FV (% NF)"
                                else "R$ %.2f"
                            ),
                        )
                        for column in effective_columns
                    },
                    "DESCONTO FRETE PESO (%)": (
                        st.column_config.NumberColumn(
                            "Desconto Frete Peso (%)",
                            min_value=0.0,
                            max_value=100.0,
                            format="%.2f%%",
                        )
                    ),
                    "DESCONTO FV (%)": st.column_config.NumberColumn(
                        "Desconto FV (%)",
                        min_value=0.0,
                        max_value=100.0,
                        format="%.2f%%",
                    ),
                },
                key=(
                    f"commercial_discount_{state}_"
                    f"{st.session_state['discount_matrix_version']}"
                ),
            )
            edited = table_discount_service.update_from_commercial_table(
                edited,
                edited_commercial,
            )
            if st.button(
                f"Atualizar valores calculados de {state}",
                key=f"refresh_values_{state}",
                use_container_width=True,
            ):
                st.session_state["discount_matrix"] = edited
                st.session_state["discount_matrix_version"] += 1
                st.rerun()

    authority = table_discount_service.validate_authority(
        edited,
        get_current_user(),
        authorities_df,
    )
    c1, c2, c3 = st.columns(3)
    c1.metric("Maior desconto Frete Peso", format_percentage(authority["MAX_FRETE_PESO"]))
    c2.metric("Maior desconto FV", format_percentage(authority["MAX_FV"]))
    c3.metric("Perfil", str(get_current_user()["PERFIL"]))

    if authority["APROVADO"]:
        st.success("Descontos dentro da alçada. Simulação liberada.")
    else:
        st.error(
            "Desconto acima da alçada. Aprovação necessária: "
            f"{authority['ALCADA_NECESSARIA']}."
        )

    if st.button(
        "Simular proposta",
        type="primary",
        use_container_width=True,
        disabled=not authority["APROVADO"],
    ):
        st.session_state["discount_matrix"] = edited
        with st.spinner("Calculando cenário estratégico..."):
            result = simulation_service.calculate_batch(
                shipments=shipments,
                cities=cities_df,
                costs=costs_df,
                freight_table=freight_table_df,
                cost_representations=cost_representations_df,
                authorities=authorities_df,
                discount_policies=get_active_policies(),
                user=get_current_user(),
                use_excess_rule=parameters["use_excess_rule"],
                discount_matrix=edited,
                payment_days=parameters["payment_days"],
            )
        store_result(result, "Cotação" if st.session_state.get("quotation_mode") else "Fluxo")
        advance_to("Decisão Estratégica")


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
        "Frete simulado",
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

    cost_tab, freight_tab, authority_tab, margin_tab = st.tabs(
        [
            "Custos",
            "Frete",
            "Alçada",
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
                "Frete tabela",
                format_currency(result["FRETE_TABELA"]),
            )

            d1, d2, d3 = st.columns(3)
            d1.metric(
                "Desconto total",
                format_currency(result["DESCONTO_TOTAL_RS"]),
            )
            d2.metric(
                "Desconto ponderado",
                format_percentage(result["DESCONTO_PONDERADO_PCT"]),
            )
            d3.metric(
                "Frete simulado",
                format_currency(result["FRETE_SIMULADO"]),
            )

    with authority_tab:
        render_authority_status(result)
        a1, a2, a3, a4 = st.columns(4)
        a1.metric(
            "Desconto Frete Peso",
            format_percentage(
                result["DESCONTO_FRETE_PESO_SOLICITADO"]
            ),
        )
        a2.metric(
            "Limite Frete Peso",
            format_percentage(result["LIMITE_DESCONTO_FRETE_PESO"]),
        )
        a3.metric(
            "Desconto FV",
            format_percentage(
                result["DESCONTO_AD_VALOREM_SOLICITADO"]
            ),
        )
        a4.metric(
            "Limite FV",
            format_percentage(result["LIMITE_DESCONTO_AD_VALOREM"]),
        )
        st.caption(
            "Política aplicada: "
            f"{result.get('POLITICA_DESCONTO_APLICADA', '-')}."
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
    current_user = get_current_user()
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
                apply_registered_policy = st.checkbox(
                    "Aplicar política cadastrada",
                    value=True,
                    help=(
                        "Usa a regra mais específica por região, UF e faixa. "
                        "Desmarque para informar descontos manualmente."
                    ),
                )
                freight_weight_discount = st.number_input(
                    "Desconto Frete Peso (%)",
                    min_value=0.0,
                    max_value=100.0,
                    value=0.0,
                    step=1.0,
                    disabled=apply_registered_policy,
                    help=(
                        "Limite do perfil: "
                        f"{format_percentage(current_user['LIMITE_FRETE_PESO'])}."
                    ),
                )
                ad_valorem_discount = st.number_input(
                    "Desconto FV / Ad Valorem (%)",
                    min_value=0.0,
                    max_value=100.0,
                    value=0.0,
                    step=1.0,
                    disabled=apply_registered_policy,
                    help=(
                        "Limite do perfil: "
                        f"{format_percentage(current_user['LIMITE_AD_VALOREM'])}."
                    ),
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
                    authorities=authorities_df,
                    discount_policies=get_active_policies(),
                    user=current_user,
                    use_excess_rule=use_excess_rule,
                    manual_freight_weight_discount=(
                        None
                        if apply_registered_policy
                        else freight_weight_discount / 100
                    ),
                    manual_ad_valorem_discount=(
                        None
                        if apply_registered_policy
                        else ad_valorem_discount / 100
                    ),
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
            "QTD VOLUMES e os descontos são opcionais. "
            "Use DESCONTO FRETE PESO e DESCONTO AD VALOREM; "
            "na ausência, a política cadastrada será aplicada."
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
                            authorities=authorities_df,
                            discount_policies=get_active_policies(),
                            user=current_user,
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
    render_cycle_header(4)
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

    parameters = st.session_state.get("simulation_parameters", {})
    if parameters:
        st.markdown(
            f"**Origem:** {parameters.get('origin', '-')} &nbsp; • &nbsp; "
            f"**Cubagem:** {'Sim' if parameters.get('customer_pays_cubage') else 'Não'} &nbsp; • &nbsp; "
            f"**Densidade:** {parameters.get('cubage_density', 300):.0f} kg/m³ &nbsp; • &nbsp; "
            f"**Pagamento:** {parameters.get('payment_days', 30)} dias &nbsp; • &nbsp; "
            f"**Horizonte:** {parameters.get('simulated_months', 1)} meses"
        )

    render_section_title("Resultado", "Indicadores executivos")
    r1, r2, r3, r4, r5 = st.columns(5)
    r1.metric("Receita simulada", format_currency(summary["FRETE_BRUTO"]))
    r2.metric(
        "Custo total",
        format_currency(summary["CUSTO_TOTAL"]),
    )
    r3.metric(
        "Impacto financeiro",
        format_currency(summary["IMPACTO_FINANCEIRO_RS"]),
    )
    r4.metric(
        "Resultado após financeiro",
        format_currency(summary["LAJIR_APOS_FINANCEIRO_RS"]),
    )
    r5.metric(
        "Margem final",
        format_percentage(summary["LAJIR_APOS_FINANCEIRO_PCT"]),
    )

    p1, p2, p3, p4, p5 = st.columns(5)
    p1.metric("Embarques", f"{int(summary['EMBARQUES']):,}")
    p2.metric("Volumes", f"{int(summary['VOLUMES']):,}")
    p3.metric(
        "Peso tarifado",
        f"{format_number(summary['PESO_TARIFADO'])} kg",
    )
    p4.metric(
        "Ticket médio",
        format_currency(summary["TICKET_MEDIO"]),
    )
    p5.metric("R$/kg", format_currency(summary["R$_KG"]))

    chart1, chart2 = st.columns(2)
    with chart1:
        render_section_title("Rentabilidade", "Escada de formação do resultado")
        render_margin_ladder(summary)
    with chart2:
        render_section_title("Custos", "Concentração por etapa")
        st.bar_chart(
            cost_stage_chart(result),
            use_container_width=True,
            color="#2E2D2C",
        )

    render_section_title("Diagnóstico", "Performance econômica do fluxo")
    range_summary = dashboard_service.create_grouped_summary(
        result,
        "Faixa de peso",
    )
    range_chart = range_summary.set_index("FAIXA_PESO")[[
        "FRETE_BRUTO",
        "CUSTO_TOTAL",
        "LAJIR_APOS_FINANCEIRO_RS",
    ]].rename(columns={
        "FRETE_BRUTO": "Receita simulada",
        "CUSTO_TOTAL": "Custo total",
        "LAJIR_APOS_FINANCEIRO_RS": "Resultado final",
    })

    diagnostic1, diagnostic2 = st.columns([1.25, 1])
    with diagnostic1:
        st.markdown("#### Receita, custo e resultado por faixa")
        st.bar_chart(
            range_chart,
            use_container_width=True,
            color=["#C00D1E", "#2E2D2C", "#8B8B88"],
        )
    with diagnostic2:
        st.markdown("#### Eficiência por UF")
        state_summary = dashboard_service.create_grouped_summary(
            result,
            "Estado",
        ).copy()
        state_summary["MARGEM_FINAL_%"] = (
            state_summary["LAJIR_APOS_FINANCEIRO_%"] * 100
        )
        st.scatter_chart(
            state_summary,
            x="R$_KG",
            y="MARGEM_FINAL_%",
            size="EMBARQUES",
            color="UF",
            use_container_width=True,
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
    negative_count = int(
        (prepared["LAJIR_APOS_FINANCEIRO_RS"] < 0).sum()
    )
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
            "Rentabilidade crítica",
            f"{negative_count:,} embarque(s) com resultado final negativo.",
        ),
        (
            "Maior concentração de custo",
            f"{largest_stage['ETAPA']}: "
            f"{format_currency(largest_stage['CUSTO'])}.",
        ),
        (
            "Prazo de pagamento",
            "Impacto financeiro de "
            f"{format_currency(summary['IMPACTO_FINANCEIRO_RS'])}.",
        ),
    ]

    insight_columns = st.columns(4)
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
    )[["LAJIR_APOS_FINANCEIRO_%"]]

    chart_col1, chart_col2 = st.columns(2)
    with chart_col1:
        st.markdown("#### Receita simulada")
        st.bar_chart(
            revenue_chart,
            use_container_width=True,
            color="#C00D1E",
        )
    with chart_col2:
        st.markdown("#### LAJIR após financeiro")
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
        "LAJIR_APOS_FINANCEIRO_%",
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
            "LAJIR_APOS_FINANCEIRO_%": st.column_config.NumberColumn(
                format="%.2f%%"
            ),
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

    filter1, filter2, filter3, filter4 = st.columns(4)
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
    with filter4:
        authority_status = st.multiselect(
            "Status da alçada",
            ["APROVADO", "BLOQUEADO", "ERRO"],
            default=["APROVADO", "BLOQUEADO", "ERRO"],
        )

    filtered = result[
        result["STATUS_CUSTO"].isin(cost_status)
        & result["STATUS_FRETE"].isin(freight_status)
        & result["STATUS_MARGEM"].isin(margin_status)
        & result["STATUS_ALCADA"].isin(authority_status)
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
        | (result["STATUS_ALCADA"] == "ERRO")
    ].copy()

    excel_output = export_service.to_excel(
        result_dataframe=result,
        cost_summary_dataframe=st.session_state["summary_cost"],
        freight_summary_dataframe=st.session_state[
            "summary_freight"
        ],
        discount_summary_dataframe=st.session_state[
            "summary_discount"
        ],
        financial_summary_dataframe=st.session_state[
            "summary_financial"
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


def render_discount_policy_page() -> None:
    render_hero(
        "JAMEF • Governança Comercial",
        "Políticas de desconto",
        "Configure descontos por região, UF e faixa sem alterar as alçadas.",
    )
    st.info(
        "A política define o desconto solicitado. A alçada do usuário "
        "continua sendo validada separadamente para Frete Peso e FV."
    )

    editor = get_active_policies().copy()
    for column in (
        "DESCONTO_FRETE_PESO",
        "DESCONTO_AD_VALOREM",
    ):
        editor[column] = editor[column] * 100

    edited = st.data_editor(
        editor,
        num_rows="dynamic",
        use_container_width=True,
        hide_index=True,
        column_config={
            "DESCONTO_FRETE_PESO": st.column_config.NumberColumn(
                "Desconto Frete Peso (%)",
                min_value=0.0,
                max_value=100.0,
                format="%.2f%%",
            ),
            "DESCONTO_AD_VALOREM": st.column_config.NumberColumn(
                "Desconto FV (%)",
                min_value=0.0,
                max_value=100.0,
                format="%.2f%%",
            ),
            "ATIVO": st.column_config.SelectboxColumn(
                options=["S", "N"],
            ),
        },
        key="policy_editor",
    )

    apply_column, download_column = st.columns(2)
    with apply_column:
        if st.button(
            "Aplicar políticas nesta sessão",
            type="primary",
            use_container_width=True,
        ):
            try:
                prepared = edited.copy()
                for column in (
                    "DESCONTO_FRETE_PESO",
                    "DESCONTO_AD_VALOREM",
                ):
                    prepared[column] = (
                        pd.to_numeric(prepared[column]) / 100
                    )
                blank_ids = (
                    prepared["ID_POLITICA"].fillna("").astype(str).str.strip()
                    == ""
                )
                for sequence, index in enumerate(
                    prepared.index[blank_ids],
                    start=1,
                ):
                    prepared.at[index, "ID_POLITICA"] = (
                        f"POL_AUTO_{sequence:03d}"
                    )
                st.session_state["discount_policies"] = (
                    discount_repository.prepare_policies(prepared)
                )
                clear_results()
                st.success(
                    "Políticas aplicadas. Novas simulações usarão esta versão."
                )
            except Exception as error:
                st.error(f"Política inválida: {error}")

    with download_column:
        download_source = edited.copy()
        for column in (
            "DESCONTO_FRETE_PESO",
            "DESCONTO_AD_VALOREM",
        ):
            download_source[column] = (
                pd.to_numeric(download_source[column]) / 100
            )
        try:
            policy_csv = discount_repository.serialize_policies(
                download_source
            )
            st.download_button(
                "Baixar políticas em CSV",
                data=policy_csv,
                file_name="db_Politicas_Desconto.csv",
                mime="text/csv",
                use_container_width=True,
            )
        except Exception:
            st.caption("Corrija a tabela para habilitar o download.")


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
            "Usuários",
            "Alçadas",
            "Políticas",
        ]
    )
    datasets = [
        ("CIDADES.csv", cities_df),
        ("CUSTOS.csv", costs_df),
        ("TABELA_PADRAO.csv", freight_table_df),
        ("db_Reprsent_Custos.csv", cost_representations_df),
        (
            "db_Usuarios.csv",
            users_df.drop(columns=["SENHA_SALT", "SENHA_HASH"]),
        ),
        ("db_Alcadas_Desconto.csv", authorities_df),
        ("db_Politicas_Desconto.csv", get_active_policies()),
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
        users_df,
        authorities_df,
        discount_policies_df,
    ) = load_reference_data()
except Exception as error:
    st.error("Falha ao carregar os arquivos de referência.")
    st.exception(error)
    st.stop()

if "authenticated_user" not in st.session_state:
    render_login()
    st.stop()

origins = file_repository.get_available_origins(costs_df)
current_user = get_current_user()

pending_navigation = st.session_state.pop("pending_navigation", None)
if pending_navigation:
    st.session_state["navigation_page"] = pending_navigation

with st.sidebar:
    st.markdown("## JAMEF")
    st.caption("Simulador de Fretes")
    st.markdown(
        f"""
        <div class="jamef-user-card">
            <div class="jamef-user-title">{current_user['NOME']}</div>
            <div class="jamef-user-subtitle">
                {current_user['PERFIL']}<br>
                Frete Peso: {format_percentage(current_user['LIMITE_FRETE_PESO'])}
                • FV: {format_percentage(current_user['LIMITE_AD_VALOREM'])}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    navigation = [
        "Parâmetros",
        "Fluxo",
        "Tabela e Descontos",
        "Decisão Estratégica",
        "Análises por Segmento",
        "Detalhamento",
    ]

    page = st.radio(
        "Navegação",
        navigation,
        label_visibility="collapsed",
        key="navigation_page",
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

    if st.button("Sair", use_container_width=True):
        clear_results()
        st.session_state.pop("authenticated_user", None)
        st.rerun()


if page == "Parâmetros":
    render_parameters_page()
elif page == "Fluxo":
    render_flow_page()
elif page == "Tabela e Descontos":
    render_discount_table_page()
elif page == "Decisão Estratégica":
    render_executive_dashboard()
elif page == "Análises por Segmento":
    render_analysis_page()
elif page == "Detalhamento":
    render_detail_page()
else:
    render_detail_page()
