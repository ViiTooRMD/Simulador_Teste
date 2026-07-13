from pathlib import Path

import pandas as pd

from utils.normalization import (
    normalize_column_name,
    normalize_text,
)
from utils.number_conversion import to_number
from utils.validation import validate_required_columns


class CostRepresentationRepository:
    COLUMN_MAPPING = {
        "RESP. ORIGEM": "RESP_ORIGEM",
        "RESP. DESTINO": "RESP_DESTINO",
        "ROTA": "ROTA_REPRESENTACAO",
        "COLETA": "PERC_COLETA",
        "ENTREGA": "PERC_ENTREGA",
        "TERMINAIS": "PERC_TERMINAIS",
        "FIXO DAS UNIDADES": "PERC_FIXO_UNIDADES",
        (
            "REDESPACHO COLETA/REDESPACHO ENTREGA"
        ): "PERC_REDESPACHO",
        "TRANSFERENCIAS": "PERC_TRANSFERENCIAS",
        "VAZIOS": "PERC_VAZIOS",
        "CUSTO MATRIZ": "PERC_CUSTO_MATRIZ",
        "TOTAL": "PERC_TOTAL",
    }

    PERCENTAGE_COLUMNS = [
        "PERC_COLETA",
        "PERC_ENTREGA",
        "PERC_TERMINAIS",
        "PERC_FIXO_UNIDADES",
        "PERC_REDESPACHO",
        "PERC_TRANSFERENCIAS",
        "PERC_VAZIOS",
        "PERC_CUSTO_MATRIZ",
        "PERC_TOTAL",
    ]

    STAGE_PERCENTAGE_COLUMNS = [
        column
        for column in PERCENTAGE_COLUMNS
        if column != "PERC_TOTAL"
    ]

    def __init__(
        self,
        representation_path: str,
    ) -> None:
        self.representation_path = Path(
            representation_path
        )

    def load_representations(self) -> pd.DataFrame:
        dataframe = self._load_csv(
            self.representation_path
        )

        validate_required_columns(
            dataframe=dataframe,
            required=set(self.COLUMN_MAPPING),
            file_name=self.representation_path.name,
        )

        dataframe = dataframe.rename(
            columns=self.COLUMN_MAPPING
        ).copy()

        dataframe["RESP_ORIGEM"] = dataframe[
            "RESP_ORIGEM"
        ].map(normalize_text)
        dataframe["RESP_DESTINO"] = dataframe[
            "RESP_DESTINO"
        ].map(normalize_text)
        dataframe["ROTA_REPRESENTACAO"] = dataframe[
            "ROTA_REPRESENTACAO"
        ].map(normalize_text)
        dataframe["CHAVE_ROTA_REPRESENTACAO"] = (
            dataframe["ROTA_REPRESENTACAO"]
            .str.replace(
                r"[^A-Z0-9]",
                "",
                regex=True,
            )
        )

        for column in self.PERCENTAGE_COLUMNS:
            dataframe[column] = dataframe[column].map(
                lambda value: to_number(
                    value,
                    percentage=True,
                )
            )

        self._validate_representations(dataframe)

        return dataframe[
            [
                "CHAVE_ROTA_REPRESENTACAO",
                "ROTA_REPRESENTACAO",
                "RESP_ORIGEM",
                "RESP_DESTINO",
            ]
            + self.PERCENTAGE_COLUMNS
        ].copy()

    def _validate_representations(
        self,
        dataframe: pd.DataFrame,
    ) -> None:
        if dataframe.empty:
            raise ValueError(
                f"{self.representation_path.name}: "
                "o arquivo não possui linhas."
            )

        if (
            dataframe["CHAVE_ROTA_REPRESENTACAO"] == ""
        ).any():
            raise ValueError(
                f"{self.representation_path.name}: "
                "existem rotas vazias."
            )

        duplicated = dataframe[
            "CHAVE_ROTA_REPRESENTACAO"
        ].duplicated(keep=False)

        if duplicated.any():
            routes = sorted(
                dataframe.loc[
                    duplicated,
                    "ROTA_REPRESENTACAO",
                ].unique()
            )
            raise ValueError(
                f"{self.representation_path.name}: "
                "existem rotas duplicadas: "
                f"{routes[:10]}"
            )

        percentages = dataframe[
            self.PERCENTAGE_COLUMNS
        ]

        if percentages.isna().any().any():
            raise ValueError(
                f"{self.representation_path.name}: "
                "existem percentuais inválidos."
            )

        if (percentages < 0).any().any():
            raise ValueError(
                f"{self.representation_path.name}: "
                "existem percentuais negativos."
            )

        total_invalid = (
            dataframe["PERC_TOTAL"] - 1.0
        ).abs() > 0.0003

        if total_invalid.any():
            routes = dataframe.loc[
                total_invalid,
                "ROTA_REPRESENTACAO",
            ].tolist()
            raise ValueError(
                f"{self.representation_path.name}: "
                "o Total deve ser 100% nas rotas: "
                f"{routes[:10]}"
            )

        stage_total = dataframe[
            self.STAGE_PERCENTAGE_COLUMNS
        ].sum(axis=1)
        stage_invalid = (
            stage_total - dataframe["PERC_TOTAL"]
        ).abs() > 0.0003

        if stage_invalid.any():
            routes = dataframe.loc[
                stage_invalid,
                "ROTA_REPRESENTACAO",
            ].tolist()
            raise ValueError(
                f"{self.representation_path.name}: "
                "a soma das etapas diverge do Total "
                "nas rotas: "
                f"{routes[:10]}"
            )

    def _load_csv(
        self,
        path: Path,
    ) -> pd.DataFrame:
        if not path.exists():
            raise FileNotFoundError(
                f"Arquivo não encontrado: {path.resolve()}"
            )

        attempts = [
            {"sep": ";", "encoding": "utf-8-sig"},
            {"sep": ";", "encoding": "latin1"},
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
