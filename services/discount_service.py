import numpy as np
import pandas as pd

from services.dashboard_service import DashboardService
from services.table_discount_service import TableDiscountService
from utils.normalization import normalize_text
from utils.number_conversion import to_number


class DiscountService:
    def create_summary(
        self,
        result: pd.DataFrame,
    ) -> pd.DataFrame:
        valid = result[result["STATUS_ALCADA"].isin(
            ["APROVADO", "BLOQUEADO"]
        )].copy()
        table_freight = self._sum_numeric(valid, "FRETE_TABELA")
        total_discount = self._sum_numeric(
            valid,
            "DESCONTO_TOTAL_RS",
        )

        return pd.DataFrame(
            [
                {
                    "QTD_EMBARQUES": len(result),
                    "QTD_APROVADOS": int(
                        (result["STATUS_ALCADA"] == "APROVADO").sum()
                    ),
                    "QTD_BLOQUEADOS": int(
                        (result["STATUS_ALCADA"] == "BLOQUEADO").sum()
                    ),
                    "QTD_ERROS_ALCADA": int(
                        (result["STATUS_ALCADA"] == "ERRO").sum()
                    ),
                    "FRETE_TABELA_TOTAL": table_freight,
                    "DESCONTO_FRETE_PESO_TOTAL": self._sum_numeric(
                        valid,
                        "DESCONTO_FRETE_PESO_RS",
                    ),
                    "DESCONTO_AD_VALOREM_TOTAL": self._sum_numeric(
                        valid,
                        "DESCONTO_AD_VALOREM_RS",
                    ),
                    "DESCONTO_TOTAL_RS": total_discount,
                    "DESCONTO_PONDERADO_PCT": (
                        total_discount / table_freight
                        if table_freight > 0
                        else 0.0
                    ),
                    "FRETE_SIMULADO_TOTAL": self._sum_numeric(
                        valid,
                        "FRETE_SIMULADO",
                    ),
                }
            ]
        )

    def calculate_batch(
        self,
        result: pd.DataFrame,
        authorities: pd.DataFrame,
        policies: pd.DataFrame,
        user: dict[str, object],
        manual_freight_weight_discount: float | None = None,
        manual_ad_valorem_discount: float | None = None,
        discount_matrix: pd.DataFrame | None = None,
    ) -> pd.DataFrame:
        details = result.apply(
            lambda row: self._calculate_row(
                row=row,
                authorities=authorities,
                policies=policies,
                user=user,
                manual_freight_weight_discount=(
                    manual_freight_weight_discount
                ),
                manual_ad_valorem_discount=(
                    manual_ad_valorem_discount
                ),
                discount_matrix=discount_matrix,
            ),
            axis=1,
            result_type="expand",
        )

        return pd.concat(
            [
                result.reset_index(drop=True),
                details.reset_index(drop=True),
            ],
            axis=1,
        )

    def _calculate_row(
        self,
        row: pd.Series,
        authorities: pd.DataFrame,
        policies: pd.DataFrame,
        user: dict[str, object],
        manual_freight_weight_discount: float | None,
        manual_ad_valorem_discount: float | None,
        discount_matrix: pd.DataFrame | None,
    ) -> dict[str, object]:
        if row.get("STATUS_FRETE") != "OK":
            return self._error_result(
                "Alçada não validada devido a erro de frete."
            )

        if discount_matrix is not None:
            (
                freight_weight_discount,
                ad_valorem_discount,
                policy_id,
            ) = self._resolve_matrix_discounts(row, discount_matrix)
        else:
            policy = self._resolve_policy(row, policies)
            freight_weight_discount = self._resolve_discount(
                row=row,
                manual_value=manual_freight_weight_discount,
                uploaded_columns=(
                    "DESCONTO FRETE PESO",
                    "DESCONTO_FRETE_PESO",
                ),
                policy_value=policy["DESCONTO_FRETE_PESO"],
            )
            ad_valorem_discount = self._resolve_discount(
                row=row,
                manual_value=manual_ad_valorem_discount,
                uploaded_columns=(
                    "DESCONTO AD VALOREM",
                    "DESCONTO_AD_VALOREM",
                ),
                policy_value=policy["DESCONTO_AD_VALOREM"],
            )
            policy_id = str(policy["ID_POLITICA"])

        if not (
            0 <= freight_weight_discount <= 1
            and 0 <= ad_valorem_discount <= 1
        ):
            return self._error_result(
                "Os descontos solicitados devem estar entre 0% e 100%."
            )

        freight_weight = to_number(row.get("FRETE_PESO"))
        ad_valorem = to_number(row.get("AD_VALOREM"))
        freight_table_value = to_number(row.get("FRETE_PARCIAL"))
        freight_weight_discount_value = (
            freight_weight * freight_weight_discount
        )
        ad_valorem_discount_value = (
            ad_valorem * ad_valorem_discount
        )
        total_discount_value = (
            freight_weight_discount_value
            + ad_valorem_discount_value
        )
        simulated_freight = (
            freight_table_value - total_discount_value
        )
        weighted_discount = (
            total_discount_value / freight_table_value
            if freight_table_value > 0
            else 0.0
        )

        freight_weight_limit = float(
            user["LIMITE_FRETE_PESO"]
        )
        ad_valorem_limit = float(
            user["LIMITE_AD_VALOREM"]
        )
        approved = (
            freight_weight_discount
            <= freight_weight_limit + 1e-12
            and ad_valorem_discount
            <= ad_valorem_limit + 1e-12
        )
        required_authority = ""

        if approved:
            status = "APROVADO"
            message = (
                "Descontos dentro da alçada do perfil "
                f"{user['PERFIL']}."
            )
        else:
            status = "BLOQUEADO"
            required_authority = self._find_required_authority(
                requested_freight_weight=freight_weight_discount,
                requested_ad_valorem=ad_valorem_discount,
                current_order=float(user["ORDEM_ALCADA"]),
                authorities=authorities,
            )
            message = (
                "Desconto acima da alçada do perfil atual. "
                f"Alçada necessária: {required_authority}."
            )

        return {
            "STATUS_ALCADA": status,
            "MENSAGEM_ALCADA": message,
            "PERFIL_SIMULACAO": user["PERFIL"],
            "LIMITE_DESCONTO_FRETE_PESO": freight_weight_limit,
            "LIMITE_DESCONTO_AD_VALOREM": ad_valorem_limit,
            "DESCONTO_FRETE_PESO_SOLICITADO": (
                freight_weight_discount
            ),
            "DESCONTO_AD_VALOREM_SOLICITADO": (
                ad_valorem_discount
            ),
            "DESCONTO_FRETE_PESO_RS": (
                freight_weight_discount_value
            ),
            "DESCONTO_AD_VALOREM_RS": (
                ad_valorem_discount_value
            ),
            "DESCONTO_TOTAL_RS": total_discount_value,
            "DESCONTO_PONDERADO_PCT": weighted_discount,
            "FRETE_TABELA": freight_table_value,
            "FRETE_PESO_LIQUIDO": (
                freight_weight - freight_weight_discount_value
            ),
            "AD_VALOREM_LIQUIDO": (
                ad_valorem - ad_valorem_discount_value
            ),
            "FRETE_SIMULADO": simulated_freight,
            "POLITICA_DESCONTO_APLICADA": policy_id,
            "ALCADA_NECESSARIA": required_authority,
        }

    def _resolve_policy(
        self,
        row: pd.Series,
        policies: pd.DataFrame,
    ) -> dict[str, object]:
        active = policies[policies["ATIVO"] == "S"].copy()
        if active.empty:
            return self._default_policy()

        state = normalize_text(row.get("UF"))
        region = DashboardService.REGION_BY_STATE.get(
            state,
            "NAO INFORMADO",
        )
        weight_range = normalize_text(row.get("FAIXA_PESO"))

        matches: list[tuple[int, pd.Series]] = []
        for _, policy in active.iterrows():
            specificity = 0
            valid = True
            for policy_column, actual_value in (
                ("REGIAO", region),
                ("UF", state),
                ("FAIXA_PESO", weight_range),
            ):
                configured = normalize_text(policy[policy_column])
                if configured in {"", "TODAS"}:
                    continue
                if configured != actual_value:
                    valid = False
                    break
                specificity += 1

            if valid:
                matches.append((specificity, policy))

        if not matches:
            return self._default_policy()

        matches.sort(key=lambda item: item[0], reverse=True)
        selected = matches[0][1]
        return {
            "ID_POLITICA": selected["ID_POLITICA"],
            "DESCONTO_FRETE_PESO": float(
                selected["DESCONTO_FRETE_PESO"]
            ),
            "DESCONTO_AD_VALOREM": float(
                selected["DESCONTO_AD_VALOREM"]
            ),
        }

    @staticmethod
    def _resolve_matrix_discounts(
        row: pd.Series,
        matrix: pd.DataFrame,
    ) -> tuple[float, float, str]:
        route = normalize_text(row.get("ROTA_FRETE"))
        match = matrix[matrix["ROTA"].map(normalize_text) == route]
        if match.empty:
            return 0.0, 0.0, "SEM_ROTA_NA_MATRIZ"

        selected = match.iloc[0]
        range_label = normalize_text(row.get("FAIXA_PESO"))
        discount_column = TableDiscountService.RANGE_DISCOUNT_COLUMNS.get(
            range_label
        )
        weight_discount = (
            to_number(selected.get(discount_column)) / 100
            if discount_column
            else 0.0
        )
        fv_discount = to_number(selected.get("DESC_FV")) / 100
        return weight_discount, fv_discount, f"MATRIZ_{route}"

    def _find_required_authority(
        self,
        requested_freight_weight: float,
        requested_ad_valorem: float,
        current_order: float,
        authorities: pd.DataFrame,
    ) -> str:
        capable = authorities[
            (authorities["ATIVO"] == "S")
            & (authorities["PODE_APROVAR"] == "S")
            & (authorities["ORDEM"] > current_order)
            & (
                authorities["DESCONTO_MAX_FRETE_PESO"]
                >= requested_freight_weight
            )
            & (
                authorities["DESCONTO_MAX_AD_VALOREM"]
                >= requested_ad_valorem
            )
        ].sort_values("ORDEM")

        if capable.empty:
            return "FORA DA POLÍTICA / GERENTE NACIONAL"

        return str(capable.iloc[0]["PERFIL"])

    @classmethod
    def _resolve_discount(
        cls,
        row: pd.Series,
        manual_value: float | None,
        uploaded_columns: tuple[str, str],
        policy_value: float,
    ) -> float:
        if manual_value is not None:
            return float(manual_value)

        for column in uploaded_columns:
            if column in row.index:
                value = row.get(column)
                if value is not None and str(value).strip() != "":
                    return cls._parse_discount(value)

        return float(policy_value)

    @staticmethod
    def _parse_discount(value: object) -> float:
        if value is None or pd.isna(value):
            return 0.0
        if isinstance(value, (int, float, np.number)):
            number = float(value)
            return number if number <= 1 else number / 100

        text = str(value).strip()
        if "%" in text:
            return to_number(text, percentage=True)
        number = to_number(text)
        return number if number <= 1 else number / 100

    @staticmethod
    def _default_policy() -> dict[str, object]:
        return {
            "ID_POLITICA": "SEM_POLITICA",
            "DESCONTO_FRETE_PESO": 0.0,
            "DESCONTO_AD_VALOREM": 0.0,
        }

    @staticmethod
    def _sum_numeric(
        dataframe: pd.DataFrame,
        column: str,
    ) -> float:
        if column not in dataframe.columns:
            return 0.0

        return float(dataframe[column].map(to_number).sum())

    @staticmethod
    def _error_result(message: str) -> dict[str, object]:
        return {
            "STATUS_ALCADA": "ERRO",
            "MENSAGEM_ALCADA": message,
            "PERFIL_SIMULACAO": "",
            "LIMITE_DESCONTO_FRETE_PESO": np.nan,
            "LIMITE_DESCONTO_AD_VALOREM": np.nan,
            "DESCONTO_FRETE_PESO_SOLICITADO": np.nan,
            "DESCONTO_AD_VALOREM_SOLICITADO": np.nan,
            "DESCONTO_FRETE_PESO_RS": np.nan,
            "DESCONTO_AD_VALOREM_RS": np.nan,
            "DESCONTO_TOTAL_RS": np.nan,
            "DESCONTO_PONDERADO_PCT": np.nan,
            "FRETE_TABELA": np.nan,
            "FRETE_PESO_LIQUIDO": np.nan,
            "AD_VALOREM_LIQUIDO": np.nan,
            "FRETE_SIMULADO": np.nan,
            "POLITICA_DESCONTO_APLICADA": "",
            "ALCADA_NECESSARIA": "",
        }
