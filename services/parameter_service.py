import pandas as pd

from utils.normalization import normalize_column_name
from utils.number_conversion import to_number


class ParameterService:
    M3_COLUMNS = ("M3", "M³", "VOLUME M3", "VOLUME_M3")

    def prepare_shipments(
        self,
        shipments: pd.DataFrame,
        origin: str,
        customer_pays_cubage: bool,
        cubage_density: float,
        payment_days: int,
        simulated_months: int,
    ) -> pd.DataFrame:
        dataframe = shipments.copy()
        dataframe.columns = [
            normalize_column_name(column)
            for column in dataframe.columns
        ]
        dataframe["ORIGEM"] = origin

        if "PESO CUBADO" not in dataframe.columns:
            dataframe["PESO CUBADO"] = 0.0

        m3_column = self._find_m3_column(dataframe)
        m3_values = (
            dataframe[m3_column].map(to_number)
            if m3_column
            else pd.Series(0.0, index=dataframe.index)
        )
        cubed_weight = dataframe["PESO CUBADO"].map(to_number)

        if customer_pays_cubage:
            invalid = m3_values <= 0
            if invalid.any():
                self._raise_missing_basis(dataframe, invalid, "M³")
            cubed_weight = m3_values * float(cubage_density)
            source = "M3_X_DENSIDADE_PARAMETRIZADA"
        else:
            missing_cubed = cubed_weight <= 0
            fallback = missing_cubed & (m3_values > 0)
            cubed_weight.loc[fallback] = m3_values.loc[fallback] * 300.0
            invalid = cubed_weight <= 0
            if invalid.any():
                self._raise_missing_basis(
                    dataframe,
                    invalid,
                    "PESO CUBADO ou M³",
                )
            source = "PESO_CUBADO_INFORMADO_OU_M3_X_300"

        dataframe["PESO CUBADO"] = cubed_weight
        dataframe["M3_CALCULO"] = m3_values
        dataframe["CLIENTE_PAGA_CUBAGEM"] = (
            "S" if customer_pays_cubage else "N"
        )
        dataframe["DENSIDADE_CUBAGEM"] = (
            float(cubage_density)
            if customer_pays_cubage
            else 300.0
        )
        dataframe["FONTE_PESO_CUBADO"] = source
        dataframe["DIAS_PAGAMENTO"] = int(payment_days)
        dataframe["MESES_SIMULADOS"] = int(simulated_months)
        return dataframe

    @classmethod
    def _find_m3_column(cls, dataframe: pd.DataFrame) -> str | None:
        for column in cls.M3_COLUMNS:
            normalized = normalize_column_name(column)
            if normalized in dataframe.columns:
                return normalized
        return None

    @staticmethod
    def _raise_missing_basis(
        dataframe: pd.DataFrame,
        invalid: pd.Series,
        required: str,
    ) -> None:
        identifiers = (
            dataframe.loc[invalid, "ID_EMBARQUE"].astype(str).tolist()
            if "ID_EMBARQUE" in dataframe.columns
            else [str(index + 1) for index in dataframe.index[invalid]]
        )
        sample = ", ".join(identifiers[:5])
        raise ValueError(
            f"Informe {required} para calcular a cubagem. "
            f"Embarque(s): {sample}."
        )
