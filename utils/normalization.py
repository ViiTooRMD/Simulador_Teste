import re
import unicodedata

import pandas as pd


def normalize_text(value: object) -> str:
    if value is None or pd.isna(value):
        return ""

    text = str(value).strip().upper()
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", errors="ignore").decode("utf-8")
    text = re.sub(r"\s+", " ", text)

    return text


def normalize_column_name(value: object) -> str:
    return normalize_text(value)
