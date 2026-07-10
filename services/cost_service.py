import numpy as np
import pandas as pd

from utils.normalization import normalize_text
from utils.number_conversion import to_number


class CostService:
    def calculate_batch(
        self,
        shipments: pd.DataFrame,
        cities: pd.DataFrame,
        costs: pd.DataFrame,
    ) -> pd.DataFrame:
        prepared_shipments = self._prepare_shipments(shipments)

        enriched = prepared_shipments.merge(
            cities[
                [
                    "CHAVE_CIDADE",
                    "UF",
                    "CIDADE",
                    "JAMEF",
                    "CAP_INT",
                    "REGIAO_CALC",
                ]
            ],
            on=["CHAVE_CIDADE", "UF"],
            how="left",
            validate="many_to_one",
        )

        enriched["ROTA_CALC"] = (
            enriched["ORIGEM"].map(normalize_text)
            + enriched["JAMEF"].fillna("")
        )

        result = enriched.merge(
            costs,
            left_on="ROTA_CALC",
            right_on="ROTA",
            how="left",
            validate="many_to_one",
        )

        calculation_details = result.apply(
            self._calculate_row,
            axis=1,
            result_type="expand",
        )

        return pd.concat(
            [
                result.reset_index(drop=True),
                calculation_details.reset_index(drop=True),
            ],
            axis=1,
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

        dataframe["CHAVE_CIDADE"] = dataframe[
            "CIDADE DESTINO"
        ].map(normalize_text)

        dataframe["UF"] = dataframe["UF"].map(normalize_text)
        dataframe["ORIGEM"] = dataframe["ORIGEM"].map(normalize_text)

        return dataframe

    def _calculate_row(
        self,
        row: pd.Series,
    ) -> dict[str, object]:
        route = row.get("ROTA_CALC", "")
        region = row.get("REGIAO_CALC", "")

        if not row.get("JAMEF"):
            return self._error_result(
                "Cidade e UF não encontradas no cadastro."
            )

        if pd.isna(row.get("PM")) or str(row.get("PM")).strip() == "":
            return self._error_result(
                f"Rota {route} não encontrada em CUSTOS.csv."
            )

        if region not in {"CAPITAL", "INTERIOR"}:
            return self._error_result(
                f"Classificação Capital/Interior inválida: "
                f"{row.get('CAP_INT')}"
            )

        real_weight = to_number(row.get("PESO REAL"))
        merchandise_value = to_number(
            row.get("VALOR MERCADORIA")
        )
        minimum_weight = to_number(row.get("PM"))

        costing_weight = max(real_weight, minimum_weight)

        if region == "CAPITAL":
            cost_per_kg = to_number(row.get("R$_CAPITAL"))
            variable_percentage = to_number(
                row.get("%_CAPITAL"),
                percentage=True,
            )
        else:
            cost_per_kg = to_number(row.get("R$_INTERIOR"))
            variable_percentage = to_number(
                row.get("%_INTERIOR"),
                percentage=True,
            )

        weight_cost = costing_weight * cost_per_kg
        variable_cost = merchandise_value * variable_percentage
        total_cost = weight_cost + variable_cost

        return {
            "STATUS": "OK",
            "MENSAGEM": (
                f"{region} | PM={minimum_weight:.2f} | "
                f"Peso custeio={costing_weight:.2f} | "
                f"R$/kg={cost_per_kg:.4f} | "
                f"Variável={variable_percentage:.4%}"
            ),
            "PESO_CUSTEIO": costing_weight,
            "CUSTO_KG": cost_per_kg,
            "PERCENTUAL_VARIAVEL": variable_percentage,
            "CUSTO_PESO": weight_cost,
            "CUSTO_VARIAVEL": variable_cost,
            "CUSTO_TOTAL": total_cost,
        }

    @staticmethod
    def _error_result(message: str) -> dict[str, object]:
        return {
            "STATUS": "ERRO",
            "MENSAGEM": message,
            "PESO_CUSTEIO": np.nan,
            "CUSTO_KG": np.nan,
            "PERCENTUAL_VARIAVEL": np.nan,
            "CUSTO_PESO": np.nan,
            "CUSTO_VARIAVEL": np.nan,
            "CUSTO_TOTAL": np.nan,
        }
