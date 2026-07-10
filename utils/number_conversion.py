import numpy as np
import pandas as pd


def to_number(
    value: object,
    percentage: bool = False,
) -> float:
    if value is None or pd.isna(value):
        return 0.0

    if isinstance(
        value,
        (int, float, np.number),
    ):
        number = float(value)
    else:
        text = str(value).strip()

        if text.upper() in {
            "",
            "-",
            "NAN",
            "NONE",
        }:
            return 0.0

        text = (
            text
            .replace("R$", "")
            .replace("%", "")
            .replace(" ", "")
        )

        if "." in text and "," in text:
            text = (
                text
                .replace(".", "")
                .replace(",", ".")
            )
        elif "," in text:
            text = text.replace(",", ".")

        number = float(text)

    if percentage:
        return number / 100.0

    return number
