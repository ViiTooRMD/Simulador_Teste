import numpy as np
import pandas as pd

from utils.normalization import normalize_text
from utils.number_conversion import to_number


class MarginService:
    STAGES = {
        "COLETA": "PERC_COLETA",
        "ENTREGA": "PERC_ENTREGA",
        "TERMINAIS": "PERC_TERMINAIS",
        "FIXO_UNIDADES": "PERC_FIXO_UNIDADES",
        "REDESPACHO": "PERC_REDESPACHO",
        "TRANSFERENCIAS": "PERC_TRANSFERENCIAS",
        "VAZIOS": "PERC_VAZIOS",
        "CUSTO_MATRIZ": "PERC_CUSTO_MATRIZ",
    }

    DIRECT_COST_STAGES = [
        "COLETA",
        "ENTREGA",
        "REDESPACHO",
        "TRANSFERENCIAS",
        "VAZIOS",
    ]

    def calculate_batch(
        self,
        result: pd.DataFrame,
        representations: pd.DataFrame,
    ) -> pd.DataFrame:
        dataframe = result.copy()
        dataframe["CHAVE_ROTA_REPRESENTACAO"] = (
            dataframe["ROTA_CUSTO"]
            .map(normalize_text)
            .str.replace(
                r"[^A-Z0-9]",
                "",
                regex=True,
            )
        )

        enriched = dataframe.merge(
            representations,
            on="CHAVE_ROTA_REPRESENTACAO",
            how="left",
            validate="many_to_one",
        )

        details = enriched.apply(
            self._calculate_row,
            axis=1,
            result_type="expand",
        )

        return pd.concat(
            [
                enriched.reset_index(drop=True),
                details.reset_index(drop=True),
            ],
            axis=1,
        )

    def create_summary(
        self,
        result: pd.DataFrame,
    ) -> pd.DataFrame:
        successful = result[
            result["STATUS_MARGEM"] == "OK"
        ].copy()

        freight_column = self._freight_column(successful)
        freight = self._sum_numeric(successful, freight_column)
        direct_costs = self._sum_numeric(
            successful,
            "CUSTOS_DIRETOS",
        )
        terminals = self._sum_numeric(
            successful,
            "CUSTO_ETAPA_TERMINAIS",
        )
        fixed_units = self._sum_numeric(
            successful,
            "CUSTO_ETAPA_FIXO_UNIDADES",
        )
        matrix_cost = self._sum_numeric(
            successful,
            "CUSTO_ETAPA_CUSTO_MATRIZ",
        )

        gross_margin = freight - direct_costs
        operating_without_fixed = (
            gross_margin - terminals
        )
        operating_margin = (
            operating_without_fixed - fixed_units
        )
        ebit = operating_margin - matrix_cost

        return pd.DataFrame(
            [
                {
                    "QTD_EMBARQUES": len(result),
                    "QTD_MARGENS_CALCULADAS": len(successful),
                    "QTD_ERROS_MARGEM": (
                        len(result) - len(successful)
                    ),
                    "FRETE_PARCIAL_TOTAL": freight,
                    "CUSTOS_DIRETOS_TOTAL": direct_costs,
                    "CUSTO_TERMINAIS_TOTAL": terminals,
                    "CUSTO_FIXO_UNIDADES_TOTAL": fixed_units,
                    "CUSTO_MATRIZ_TOTAL": matrix_cost,
                    "MARGEM_BRUTA_RS": gross_margin,
                    "MARGEM_BRUTA_PCT": self._margin_percentage(
                        gross_margin,
                        freight,
                    ),
                    "MARGEM_OPERACIONAL_SEM_FIXO_RS": (
                        operating_without_fixed
                    ),
                    "MARGEM_OPERACIONAL_SEM_FIXO_PCT": (
                        self._margin_percentage(
                            operating_without_fixed,
                            freight,
                        )
                    ),
                    "MARGEM_OPERACIONAL_RS": operating_margin,
                    "MARGEM_OPERACIONAL_PCT": (
                        self._margin_percentage(
                            operating_margin,
                            freight,
                        )
                    ),
                    "LAJIR_RS": ebit,
                    "LAJIR_PCT": self._margin_percentage(
                        ebit,
                        freight,
                    ),
                }
            ]
        )

    def _calculate_row(
        self,
        row: pd.Series,
    ) -> dict[str, object]:
        route = row.get("ROTA_CUSTO", "")

        if row.get("STATUS_CUSTO") != "OK":
            return self._error_result(
                "Margem não calculada devido a erro de custo."
            )

        if row.get("STATUS_FRETE") != "OK":
            return self._error_result(
                "Margem não calculada devido a erro de frete."
            )

        representation_route = row.get(
            "ROTA_REPRESENTACAO"
        )

        if (
            pd.isna(representation_route)
            or str(representation_route).strip() == ""
        ):
            return self._error_result(
                "Representatividade de custo não encontrada "
                f"para a rota {route}."
            )

        freight = to_number(
            row.get(
                "FRETE_SIMULADO",
                row.get("FRETE_PARCIAL"),
            )
        )
        total_cost = to_number(row.get("CUSTO_TOTAL"))

        stage_percentage_total = sum(
            to_number(row.get(percentage_column))
            for percentage_column in self.STAGES.values()
        )

        if stage_percentage_total <= 0:
            return self._error_result(
                "Soma das representatividades inválida ou zerada."
            )

        stage_costs: dict[str, float] = {}

        for stage, percentage_column in self.STAGES.items():
            raw_percentage = to_number(
                row.get(percentage_column)
            )
            normalized_percentage = (
                raw_percentage / stage_percentage_total
            )
            stage_costs[stage] = (
                total_cost * normalized_percentage
            )

        direct_costs = sum(
            stage_costs[stage]
            for stage in self.DIRECT_COST_STAGES
        )
        gross_margin = freight - direct_costs
        operating_without_fixed = (
            gross_margin - stage_costs["TERMINAIS"]
        )
        operating_margin = (
            operating_without_fixed
            - stage_costs["FIXO_UNIDADES"]
        )
        ebit = (
            operating_margin
            - stage_costs["CUSTO_MATRIZ"]
        )
        appropriated_cost = sum(stage_costs.values())

        result: dict[str, object] = {
            "STATUS_MARGEM": "OK",
            "MENSAGEM_MARGEM": (
                f"Rota={route} | "
                f"Representação={representation_route} | "
                f"Soma original={stage_percentage_total:.4%} | "
                f"Custo apropriado={appropriated_cost:.2f}"
            ),
            "SOMA_PERCENTUAIS_ETAPAS": stage_percentage_total,
            "CUSTO_TOTAL_APROPRIADO": appropriated_cost,
            "CUSTOS_DIRETOS": direct_costs,
            "MARGEM_BRUTA_RS": gross_margin,
            "MARGEM_BRUTA_PCT": self._margin_percentage(
                gross_margin,
                freight,
            ),
            "MARGEM_OPERACIONAL_SEM_FIXO_RS": (
                operating_without_fixed
            ),
            "MARGEM_OPERACIONAL_SEM_FIXO_PCT": (
                self._margin_percentage(
                    operating_without_fixed,
                    freight,
                )
            ),
            "MARGEM_OPERACIONAL_RS": operating_margin,
            "MARGEM_OPERACIONAL_PCT": self._margin_percentage(
                operating_margin,
                freight,
            ),
            "LAJIR_RS": ebit,
            "LAJIR_PCT": self._margin_percentage(
                ebit,
                freight,
            ),
        }

        for stage, cost in stage_costs.items():
            result[f"CUSTO_ETAPA_{stage}"] = cost

        return result

    @staticmethod
    def _margin_percentage(
        margin: float,
        freight: float,
    ) -> float:
        if freight == 0:
            return np.nan

        return margin / freight

    @staticmethod
    def _sum_numeric(
        dataframe: pd.DataFrame,
        column: str,
    ) -> float:
        if column not in dataframe.columns:
            return 0.0

        return float(
            dataframe[column]
            .map(to_number)
            .sum()
        )

    @staticmethod
    def _freight_column(dataframe: pd.DataFrame) -> str:
        if "FRETE_SIMULADO" in dataframe.columns:
            return "FRETE_SIMULADO"

        return "FRETE_PARCIAL"

    @classmethod
    def _error_result(
        cls,
        message: str,
    ) -> dict[str, object]:
        result: dict[str, object] = {
            "STATUS_MARGEM": "ERRO",
            "MENSAGEM_MARGEM": message,
            "SOMA_PERCENTUAIS_ETAPAS": np.nan,
            "CUSTO_TOTAL_APROPRIADO": np.nan,
            "CUSTOS_DIRETOS": np.nan,
            "MARGEM_BRUTA_RS": np.nan,
            "MARGEM_BRUTA_PCT": np.nan,
            "MARGEM_OPERACIONAL_SEM_FIXO_RS": np.nan,
            "MARGEM_OPERACIONAL_SEM_FIXO_PCT": np.nan,
            "MARGEM_OPERACIONAL_RS": np.nan,
            "MARGEM_OPERACIONAL_PCT": np.nan,
            "LAJIR_RS": np.nan,
            "LAJIR_PCT": np.nan,
        }

        for stage in cls.STAGES:
            result[f"CUSTO_ETAPA_{stage}"] = np.nan

        return result
