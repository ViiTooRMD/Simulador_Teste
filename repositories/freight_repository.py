from pathlib import Path

import pandas as pd

from utils.normalization import (
    normalize_column_name,
    normalize_text,
)
from utils.validation import validate_required_columns


class FreightRepository:
    COLUMN_MAPPING = {
        "10-FRETE PESO": "FRETE_FAIXA_10",
        "20-FRETE PESO": "FRETE_FAIXA_20",
        "30-FRETE PESO": "FRETE_FAIXA_30",
        "50-FRETE PESO": "FRETE_FAIXA_50",
        "75-FRETE PESO": "FRETE_FAIXA_75",
        "100-FRETE PESO": "FRETE_FAIXA_100",
        "999,999,999.9999-FRETE PESO": (
            "FRETE_KG_ACIMA_100"
        ),
        "999,999,999.9999-FRETE VALOR": (
            "PERCENTUAL_AD_VALOREM"
        ),
    }

    def __init__(
        self,
        freight_table_path: str,
    ) -> None:
        self.freight_table_path = Path(
            freight_table_path
        )

    def load_freight_table(
        self,
    ) -> pd.DataFrame:
        dataframe = self._load_csv(
            self.freight_table_path
        )

        validate_required_columns(
            dataframe=dataframe,
            required={
                "ROTA",
                "ORIGEM",
                "DESTINO",
                "10-FRETE PESO",
                "20-FRETE PESO",
                "30-FRETE PESO",
                "50-FRETE PESO",
                "75-FRETE PESO",
                "100-FRETE PESO",
                "999,999,999.9999-FRETE PESO",
                "999,999,999.9999-FRETE VALOR",
            },
            file_name=self.freight_table_path.name,
        )

        dataframe = dataframe.rename(
            columns=self.COLUMN_MAPPING
        ).copy()

        dataframe["ROTA"] = (
            dataframe["ROTA"]
            .fillna("")
            .map(normalize_text)
            .str.replace(" ", "", regex=False)
        )

        dataframe["ORIGEM"] = (
            dataframe["ORIGEM"]
            .fillna("")
            .map(normalize_text)
            .str.replace(" ", "", regex=False)
        )

        dataframe["DESTINO"] = (
            dataframe["DESTINO"]
            .fillna("")
            .map(normalize_text)
            .str.replace(" ", "", regex=False)
        )

        dataframe = dataframe[
            dataframe["ROTA"] != ""
        ].copy()

        duplicated_routes = dataframe[
            dataframe["ROTA"].duplicated(
                keep=False
            )
        ]

        if not duplicated_routes.empty:
            duplicated_values = sorted(
                duplicated_routes["ROTA"]
                .drop_duplicates()
                .tolist()
            )

            raise ValueError(
                "A tabela padrão possui rotas duplicadas: "
                f"{duplicated_values[:20]}"
            )

        return dataframe

    def _load_csv(
        self,
        path: Path,
    ) -> pd.DataFrame:
        if not path.exists():
            raise FileNotFoundError(
                f"Arquivo não encontrado: "
                f"{path.resolve()}"
            )

        attempts = [
            {
                "sep": ";",
                "encoding": "utf-8-sig",
            },
            {
                "sep": ";",
                "encoding": "latin1",
            },
            {
                "sep": ",",
                "encoding": "utf-8-sig",
            },
            {
                "sep": ",",
                "encoding": "latin1",
            },
        ]

        errors: list[str] = []

        for parameters in attempts:
            try:
                dataframe = pd.read_csv(
                    path,
                    dtype=str,
                    keep_default_na=False,
                    **parameters,
                )

                if len(dataframe.columns) <= 1:
                    raise ValueError(
                        "O arquivo foi lido com apenas "
                        "uma coluna. Verifique o separador."
                    )

                dataframe.columns = [
                    normalize_column_name(column)
                    for column in dataframe.columns
                ]

                return dataframe

            except Exception as error:
                errors.append(
                    f"{parameters}: "
                    f"{type(error).__name__}: "
                    f"{error}"
                )

        raise ValueError(
            f"Não foi possível ler "
            f"{path.name}.\n"
            + "\n".join(errors)
        )
