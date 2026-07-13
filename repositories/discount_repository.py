from pathlib import Path

import pandas as pd

from utils.normalization import (
    normalize_column_name,
    normalize_text,
)
from utils.number_conversion import to_number
from utils.validation import validate_required_columns


class DiscountRepository:
    AUTHORITY_REQUIRED_COLUMNS = {
        "ORDEM",
        "COD_PERFIL",
        "PERFIL",
        "DESCONTO_MAX_FRETE_PESO",
        "DESCONTO_MAX_AD_VALOREM",
        "PODE_APROVAR",
        "ATIVO",
    }
    POLICY_REQUIRED_COLUMNS = {
        "ID_POLITICA",
        "REGIAO",
        "UF",
        "FAIXA_PESO",
        "DESCONTO_FRETE_PESO",
        "DESCONTO_AD_VALOREM",
        "ATIVO",
        "OBSERVACAO",
    }

    def __init__(
        self,
        authorities_path: str,
        policies_path: str,
    ) -> None:
        self.authorities_path = Path(authorities_path)
        self.policies_path = Path(policies_path)

    def load_authorities(self) -> pd.DataFrame:
        dataframe = self._load_csv(self.authorities_path)
        validate_required_columns(
            dataframe=dataframe,
            required=self.AUTHORITY_REQUIRED_COLUMNS,
            file_name=self.authorities_path.name,
        )

        dataframe = dataframe.copy()
        dataframe["ORDEM"] = dataframe["ORDEM"].map(to_number)
        for column in (
            "COD_PERFIL",
            "PERFIL",
            "PODE_APROVAR",
            "ATIVO",
        ):
            dataframe[column] = dataframe[column].map(
                normalize_text
            )
        for column in (
            "DESCONTO_MAX_FRETE_PESO",
            "DESCONTO_MAX_AD_VALOREM",
        ):
            dataframe[column] = dataframe[column].map(
                lambda value: to_number(value, percentage=True)
            )

        if dataframe["COD_PERFIL"].duplicated().any():
            raise ValueError(
                f"{self.authorities_path.name}: "
                "existem perfis duplicados."
            )

        self._validate_discount_range(
            dataframe,
            [
                "DESCONTO_MAX_FRETE_PESO",
                "DESCONTO_MAX_AD_VALOREM",
            ],
            self.authorities_path.name,
        )
        return dataframe.sort_values("ORDEM").reset_index(drop=True)

    def load_policies(self) -> pd.DataFrame:
        dataframe = self._load_csv(self.policies_path)
        return self.prepare_policies(dataframe)

    def prepare_policies(
        self,
        dataframe: pd.DataFrame,
    ) -> pd.DataFrame:
        prepared = dataframe.copy()
        prepared.columns = [
            normalize_column_name(column)
            for column in prepared.columns
        ]
        validate_required_columns(
            dataframe=prepared,
            required=self.POLICY_REQUIRED_COLUMNS,
            file_name=self.policies_path.name,
        )

        for column in (
            "ID_POLITICA",
            "REGIAO",
            "UF",
            "FAIXA_PESO",
            "ATIVO",
            "OBSERVACAO",
        ):
            prepared[column] = prepared[column].map(normalize_text)

        for column in (
            "REGIAO",
            "UF",
            "FAIXA_PESO",
        ):
            prepared[column] = prepared[column].replace("", "TODAS")

        for column in (
            "DESCONTO_FRETE_PESO",
            "DESCONTO_AD_VALOREM",
        ):
            prepared[column] = prepared[column].map(
                self._parse_discount
            )

        if prepared["ID_POLITICA"].duplicated().any():
            raise ValueError(
                f"{self.policies_path.name}: "
                "existem IDs de política duplicados."
            )

        self._validate_discount_range(
            prepared,
            [
                "DESCONTO_FRETE_PESO",
                "DESCONTO_AD_VALOREM",
            ],
            self.policies_path.name,
        )
        return prepared.reset_index(drop=True)

    def serialize_policies(
        self,
        dataframe: pd.DataFrame,
    ) -> bytes:
        prepared = self.prepare_policies(dataframe)
        output = prepared.copy()

        for column in (
            "DESCONTO_FRETE_PESO",
            "DESCONTO_AD_VALOREM",
        ):
            output[column] = output[column].map(
                lambda value: (
                    f"{value * 100:.2f}%".replace(".", ",")
                )
            )

        return output.to_csv(
            sep=";",
            index=False,
            encoding="utf-8-sig",
        ).encode("utf-8-sig")

    @staticmethod
    def _parse_discount(value: object) -> float:
        if isinstance(value, (int, float)):
            number = float(value)
            return number if number <= 1 else number / 100

        text = str(value).strip()
        if "%" in text:
            return to_number(text, percentage=True)

        number = to_number(text)
        return number if number <= 1 else number / 100

    @staticmethod
    def _validate_discount_range(
        dataframe: pd.DataFrame,
        columns: list[str],
        file_name: str,
    ) -> None:
        values = dataframe[columns]
        if values.isna().any().any():
            raise ValueError(
                f"{file_name}: existem descontos inválidos."
            )
        if ((values < 0) | (values > 1)).any().any():
            raise ValueError(
                f"{file_name}: descontos devem estar entre 0% e 100%."
            )

    @staticmethod
    def _load_csv(path: Path) -> pd.DataFrame:
        if not path.exists():
            raise FileNotFoundError(
                f"Arquivo não encontrado: {path.resolve()}"
            )

        errors: list[str] = []
        for encoding in ("utf-8-sig", "latin1"):
            try:
                dataframe = pd.read_csv(
                    path,
                    sep=";",
                    encoding=encoding,
                    dtype=str,
                    keep_default_na=False,
                )
                dataframe.columns = [
                    normalize_column_name(column)
                    for column in dataframe.columns
                ]
                return dataframe
            except Exception as error:
                errors.append(
                    f"{encoding}: {type(error).__name__}: {error}"
                )

        raise ValueError(
            f"Não foi possível ler {path.name}.\n"
            + "\n".join(errors)
        )
