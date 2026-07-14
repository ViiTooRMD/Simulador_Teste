import pandas as pd


SHIPMENT_REQUIRED_COLUMNS = {
    "CIDADE DESTINO",
    "UF",
    "PESO REAL",
    "VALOR MERCADORIA",
}


def validate_required_columns(
    dataframe: pd.DataFrame,
    required: set[str],
    file_name: str,
) -> None:
    found = set(dataframe.columns)
    missing = required - found

    if missing:
        raise ValueError(
            f"{file_name}: colunas obrigatórias ausentes: "
            f"{sorted(missing)}. "
            f"Colunas encontradas: {sorted(found)}"
        )


def validate_shipment_columns(
    dataframe: pd.DataFrame,
    file_name: str = "Volumetria",
) -> None:
    validate_required_columns(
        dataframe=dataframe,
        required=SHIPMENT_REQUIRED_COLUMNS,
        file_name=file_name,
    )
    cubage_columns = {
        "PESO CUBADO",
        "M3",
        "M³",
        "VOLUME M3",
        "VOLUME_M3",
    }
    if not cubage_columns.intersection(dataframe.columns):
        raise ValueError(
            f"{file_name}: informe PESO CUBADO ou M³."
        )


def validate_non_empty_dataframe(
    dataframe: pd.DataFrame,
    file_name: str = "Volumetria",
) -> None:
    if dataframe.empty:
        raise ValueError(
            f"{file_name}: "
            "o arquivo não possui linhas para processamento."
        )
