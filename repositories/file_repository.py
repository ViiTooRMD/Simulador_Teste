from pathlib import Path
from typing import BinaryIO

import pandas as pd

from utils.normalization import normalize_column_name, normalize_text
from utils.validation import (
    validate_non_empty_dataframe,
    validate_required_columns,
    validate_shipment_columns,
)def load_uploaded_shipments(
    self,
    uploaded_file: BinaryIO,
    file_name: str,
) -> pd.DataFrame:
    extension = Path(file_name).suffix.lower()

    if extension == ".xlsx":
        dataframe = pd.read_excel(
            uploaded_file,
            sheet_name="Volumetria",
            dtype={
                "ORIGEM": str,
                "CIDADE DESTINO": str,
                "UF": str,
            },
        )

    elif extension == ".csv":
        dataframe = self._load_uploaded_csv(uploaded_file)

    else:
        raise ValueError(
            "Formato não suportado. Utilize um arquivo XLSX ou CSV."
        )

    dataframe.columns = [
        normalize_column_name(column)
        for column in dataframe.columns
    ]

    validate_non_empty_dataframe(
        dataframe=dataframe,
        file_name=file_name,
    )

    validate_shipment_columns(
        dataframe=dataframe,
        file_name=file_name,
    )

    return dataframe


def _load_uploaded_csv(
    self,
    uploaded_file: BinaryIO,
) -> pd.DataFrame:
    attempts = [
        {"sep": ";", "encoding": "utf-8-sig"},
        {"sep": ";", "encoding": "latin1"},
        {"sep": ",", "encoding": "utf-8-sig"},
        {"sep": ",", "encoding": "latin1"},
    ]

    errors: list[str] = []

    for parameters in attempts:
        try:
            uploaded_file.seek(0)

            dataframe = pd.read_csv(
                uploaded_file,
                dtype=str,
                keep_default_na=False,
                **parameters,
            )

            if len(dataframe.columns) <= 1:
                raise ValueError(
                    "O arquivo foi lido com apenas uma coluna."
                )

            return dataframe

        except Exception as error:
            errors.append(
                f"{parameters}: {type(error).__name__}: {error}"
            )

    raise ValueError(
        "Não foi possível ler o arquivo CSV.\n"
        + "\n".join(errors)
    )
