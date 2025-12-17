# =============================================================================
# BASE STRATEGY
# =============================================================================
from abc import ABC, abstractmethod
import pandas as pd


class BaseStrategy(ABC):
    name = "base"
    required_columns = ["time", "open", "high", "low", "close", "volume"]

    def _validate_dataframe(self, df):
        """Validate DataFrame has required columns and sufficient data"""
        if df is None or df.empty:
            return False, "DataFrame rỗng"
        
        missing_cols = [col for col in self.required_columns if col not in df.columns]
        if missing_cols:
            return False, f"Thiếu cột: {', '.join(missing_cols)}"
        
        return True, None

    def _serialize_value(self, value):
        """Convert pandas/numpy types to JSON-serializable types"""
        if pd.isna(value):
            return None
        if isinstance(value, (pd.Timestamp, pd.DatetimeTZDtype)):
            return value.isoformat()
        if hasattr(value, 'item'):  # numpy types
            return value.item()
        return value

    def _serialize_row(self, row, columns):
        """Serialize a DataFrame row to dict"""
        result = {}
        for col in columns:
            if col in row.index:
                value = row[col]
                if col == 'time':
                    result[col] = value.isoformat() if hasattr(value, 'isoformat') else str(value)
                else:
                    result[col] = self._serialize_value(value)
        return result

    @abstractmethod
    def apply(self, df):
        """
        Apply strategy to DataFrame
        
        Returns:
        {
            "signals": [],  # List of signal dicts
            "meta": {}      # Metadata about the analysis
        }
        """
        pass
