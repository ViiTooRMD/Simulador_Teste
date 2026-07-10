from pathlib import Path
from typing import BinaryIO

import pandas as pd

from utils.normalization import normalize_column_name, normalize_text
from utils.validation import (
    validate_non_empty_dataframe,
    validate_required_columns,
    validate_shipment_columns,
)


class FileRepository:
    def __init__(
        self,
        cities_path: str,
        costs_path: str,
    ) -> None:
        self.cities_path = Path(cities_path)
        self.costs_path = Path(costs_path)

    def load_cities(self) -> pd.DataFrame:
        dataframe = self._load_csv(self.cities_path)

        validate_required_columns(
            dataframe=dataframe,
            required={
                "CIDADE",
                "UF",
                "JAMEF",
                "CAP_INT",
            },
            file_name=self.cities_path.name,
        )

        dataframe = dataframe.copy()
        dataframe["CHAVE_CIDADE"] = dataframe["CIDADE"].map(
            normalize_text
        )
        dataframe["UF"] = dataframe["UF"].map(normalize_text)
        dataframe["JAMEF"] = dataframe["JAMEF"].map(normalize_text)
        dataframe["CAP_INT"] = dataframe["CAP_INT"].map(
            normalize_text
        )
        dataframe["REGIAO_CALC"] = dataframe["CAP_INT"].map(
            self._classify_region
        )

        return dataframe

    def load_costs(self) -> pd.DataFrame:
        dataframe = self._load_csv(self.costs_path)

        validate_required_columns(
            dataframe=dataframe,
            required={
                "ROTA",
                "PM",
                "R$_CAPITAL",
                "%_CAPITAL",
                "R$_INTERIOR",
                "%_INTERIOR",
            },
            file_name=self.costs_path.name,
        )

        dataframe = dataframe.copy()
        dataframe["ROTA"] = dataframe["ROTA"].map(normalize_text)
        dataframe["FILIAL_ORIGEM"] = dataframe[
            "FILIAL_ORIGEM"
        ].map(normalize_text)
        dataframe["FILIAL_DESTINO"] = dataframe[
            "FILIAL_DESTINO"
        ].map(normalize_text)

        return dataframe

    def get_available_origins(
        self,
        costs: pd.DataFrame,
    ) -> list[str]:
        if "FILIAL_ORIGEM" in costs.columns:
            origins = (
                costs["FILIAL_ORIGEM"]
                .dropna()
                .astype(str)
                .map(normalize_text)
                .loc[lambda series: series != ""]
                .drop_duplicates()
                .sort_values()
                .tolist()
            )
            if origins:
                return origins

        return (
            costs["ROTA"]
            .dropna()
            .astype(str)
            .str[:3]
            .drop_duplicates()
            .sort_values()
            .tolist()
        )

    def load_uploaded_shipments(
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
                    f"{parameters}: "
                    f"{type(error).__name__}: {error}"
                )

        raise ValueError(
            "Não foi possível ler o arquivo CSV.\n"
            + "\n".join(errors)
        )

    def _load_csv(self, path: Path) -> pd.DataFrame:
        if not path.exists():
            raise FileNotFoundError(
                f"Arquivo não encontrado: {path.resolve()}"
            )

        attempts = [
            {"sep": ";", "encoding": "utf-8-sig"},
            {"sep": ";", "encoding": "latin1"},
            {"sep": ",", "encoding": "utf-8-sig"},
            {"sep": ",", "encoding": "latin1"},
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
                        "O arquivo foi lido com apenas uma coluna."
                    )

                dataframe.columns = [
                    normalize_column_name(column)
                    for column in dataframe.columns
                ]

                return dataframe

            except Exception as error:
                errors.append(
                    f"{parameters}: "
                    f"{type(error).__name__}: {error}"
                )

        raise ValueError(
            f"Não foi possível ler {path.name}.\n"
            + "\n".join(errors)
        )

    @staticmethod
    def _classify_region(value: str) -> str:
        if value in {"C", "CAP", "CAPITAL"}:
            return "CAPITAL"

        if value in {"I", "INT", "INTERIOR"}:
            return "INTERIOR"

        return "NAO_IDENTIFICADA"
