import math
import re
from typing import Any

import numpy as np
import pandas as pd


EMPTY_VALUES = {
    "",
    "-",
    "--",
    "NAN",
    "NONE",
    "NULL",
    "N/A",
    "NA",
}


def to_number(
    value: Any,
    percentage: bool = False,
    default: float = 0.0,
) -> float:
    """
    Converte valores numéricos brasileiros e internacionais.

    Exemplos aceitos:
    - 1234.56
    - 1234,56
    - 1.234,56
    - R$ 3,14
    - 0,45%
    - célula vazia
    - None
    - NaN
    """

    if value is None:
        return default

    try:
        if pd.isna(value):
            return default
    except (TypeError, ValueError):
        pass

    if isinstance(value, (int, float, np.integer, np.floating)):
        number = float(value)

        if math.isnan(number) or math.isinf(number):
            return default

        return number / 100.0 if percentage else number

    text = str(value).strip()

    if text.upper() in EMPTY_VALUES:
        return default

    text = (
        text
        .replace("R$", "")
        .replace("%", "")
        .replace("\u00a0", "")
        .replace(" ", "")
        .strip()
    )

    if text.upper() in EMPTY_VALUES:
        return default

    # Mantém somente números, sinais e separadores.
    text = re.sub(r"[^0-9,\.\-+]", "", text)

    if text in {"", "-", "+", ".", ","}:
        return default

    # Padrão brasileiro: 1.234,56
    if "." in text and "," in text:
        last_dot = text.rfind(".")
        last_comma = text.rfind(",")

        if last_comma > last_dot:
            text = text.replace(".", "")
            text = text.replace(",", ".")
        else:
            text = text.replace(",", "")

    # Somente vírgula: 1234,56
    elif "," in text:
        text = text.replace(".", "")
        text = text.replace(",", ".")

    try:
        number = float(text)
    except (TypeError, ValueError):
        return default

    if math.isnan(number) or math.isinf(number):
        return default

    if percentage:
        return number / 100.0

    return number
