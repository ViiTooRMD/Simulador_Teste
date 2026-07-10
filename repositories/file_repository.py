from pathlib import Path
from typing import BinaryIO

import pandas as pd

from utils.normalization import normalize_column_name, normalize_text
from utils.validation import (
    validate_non_empty_dataframe,
    validate_required_columns,
    validate_shipment_columns,
)
