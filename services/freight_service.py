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
    ) -> pd.DataFrame:
        """
        Calcula o frete-peso e o ad valorem para uma ou várias linhas.

        Fluxo:
        1. Normaliza os embarques.
        2. Monta BUSCA_DESTINO = UF + CIDADE DESTINO.
        3. Localiza a filial JAMEF de atendimento.
        4. Monta ROTA_FRETE = ORIGEM + JAMEF_DESTINO.
        5. Localiza a rota na tabela padrão.
        6. Calcula peso tarifado, faixa, frete-peso e ad valorem.
        """

        prepared = self._prepare_shipments(
            shipments
        )

        city_reference = (
            cities[
                [
                    "BUSCA",
                    "JAMEF",
                ]
            ]
            .copy()
            .drop_duplicates(
                subset=["BUSCA"]
            )
        )

        city_reference["BUSCA"] = (
            city_reference["BUSCA"]
            .fillna("")
            .map(normalize_text)
        )

        city_reference["JAMEF"] = (
            city_reference["JAMEF"]
            .fillna("")
            .map(normalize_text)
            .str.replace(
                " ",
                "",
                regex=False,
            )
        )

        enriched = prepared.merge(
            city_reference,
            left_on="BUSCA_DESTINO",
            right_on="BUSCA",
            how="left",
            validate="many_to_one",
        )

        enriched = enriched.rename(
            columns={
                "JAMEF": "JAMEF_DESTINO",
            }
        )

        enriched["ROTA_FRETE"] = (
            enriched["ORIGEM"].fillna("")
            + enriched["JAMEF_DESTINO"].fillna("")
        )

        enriched["ROTA_FRETE"] = (
            enriched["ROTA_FRETE"]
            .map(normalize_text)
            .str.replace(
                " ",
                "",
                regex=False,
            )
        )

        result = enriched.merge(
            freight_table,
            left_on="ROTA_FRETE",
            right_on="ROTA",
            how="left",
            validate="many_to_one",
            suffixes=(
                "",
                "_FRETE_REF",
            ),
        )

        details = result.apply(
            self._calculate_row,
            axis=1,
            result_type="expand",
        )

        base_columns = [
            "ID_EMBARQUE",
            "BUSCA_DESTINO",
            "JAMEF_DESTINO",
            "ROTA_FRETE",
            "ROTA",
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
                    base_columns
                    + reference_columns
                )
                if column in result.columns
            ]
        ].copy()

        return pd.concat(
            [
                selected.reset_index(
                    drop=True
                ),
                details.reset_index(
                    drop=True
                ),
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
                    "QTD_CALCULADOS_FRETE": (
                        len(successful)
                    ),
                    "QTD_ERROS_FRETE": (
                        len(result)
                        - len(successful)
                    ),
                    "PESO_TARIFADO_TOTAL": (
                        self._sum_numeric(
                            successful,
                            "PESO_TARIFADO",
                        )
                    ),
                    "FRETE_PESO_TOTAL": (
                        self._sum_numeric(
                            successful,
                            "FRETE_PESO",
                        )
                    ),
                    "AD_VALOREM_TOTAL": (
                        self._sum_numeric(
                            successful,
                            "AD_VALOREM",
                        )
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

        dataframe["ORIGEM"] = (
            dataframe["ORIGEM"]
            .fillna("")
            .map(normalize_text)
            .str.replace(
                " ",
                "",
                regex=False,
            )
        )

        dataframe["UF"] = (
            dataframe["UF"]
            .fillna("")
            .map(normalize_text)
        )

        dataframe["CIDADE DESTINO"] = (
            dataframe["CIDADE DESTINO"]
            .fillna("")
            .map(normalize_text)
        )

        dataframe["BUSCA_DESTINO"] = (
            dataframe["UF"]
            + dataframe["CIDADE DESTINO"]
        )

        dataframe["BUSCA_DESTINO"] = (
            dataframe["BUSCA_DESTINO"]
            .map(normalize_text)
        )

        return dataframe

    def _calculate_row(
        self,
        row: pd.Series,
    ) -> dict[str, object]:
        jamef_destination = row.get(
            "JAMEF_DESTINO"
        )

        if (
            jamef_destination is None
            or pd.isna(jamef_destination)
            or str(
                jamef_destination
            ).strip() == ""
        ):
            return self._error_result(
                "BUSCA de cidade/UF não encontrou "
                "a filial JAMEF de atendimento."
            )

        route = str(
            row.get(
                "ROTA_FRETE",
                "",
            )
        ).strip()

        route_found = row.get("ROTA")

        if (
            route_found is None
            or pd.isna(route_found)
            or str(
                route_found
            ).strip() == ""
        ):
            return self._error_result(
                f"Rota de frete {route} "
                "não encontrada na "
                "TABELA_PADRAO.csv."
            )

        real_weight = to_number(
            row.get("PESO REAL"),
            default=0.0,
        )

        cubed_weight = to_number(
            row.get("PESO CUBADO"),
            default=0.0,
        )

        merchandise_value = to_number(
            row.get(
                "VALOR MERCADORIA"
            ),
            default=0.0,
        )

        if (
            real_weight < 0
            or cubed_weight < 0
        ):
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
        ) = self._calculate_weight_freight(
            row=row,
            tariff_weight=tariff_weight,
        )

        if (
            range_value is None
            or pd.isna(range_value)
            or range_value <= 0
        ):
            return self._error_result(
                "Valor da faixa de frete "
                "inválido ou zerado."
            )

        ad_valorem_percentage = to_number(
            row.get(
                "PERCENTUAL_AD_VALOREM"
            ),
            percentage=True,
            default=0.0,
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
                f"Jamef destino="
                f"{jamef_destination} | "
                f"Peso tarifado="
                f"{tariff_weight:.2f} | "
                f"Faixa={weight_range} | "
                f"Valor faixa="
                f"{range_value:.4f} | "
                f"Ad valorem="
                f"{ad_valorem_percentage:.4%}"
            ),
            "PESO_TARIFADO": (
                tariff_weight
            ),
            "FAIXA_PESO": (
                weight_range
            ),
            "VALOR_FAIXA": (
                range_value
            ),
            "FRETE_PESO": (
                freight_weight
            ),
            (
                "PERCENTUAL_"
                "AD_VALOREM_CALCULADO"
            ): ad_valorem_percentage,
            "AD_VALOREM": ad_valorem,
            "FRETE_PARCIAL": (
                partial_freight
            ),
        }

    def _calculate_weight_freight(
        self,
        row: pd.Series,
        tariff_weight: float,
    ) -> tuple[
        str,
        float,
        float,
    ]:
        if tariff_weight <= 10:
            label = "0 A 10 KG"
            value = to_number(
                row.get(
                    "FRETE_FAIXA_10"
                ),
                default=0.0,
            )

            return (
                label,
                value,
                value,
            )

        if tariff_weight <= 20:
            label = "10 A 20 KG"
            value = to_number(
                row.get(
                    "FRETE_FAIXA_20"
                ),
                default=0.0,
            )

            return (
                label,
                value,
                value,
            )

        if tariff_weight <= 30:
            label = "20 A 30 KG"
            value = to_number(
                row.get(
                    "FRETE_FAIXA_30"
                ),
                default=0.0,
            )

            return (
                label,
                value,
                value,
            )

        if tariff_weight <= 50:
            label = "30 A 50 KG"
            value = to_number(
                row.get(
                    "FRETE_FAIXA_50"
                ),
                default=0.0,
            )

            return (
                label,
                value,
                value,
            )

        if tariff_weight <= 75:
            label = "50 A 75 KG"
            value = to_number(
                row.get(
                    "FRETE_FAIXA_75"
                ),
                default=0.0,
            )

            return (
                label,
                value,
                value,
            )

        if tariff_weight <= 100:
            label = "75 A 100 KG"
            value = to_number(
                row.get(
                    "FRETE_FAIXA_100"
                ),
                default=0.0,
            )

            return (
                label,
                value,
                value,
            )

        label = "ACIMA DE 100 KG"

        value = to_number(
            row.get(
                "FRETE_KG_ACIMA_100"
            ),
            default=0.0,
        )

        freight_weight = (
            tariff_weight
            * value
        )

        return (
            label,
            value,
            freight_weight,
        )

    @staticmethod
    def _sum_numeric(
        dataframe: pd.DataFrame,
        column: str,
    ) -> float:
        if dataframe.empty:
            return 0.0

        if column not in dataframe.columns:
            return 0.0

        numeric_values = (
            dataframe[column]
            .apply(
                lambda value: to_number(
                    value=value,
                    default=0.0,
                )
            )
        )

        return float(
            numeric_values.sum()
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
            "VALOR_FAIXA": np.nan,
            "FRETE_PESO": np.nan,
            (
                "PERCENTUAL_"
                "AD_VALOREM_CALCULADO"
            ): np.nan,
            "AD_VALOREM": np.nan,
            "FRETE_PARCIAL": np.nan,
        }
