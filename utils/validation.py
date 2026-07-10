import pandas as pd


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
