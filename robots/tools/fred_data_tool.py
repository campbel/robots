"""Federal Reserve Economic Data (FRED) tool."""

import json
import os
from typing import Any, Dict, List

import pandas as pd
from fredapi import Fred

from robots.tools.base import Tool
from robots.utils.json_encoder import CustomJSONEncoder


class FredDataTool(Tool):
    """Tool for retrieving economic data from FRED."""

    @property
    def name(self) -> str:
        """Return the name of the tool."""
        return "fred_data"

    @property
    def description(self) -> str:
        """Return the description of the tool."""
        return "Get economic data from the Federal Reserve Economic Database (FRED)."

    @property
    def input_schema(self) -> Dict[str, Any]:
        """Return the input schema of the tool."""
        return {
            "type": "object",
            "properties": {
                "series_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of FRED series IDs (e.g., ['GDP', 'CPIAUCSL', 'UNRATE'])"
                },
                "observation_start": {
                    "type": "string",
                    "description": "Start date for data in format YYYY-MM-DD",
                    "default": None
                },
                "observation_end": {
                    "type": "string",
                    "description": "End date for data in format YYYY-MM-DD",
                    "default": None
                },
                "include_metadata": {
                    "type": "boolean",
                    "description": "Whether to include series metadata",
                    "default": True
                }
            },
            "required": ["series_ids"]
        }

    async def execute(self, input_data: Dict[str, Any]) -> str:
        """Execute the FRED data tool.
        
        Args:
            input_data: Contains series_ids and optional parameters.
            
        Returns:
            JSON string with economic data.
        """
        try:
            series_ids = input_data.get("series_ids", [])
            observation_start = input_data.get("observation_start", None)
            observation_end = input_data.get("observation_end", None)
            include_metadata = input_data.get("include_metadata", True)
            
            if not series_ids:
                return "Error: No series IDs provided"
            
            fred = Fred(api_key=os.environ.get("FRED_API_KEY"))
            result = {}
            
            # Get data for each series
            for series_id in series_ids:
                try:
                    data = fred.get_series(series_id, observation_start=observation_start, observation_end=observation_end)
                    # Convert the Series to a dictionary with string dates
                    data_dict = {date.strftime('%Y-%m-%d'): float(value) if not pd.isna(value) else None for date, value in data.items()}
                    
                    # Calculate summary statistics if we have data
                    summary = {}
                    if len(data) > 0:
                        # Get the most recent value
                        summary["most_recent_value"] = float(data.iloc[-1]) if not pd.isna(data.iloc[-1]) else None
                        summary["most_recent_date"] = data.index[-1].strftime('%Y-%m-%d')
                        
                        # Calculate percent changes if we have enough data
                        if len(data) > 1 and not pd.isna(data.iloc[-1]) and not pd.isna(data.iloc[-2]) and data.iloc[-2] != 0:
                            # Calculate period-over-period change
                            pop_change = float(((data.iloc[-1] / data.iloc[-2]) - 1) * 100)
                            summary["period_over_period_pct_change"] = round(pop_change, 2)
                        
                        # If we have at least a year of data
                        if len(data) >= 12 and not pd.isna(data.iloc[-1]) and not pd.isna(data.iloc[-12]) and data.iloc[-12] != 0:
                            # Calculate year-over-year change (assuming monthly data)
                            yoy_change = float(((data.iloc[-1] / data.iloc[-12]) - 1) * 100)
                            summary["year_over_year_pct_change"] = round(yoy_change, 2)
                    
                    # Get metadata and convert to serializable dict if requested
                    metadata = None
                    if include_metadata:
                        try:
                            info = fred.get_series_info(series_id)
                            metadata = {
                                "id": info.get("id", ""),
                                "title": info.get("title", ""),
                                "units": info.get("units", ""),
                                "frequency": info.get("frequency", ""),
                                "seasonal_adjustment": info.get("seasonal_adjustment", ""),
                                "notes": info.get("notes", "")
                            }
                        except Exception as e:
                            metadata = {"error": str(e)}
                    
                    result[series_id] = {
                        "series_id": series_id,
                        "data": data_dict,
                        "summary": summary,
                        "metadata": metadata
                    }
                except Exception as e:
                    result[series_id] = {"error": str(e)}
            
            return json.dumps(result, indent=2, cls=CustomJSONEncoder)
        except Exception as e:
            return f"Error: {str(e)}" 