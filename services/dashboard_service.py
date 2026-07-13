import numpy as np
import pandas as pd

from utils.number_conversion import to_number


class DashboardService:
    WEIGHT_RANGE_ORDER = [
        "0 A 10 KG",
        "10 A 20 KG",
        "20 A 30 KG",
        "30 A 50 KG",
        "50 A 75 KG",
        "75 A 100 KG",
        "ACIMA DE 100 KG",
        "NÃO INFORMADO",
    ]

    REGION_ORDER = [
        "NORTE",
        "NORDESTE",
        "CENTRO-OESTE",
        "SUDESTE",
        "SUL",
        "NÃO INFORMADO",
    ]

    REGION_BY_STATE = {
        "AC": "NORTE",
        "AL": "NORDESTE",
        "AP": "NORTE",
        "AM": "NORTE",
        "BA": "NORDESTE",
        "CE": "NORDESTE",
        "DF": "CENTRO-OESTE",
        "ES": "SUDESTE",
        "GO": "CENTRO-OESTE",
        "MA": "NORDESTE",
        "MT": "CENTRO-OESTE",
        "MS": "CENTRO-OESTE",
        "MG": "SUDESTE",
        "PA": "NORTE",
        "PB": "NORDESTE",
        "PR": "SUL",
        "PE": "NORDESTE",
        "PI": "NORDESTE",
        "RJ": "SUDESTE",
        "RN": "NORDESTE",
        "RS": "SUL",
        "RO": "NORTE",
        "RR": "NORTE",
        "SC": "SUL",
        "SP": "SUDESTE",
        "SE": "NORDESTE",
        "TO": "NORTE",
    }

    NUMERIC_COLUMNS = [
        "PESO REAL",
        "PESO CUBADO",
        "PESO_TARIFADO",
        "VALOR MERCADORIA",
        "FRETE_PESO",
        "AD_VALOREM",
        "FRETE_PARCIAL",
        "CUSTO_TOTAL",
        "MARGEM_BRUTA_RS",
        "MARGEM_OPERACIONAL_SEM_FIXO_RS",
        "MARGEM_OPERACIONAL_RS",
        "LAJIR_RS",
        "CUSTO_ETAPA_COLETA",
        "CUSTO_ETAPA_ENTREGA",
        "CUSTO_ETAPA_TERMINAIS",
        "CUSTO_ETAPA_FIXO_UNIDADES",
        "CUSTO_ETAPA_REDESPACHO",
        "CUSTO_ETAPA_TRANSFERENCIAS",
        "CUSTO_ETAPA_VAZIOS",
        "CUSTO_ETAPA_CUSTO_MATRIZ",
    ]

    GROUPING_COLUMNS = {
        "Faixa de peso": "FAIXA_PESO",
        "Região": "REGIAO_DESTINO",
        "Estado": "UF",
        "Filial": "FILIAL_DESTINO",
    }

    def prepare_result(
        self,
        result: pd.DataFrame,
    ) -> pd.DataFrame:
        dataframe = result.copy()

        for column in self.NUMERIC_COLUMNS:
            if column not in dataframe.columns:
                dataframe[column] = 0.0
            dataframe[column] = dataframe[column].map(
                to_number
            )

        volume_column = self._find_volume_column(dataframe)
        if volume_column:
            dataframe["QTD_VOLUMES_DASHBOARD"] = (
                dataframe[volume_column].map(to_number)
            )
        else:
            dataframe["QTD_VOLUMES_DASHBOARD"] = 0.0

        if "UF" not in dataframe.columns:
            dataframe["UF"] = "NÃO INFORMADO"
        dataframe["UF"] = (
            dataframe["UF"]
            .fillna("")
            .astype(str)
            .str.strip()
            .str.upper()
            .replace("", "NÃO INFORMADO")
        )
        dataframe["REGIAO_DESTINO"] = (
            dataframe["UF"]
            .map(self.REGION_BY_STATE)
            .fillna("NÃO INFORMADO")
        )

        if "JAMEF_DESTINO" in dataframe.columns:
            branch = dataframe["JAMEF_DESTINO"]
        elif "JAMEF" in dataframe.columns:
            branch = dataframe["JAMEF"]
        else:
            branch = pd.Series(
                "NÃO INFORMADO",
                index=dataframe.index,
            )
        dataframe["FILIAL_DESTINO"] = (
            branch.fillna("")
            .astype(str)
            .str.strip()
            .str.upper()
            .replace("", "NÃO INFORMADO")
        )

        if "FAIXA_PESO" not in dataframe.columns:
            dataframe["FAIXA_PESO"] = "NÃO INFORMADO"
        dataframe["FAIXA_PESO"] = (
            dataframe["FAIXA_PESO"]
            .fillna("NÃO INFORMADO")
            .replace("", "NÃO INFORMADO")
        )

        return dataframe

    def create_executive_summary(
        self,
        result: pd.DataFrame,
    ) -> dict[str, float]:
        dataframe = self.prepare_result(result)
        freight = float(dataframe["FRETE_PARCIAL"].sum())
        cost = float(dataframe["CUSTO_TOTAL"].sum())
        shipments = float(len(dataframe))
        real_weight = float(dataframe["PESO REAL"].sum())
        cubed_weight = float(dataframe["PESO CUBADO"].sum())
        tariff_weight = float(
            dataframe["PESO_TARIFADO"].sum()
        )
        merchandise = float(
            dataframe["VALOR MERCADORIA"].sum()
        )

        return {
            "EMBARQUES": shipments,
            "VOLUMES": float(
                dataframe["QTD_VOLUMES_DASHBOARD"].sum()
            ),
            "PESO_REAL": real_weight,
            "PESO_CUBADO": cubed_weight,
            "PESO_TARIFADO": tariff_weight,
            "VALOR_MERCADORIA": merchandise,
            "FRETE_BRUTO": freight,
            "CUSTO_TOTAL": cost,
            "MARGEM_BRUTA_RS": float(
                dataframe["MARGEM_BRUTA_RS"].sum()
            ),
            "MARGEM_BRUTA_PCT": self._safe_divide(
                dataframe["MARGEM_BRUTA_RS"].sum(),
                freight,
            ),
            "MARGEM_OPERACIONAL_SEM_FIXO_RS": float(
                dataframe[
                    "MARGEM_OPERACIONAL_SEM_FIXO_RS"
                ].sum()
            ),
            "MARGEM_OPERACIONAL_SEM_FIXO_PCT": (
                self._safe_divide(
                    dataframe[
                        "MARGEM_OPERACIONAL_SEM_FIXO_RS"
                    ].sum(),
                    freight,
                )
            ),
            "MARGEM_OPERACIONAL_RS": float(
                dataframe["MARGEM_OPERACIONAL_RS"].sum()
            ),
            "MARGEM_OPERACIONAL_PCT": self._safe_divide(
                dataframe["MARGEM_OPERACIONAL_RS"].sum(),
                freight,
            ),
            "LAJIR_RS": float(dataframe["LAJIR_RS"].sum()),
            "LAJIR_PCT": self._safe_divide(
                dataframe["LAJIR_RS"].sum(),
                freight,
            ),
            "R$_KG": self._safe_divide(
                freight,
                tariff_weight,
            ),
            "CUSTO_KG": self._safe_divide(
                cost,
                tariff_weight,
            ),
            "TICKET_MEDIO": self._safe_divide(
                freight,
                shipments,
            ),
            "PERCENTUAL_SOBRE_NF": self._safe_divide(
                freight,
                merchandise,
            ),
            "DROPSIZE": self._safe_divide(
                cubed_weight,
                shipments,
            ),
        }

    def create_grouped_summary(
        self,
        result: pd.DataFrame,
        grouping_label: str,
    ) -> pd.DataFrame:
        dataframe = self.prepare_result(result)
        group_column = self.GROUPING_COLUMNS[
            grouping_label
        ]

        grouped = dataframe.groupby(
            group_column,
            dropna=False,
            observed=True,
        ).agg(
            PESO_REAL=("PESO REAL", "sum"),
            PESO_CUBADO=("PESO CUBADO", "sum"),
            PESO_TARIFADO=("PESO_TARIFADO", "sum"),
            VOLUMES=("QTD_VOLUMES_DASHBOARD", "sum"),
            EMBARQUES=("ID_EMBARQUE", "count"),
            VALOR_MERCADORIA=("VALOR MERCADORIA", "sum"),
            FRETE_BRUTO=("FRETE_PARCIAL", "sum"),
            CUSTO_TOTAL=("CUSTO_TOTAL", "sum"),
            MARGEM_BRUTA_RS=("MARGEM_BRUTA_RS", "sum"),
            MARGEM_OPERACIONAL_SEM_FIXO_RS=(
                "MARGEM_OPERACIONAL_SEM_FIXO_RS",
                "sum",
            ),
            MARGEM_OPERACIONAL_RS=(
                "MARGEM_OPERACIONAL_RS",
                "sum",
            ),
            LAJIR_RS=("LAJIR_RS", "sum"),
        ).reset_index()

        total_weight = grouped["PESO_TARIFADO"].sum()
        total_shipments = grouped["EMBARQUES"].sum()

        grouped["PESO_%"] = self._safe_series_divide(
            grouped["PESO_TARIFADO"],
            total_weight,
        )
        grouped["EMBARQUES_%"] = self._safe_series_divide(
            grouped["EMBARQUES"],
            total_shipments,
        )
        grouped["VALOR_AGREGADO"] = self._safe_series_divide(
            grouped["VALOR_MERCADORIA"],
            grouped["PESO_REAL"],
        )
        grouped["DROPSIZE"] = self._safe_series_divide(
            grouped["PESO_CUBADO"],
            grouped["EMBARQUES"],
        )
        grouped["R$_KG"] = self._safe_series_divide(
            grouped["FRETE_BRUTO"],
            grouped["PESO_TARIFADO"],
        )
        grouped["CUSTO_KG"] = self._safe_series_divide(
            grouped["CUSTO_TOTAL"],
            grouped["PESO_TARIFADO"],
        )
        grouped["TICKET_MEDIO"] = self._safe_series_divide(
            grouped["FRETE_BRUTO"],
            grouped["EMBARQUES"],
        )
        grouped["%_SOBRE_NF"] = self._safe_series_divide(
            grouped["FRETE_BRUTO"],
            grouped["VALOR_MERCADORIA"],
        )
        grouped["MARGEM_BRUTA_%"] = self._safe_series_divide(
            grouped["MARGEM_BRUTA_RS"],
            grouped["FRETE_BRUTO"],
        )
        grouped["MARGEM_OPERACIONAL_SEM_FIXO_%"] = (
            self._safe_series_divide(
                grouped["MARGEM_OPERACIONAL_SEM_FIXO_RS"],
                grouped["FRETE_BRUTO"],
            )
        )
        grouped["MARGEM_OPERACIONAL_%"] = (
            self._safe_series_divide(
                grouped["MARGEM_OPERACIONAL_RS"],
                grouped["FRETE_BRUTO"],
            )
        )
        grouped["LAJIR_%"] = self._safe_series_divide(
            grouped["LAJIR_RS"],
            grouped["FRETE_BRUTO"],
        )

        if grouping_label == "Faixa de peso":
            grouped[group_column] = pd.Categorical(
                grouped[group_column],
                categories=self.WEIGHT_RANGE_ORDER,
                ordered=True,
            )
            grouped = grouped.sort_values(group_column)
            grouped[group_column] = grouped[
                group_column
            ].astype(str)
        elif grouping_label == "Região":
            grouped[group_column] = pd.Categorical(
                grouped[group_column],
                categories=self.REGION_ORDER,
                ordered=True,
            )
            grouped = grouped.sort_values(group_column)
            grouped[group_column] = grouped[
                group_column
            ].astype(str)
        else:
            grouped = grouped.sort_values(
                "FRETE_BRUTO",
                ascending=False,
            )

        return grouped.reset_index(drop=True)

    def create_cost_stage_summary(
        self,
        result: pd.DataFrame,
    ) -> pd.DataFrame:
        dataframe = self.prepare_result(result)
        mapping = {
            "Coleta": "CUSTO_ETAPA_COLETA",
            "Entrega": "CUSTO_ETAPA_ENTREGA",
            "Terminais": "CUSTO_ETAPA_TERMINAIS",
            "Fixo das Unidades": "CUSTO_ETAPA_FIXO_UNIDADES",
            "Redespacho": "CUSTO_ETAPA_REDESPACHO",
            "Transferências": "CUSTO_ETAPA_TRANSFERENCIAS",
            "Vazios": "CUSTO_ETAPA_VAZIOS",
            "Custo Matriz": "CUSTO_ETAPA_CUSTO_MATRIZ",
        }

        return pd.DataFrame(
            {
                "ETAPA": list(mapping),
                "CUSTO": [
                    float(dataframe[column].sum())
                    for column in mapping.values()
                ],
            }
        ).sort_values(
            "CUSTO",
            ascending=False,
        )

    @staticmethod
    def _find_volume_column(
        dataframe: pd.DataFrame,
    ) -> str | None:
        for column in (
            "QTD VOLUMES",
            "QTD_VOLUMES",
            "VOLUMES",
        ):
            if column in dataframe.columns:
                return column

        return None

    @staticmethod
    def _safe_divide(
        numerator: float,
        denominator: float,
    ) -> float:
        if denominator == 0:
            return np.nan

        return float(numerator / denominator)

    @staticmethod
    def _safe_series_divide(
        numerator: pd.Series,
        denominator: pd.Series | float,
    ) -> pd.Series:
        if isinstance(denominator, pd.Series):
            safe_denominator = denominator.replace(0, np.nan)
        elif denominator == 0:
            safe_denominator = np.nan
        else:
            safe_denominator = denominator

        return numerator / safe_denominator
