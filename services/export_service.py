from io import BytesIO

import pandas as pd


class ExportService:
    @staticmethod
    def to_excel(
        result_dataframe: pd.DataFrame,
        summary_dataframe: pd.DataFrame,
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

            summary_dataframe.to_excel(
                writer,
                sheet_name="Resumo",
                index=False,
            )

        output.seek(0)

        return output.getvalue()
