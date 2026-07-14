from io import BytesIO

import pandas as pd


class ExportService:
    @staticmethod
    def to_excel(
        result_dataframe: pd.DataFrame,
        cost_summary_dataframe: pd.DataFrame,
        freight_summary_dataframe: pd.DataFrame,
        discount_summary_dataframe: pd.DataFrame,
        financial_summary_dataframe: pd.DataFrame,
        margin_summary_dataframe: pd.DataFrame,
        errors_dataframe: pd.DataFrame,
    ) -> bytes:
        output = BytesIO()

        with pd.ExcelWriter(
            output,
            engine="openpyxl",
        ) as writer:
            result_dataframe.to_excel(
                writer,
                sheet_name="Resultado_Detalhado",
                index=False,
            )

            cost_summary_dataframe.to_excel(
                writer,
                sheet_name="Resumo_Custo",
                index=False,
            )

            freight_summary_dataframe.to_excel(
                writer,
                sheet_name="Resumo_Frete",
                index=False,
            )

            discount_summary_dataframe.to_excel(
                writer,
                sheet_name="Resumo_Descontos",
                index=False,
            )

            financial_summary_dataframe.to_excel(
                writer,
                sheet_name="Resumo_Financeiro",
                index=False,
            )

            margin_summary_dataframe.to_excel(
                writer,
                sheet_name="Resumo_Margens",
                index=False,
            )

            errors_dataframe.to_excel(
                writer,
                sheet_name="Erros",
                index=False,
            )

        output.seek(0)

        return output.getvalue()
