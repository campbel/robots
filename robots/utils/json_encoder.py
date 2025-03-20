"""Custom JSON encoder for handling non-serializable types."""

import json
import numpy as np
import pandas as pd


class CustomJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder to handle numpy and pandas objects."""
    
    def default(self, obj):
        """Override the default method to handle non-serializable types."""
        if isinstance(obj, (np.integer, np.floating, np.bool_)):
            return obj.item()
        if isinstance(obj, pd.Timestamp):
            return obj.strftime('%Y-%m-%d')
        if pd.isna(obj):
            return None
        return super(CustomJSONEncoder, self).default(obj) 