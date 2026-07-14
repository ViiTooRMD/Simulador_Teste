import numpy as np
import pandas as pd

from utils.number_conversion import to_number


class FinancialService:
    ANNUAL_SELIC_RATE = 0.1425

    @property
    def monthly_rate(self) -> float:
        return (1 + self.ANNUAL_SELIC_RATE) ** (1 / 12) - 1

    def calculate_batch(
        self,
        result: pd.DataFrame,
        payment_days: int,
    ) -> pd.DataFrame:
        dataframe = result.copy()
        freight = dataframe["FRETE_SIMULADO"].map(to_number)
        proportional_rate = self.monthly_rate * (
            float(payment_days) / 30.0
        )
        dataframe["TAXA_SELIC_ANUAL"] = self.ANNUAL_SELIC_RATE
        dataframe["TAXA_FINANCEIRA_MENSAL"] = self.monthly_rate
        dataframe["TAXA_FINANCEIRA_APROPRIADA"] = proportional_rate
        dataframe["IMPACTO_FINANCEIRO_RS"] = freight * proportional_rate
        dataframe["LAJIR_APOS_FINANCEIRO_RS"] = (
            dataframe["LAJIR_RS"].map(to_number)
            - dataframe["IMPACTO_FINANCEIRO_RS"]
        )
        dataframe["LAJIR_APOS_FINANCEIRO_PCT"] = np.where(
            freight != 0,
            dataframe["LAJIR_APOS_FINANCEIRO_RS"] / freight,
            np.nan,
        )
        return dataframe

    def create_summary(self, result: pd.DataFrame) -> pd.DataFrame:
        freight = float(result["FRETE_SIMULADO"].map(to_number).sum())
        impact = float(result["IMPACTO_FINANCEIRO_RS"].map(to_number).sum())
        adjusted = float(
            result["LAJIR_APOS_FINANCEIRO_RS"].map(to_number).sum()
        )
        return pd.DataFrame(
            [{
                "FRETE_SIMULADO_TOTAL": freight,
                "TAXA_SELIC_ANUAL": self.ANNUAL_SELIC_RATE,
                "TAXA_FINANCEIRA_MENSAL": self.monthly_rate,
                "IMPACTO_FINANCEIRO_TOTAL": impact,
                "LAJIR_APOS_FINANCEIRO_RS": adjusted,
                "LAJIR_APOS_FINANCEIRO_PCT": (
                    adjusted / freight if freight else np.nan
                ),
            }]
        )
