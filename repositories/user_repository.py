from pathlib import Path

import pandas as pd

from utils.normalization import (
    normalize_column_name,
    normalize_text,
)
from utils.validation import validate_required_columns


class UserRepository:
    REQUIRED_COLUMNS = {
        "ID_USUARIO",
        "NOME",
        "EMAIL",
        "SENHA_SALT",
        "SENHA_HASH",
        "COD_PERFIL",
        "REGIAO",
        "UF",
        "FILIAL",
        "ADMIN",
        "ATIVO",
    }

    def __init__(self, users_path: str) -> None:
        self.users_path = Path(users_path)

    def load_users(self) -> pd.DataFrame:
        dataframe = self._load_csv(self.users_path)
        validate_required_columns(
            dataframe=dataframe,
            required=self.REQUIRED_COLUMNS,
            file_name=self.users_path.name,
        )

        dataframe = dataframe.copy()
        dataframe["EMAIL"] = (
            dataframe["EMAIL"]
            .astype(str)
            .str.strip()
            .str.lower()
        )

        for column in (
            "ID_USUARIO",
            "NOME",
            "COD_PERFIL",
            "REGIAO",
            "UF",
            "FILIAL",
            "ADMIN",
            "ATIVO",
        ):
            dataframe[column] = dataframe[column].map(
                normalize_text
            )

        if dataframe["EMAIL"].duplicated().any():
            raise ValueError(
                f"{self.users_path.name}: existem e-mails duplicados."
            )

        if dataframe["ID_USUARIO"].duplicated().any():
            raise ValueError(
                f"{self.users_path.name}: existem IDs duplicados."
            )

        if (
            (dataframe["EMAIL"] == "")
            | (dataframe["COD_PERFIL"] == "")
        ).any():
            raise ValueError(
                f"{self.users_path.name}: "
                "e-mail e perfil são obrigatórios."
            )

        return dataframe

    def _load_csv(self, path: Path) -> pd.DataFrame:
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
