import threading
from typing import Optional

import pandas as pd
from django.conf import settings

from analytics.utils.data_loader import load_dataset_from_path

class DataRepository:
    """
    Simple in-memory store for the active dataset.
    Thread-safe enough for typical small deployments.
    """

    _lock = threading.Lock()
    _df: Optional[pd.DataFrame] = None
    _path: Optional[str] = None

    @classmethod
    def get_dataframe(cls) -> pd.DataFrame:
        with cls._lock:
            if cls._df is None:
                cls._path = settings.DEFAULT_DATASET_PATH
                cls._df = load_dataset_from_path(cls._path)
            return cls._df

    @classmethod
    def replace_with_file(cls, file_path: str) -> pd.DataFrame:
        with cls._lock:
            df = load_dataset_from_path(file_path)
            cls._df = df
            cls._path = file_path
            return df

    @classmethod
    def get_current_path(cls) -> Optional[str]:
        with cls._lock:
            return cls._path
