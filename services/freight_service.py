import numpy as np
import pandas as pd

from utils.normalization import normalize_text
from utils.number_conversion import to_number


class FreightService:
    def calculate_batch(
        self,
        shipments: pd.DataFrame,
        cities: pd.DataFrame,
        freight_table: pd.DataFrame,
        use_excess_rule: bool = False,
    ) -> pd.DataFrame:
        prepared = self._prepare_shipments(
            shipments
        )

        city_reference = cities[
            [
                "BUSCA",
                "JAMEF",
            ]
        ].drop_duplicates(
            subset=["BUSCA"]
        )

        enriched = prepared.merge(
            city_reference,
            left_on="BUSCA_DESTINO",
            right_on="BUSCA",
            how="left",
            validate="many_to_one",
        )

        enriched = enriched.rename(
            columns={"JAMEF": "JAMEF_DESTINO"}
        )

        enriched["ROTA_FRETE"] = (
            enriched["ORIGEM"]
            + enriched["JAMEF_DESTINO"].fillna("")
        )

        result = enriched.merge(
            freight_table,
            left_on="ROTA_FRETE",
            right_on="ROTA",
            how="left",
            validate="many_to_one",
            suffixes=("", "_FRETE_REF"),
        )

        details = result.apply(
            lambda row: self._calculate_row(
                row=row,
                use_excess_rule=use_excess_rule,
            ),
            axis=1,
            result_type="expand",
        )

        base_columns = [
            "ID_EMBARQUE",
            "BUSCA_DESTINO",
            "JAMEF_DESTINO",
            "ROTA_FRETE",
        ]

        reference_columns = [
            "FRETE_FAIXA_10",
            "FRETE_FAIXA_20",
            "FRETE_FAIXA_30",
            "FRETE_FAIXA_50",
            "FRETE_FAIXA_75",
            "FRETE_FAIXA_100",
            "FRETE_KG_ACIMA_100",
            "PERCENTUAL_AD_VALOREM",
        ]

        selected = result[
            [
                column
                for column in (
                    base_columns + reference_columns
                )
                if column in result.columns
            ]
        ].copy()

        return pd.concat(
            [
                selected.reset_index(drop=True),
                details.reset_index(drop=True),
            ],
            axis=1,
        )

    def create_summary(
        self,
        result: pd.DataFrame,
    ) -> pd.DataFrame:
        successful = result[
            result["STATUS_FRETE"] == "OK"
        ].copy()

        return pd.DataFrame(
            [
                {
                    "QTD_EMBARQUES": len(result),
                    "QTD_CALCULADOS_FRETE": len(successful),
                    "QTD_ERROS_FRETE": (
                        len(result) - len(successful)
                    ),
                    "PESO_TARIFADO_TOTAL": self._sum_numeric(
                        successful,
                        "PESO_TARIFADO",
                    ),
                    "FRETE_PESO_TOTAL": self._sum_numeric(
                        successful,
                        "FRETE_PESO",
                    ),
                    "AD_VALOREM_TOTAL": self._sum_numeric(
                        successful,
                        "AD_VALOREM",
                    ),
                    "FRETE_PARCIAL_TOTAL": (
                        self._sum_numeric(
                            successful,
                            "FRETE_PARCIAL",
                        )
                    ),
                }
            ]
        )

    def _prepare_shipments(
        self,
        shipments: pd.DataFrame,
    ) -> pd.DataFrame:
        dataframe = shipments.copy()

        dataframe.columns = [
            normalize_text(column)
            for column in dataframe.columns
        ]

        dataframe["ORIGEM"] = dataframe[
            "ORIGEM"
        ].map(normalize_text)

        dataframe["UF"] = dataframe[
            "UF"
        ].map(normalize_text)

        dataframe["CIDADE DESTINO"] = dataframe[
            "CIDADE DESTINO"
        ].map(normalize_text)

        dataframe["BUSCA_DESTINO"] = (
            dataframe["UF"]
            + dataframe["CIDADE DESTINO"]
        )

        return dataframe

    def _calculate_row(
        self,
        row: pd.Series,
        use_excess_rule: bool = False,
    ) -> dict[str, object]:
        if not row.get("JAMEF_DESTINO"):
            return self._error_result(
                "BUSCA de cidade/UF não encontrou JAMEF."
            )

        route = row.get("ROTA_FRETE", "")

        if not row.get("ROTA"):
            return self._error_result(
                f"Rota de frete {route} não encontrada."
            )

        real_weight = to_number(
            row.get("PESO REAL")
        )

        cubed_weight = to_number(
            row.get("PESO CUBADO")
        )

        merchandise_value = to_number(
            row.get("VALOR MERCADORIA")
        )

        if real_weight < 0 or cubed_weight < 0:
            return self._error_result(
                "Peso real ou cubado inválido."
            )

        if merchandise_value < 0:
            return self._error_result(
                "Valor da mercadoria inválido."
            )

        tariff_weight = max(
            real_weight,
            cubed_weight,
        )

        (
            weight_range,
            range_value,
            freight_weight,
            calculation_rule,
            excess_weight,
            base_range_value,
        ) = self._calculate_weight_freight(
            row=row,
            tariff_weight=tariff_weight,
            use_excess_rule=use_excess_rule,
        )

        if range_value <= 0:
            return self._error_result(
                "Valor da faixa de frete "
                "inválido ou zerado."
            )

        if (
            calculation_rule == "EXCEDENTE"
            and base_range_value <= 0
        ):
            return self._error_result(
                "Valor da faixa de 100 kg "
                "inválido ou zerado."
            )

        ad_valorem_percentage = to_number(
            row.get("PERCENTUAL_AD_VALOREM"),
            percentage=True,
        )

        ad_valorem = (
            merchandise_value
            * ad_valorem_percentage
        )

        partial_freight = (
            freight_weight
            + ad_valorem
        )

        return {
            "STATUS_FRETE": "OK",
            "MENSAGEM_FRETE": (
                f"Rota={route} | "
                f"Peso tarifado={tariff_weight:.2f} | "
                f"Faixa={weight_range} | "
                f"Regra={calculation_rule} | "
                f"Peso excedente={excess_weight:.2f} | "
                f"Base faixa={base_range_value:.2f} | "
                f"Valor faixa={range_value:.4f} | "
                f"Ad valorem={ad_valorem_percentage:.4%}"
            ),
            "PESO_TARIFADO": tariff_weight,
            "FAIXA_PESO": weight_range,
            "REGRA_CALCULO_FRETE": calculation_rule,
            "PESO_EXCEDENTE": excess_weight,
            "VALOR_BASE_FAIXA": base_range_value,
            "VALOR_FAIXA": range_value,
            "FRETE_PESO": freight_weight,
            "PERCENTUAL_AD_VALOREM_CALCULADO": (
                ad_valorem_percentage
            ),
            "AD_VALOREM": ad_valorem,
            "FRETE_PARCIAL": partial_freight,
        }

    def _calculate_weight_freight(
        self,
        row: pd.Series,
        tariff_weight: float,
        use_excess_rule: bool = False,
    ) -> tuple[
        str,
        float,
        float,
        str,
        float,
        float,
    ]:
        if tariff_weight <= 10:
            label = "0 A 10 KG"
            value = to_number(
                row.get("FRETE_FAIXA_10")
            )

            return (
                label,
                value,
                value,
                "FAIXA FIXA",
                0.0,
                value,
            )

        if tariff_weight <= 20:
            label = "10 A 20 KG"
            value = to_number(
                row.get("FRETE_FAIXA_20")
            )

            return (
                label,
                value,
                value,
                "FAIXA FIXA",
                0.0,
                value,
            )

        if tariff_weight <= 30:
            label = "20 A 30 KG"
            value = to_number(
                row.get("FRETE_FAIXA_30")
            )

            return (
                label,
                value,
                value,
                "FAIXA FIXA",
                0.0,
                value,
            )

        if tariff_weight <= 50:
            label = "30 A 50 KG"
            value = to_number(
                row.get("FRETE_FAIXA_50")
            )

            return (
                label,
                value,
                value,
                "FAIXA FIXA",
                0.0,
                value,
            )

        if tariff_weight <= 75:
            label = "50 A 75 KG"
            value = to_number(
                row.get("FRETE_FAIXA_75")
            )

            return (
                label,
                value,
                value,
                "FAIXA FIXA",
                0.0,
                value,
            )

        if tariff_weight <= 100:
            label = "75 A 100 KG"
            value = to_number(
                row.get("FRETE_FAIXA_100")
            )

            return (
                label,
                value,
                value,
                "FAIXA FIXA",
                0.0,
                value,
            )

        label = "ACIMA DE 100 KG"

        value = to_number(
            row.get("FRETE_KG_ACIMA_100")
        )

        if use_excess_rule:
            base_range_value = to_number(
                row.get("FRETE_FAIXA_100")
            )

            excess_weight = (
                tariff_weight - 100.0
            )

            freight_weight = (
                base_range_value
                + excess_weight * value
            )

            return (
                label,
                value,
                freight_weight,
                "EXCEDENTE",
                excess_weight,
                base_range_value,
            )

        freight_weight = (
            tariff_weight * value
        )

        return (
            label,
            value,
            freight_weight,
            "PESO TOTAL",
            0.0,
            0.0,
        )

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
    def _error_result(
        message: str,
    ) -> dict[str, object]:
        return {
            "STATUS_FRETE": "ERRO",
            "MENSAGEM_FRETE": message,
            "PESO_TARIFADO": np.nan,
            "FAIXA_PESO": "",
            "REGRA_CALCULO_FRETE": "",
            "PESO_EXCEDENTE": np.nan,
            "VALOR_BASE_FAIXA": np.nan,
            "VALOR_FAIXA": np.nan,
            "FRETE_PESO": np.nan,
            "PERCENTUAL_AD_VALOREM_CALCULADO": (
                np.nan
            ),
            "AD_VALOREM": np.nan,
            "FRETE_PARCIAL": np.nan,
        }
