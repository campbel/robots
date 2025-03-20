"""Stock information tool using yfinance."""

import json
from typing import Any, Dict, List

import yfinance as yf

from robots.tools.base import Tool
from robots.utils.json_encoder import CustomJSONEncoder


class StockInfoTool(Tool):
    """Tool for retrieving stock market information."""

    @property
    def name(self) -> str:
        """Return the name of the tool."""
        return "stock_info"

    @property
    def description(self) -> str:
        """Return the description of the tool."""
        return "Get information about stocks using their ticker symbols."

    @property
    def input_schema(self) -> Dict[str, Any]:
        """Return the input schema of the tool."""
        return {
            "type": "object",
            "properties": {
                "tickers": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of ticker symbols (e.g., ['AAPL', 'MSFT', 'GOOG'])"
                },
                "period": {
                    "type": "string",
                    "description": "Time period for historical data (e.g., '1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', 'max')",
                    "default": "1mo"
                },
                "info": {
                    "type": "boolean",
                    "description": "Whether to include company information",
                    "default": True
                }
            },
            "required": ["tickers"]
        }

    async def execute(self, input_data: Dict[str, Any]) -> str:
        """Execute the stock info tool.
        
        Args:
            input_data: Contains tickers, period, and info flag.
            
        Returns:
            JSON string with stock information.
        """
        try:
            ticker_symbols = input_data.get("tickers", [])
            period = input_data.get("period", "1mo")
            include_info = input_data.get("info", True)
            
            if not ticker_symbols:
                return "Error: No ticker symbols provided"
            
            result = {}
            
            # Get ticker information
            tickers = yf.Tickers(" ".join(ticker_symbols))
            
            # Get historical data
            hist_data = yf.download(ticker_symbols, period=period)
            
            # Format the result
            result["historical"] = {
                "start_date": hist_data.index[0].strftime("%Y-%m-%d"),
                "end_date": hist_data.index[-1].strftime("%Y-%m-%d"),
                "tickers": {}
            }
            
            # Add last price for each ticker
            for ticker in ticker_symbols:
                result["historical"]["tickers"][ticker] = {
                    "last_price": round(float(hist_data['Close'][ticker].iloc[-1]), 2) if ticker in hist_data else None,
                    "change_percent": round(float(100 * (hist_data['Close'][ticker].iloc[-1] / hist_data['Close'][ticker].iloc[0] - 1)), 2) if ticker in hist_data else None
                }
            
            # Add company info if requested
            if include_info:
                result["info"] = {}
                for ticker in ticker_symbols:
                    try:
                        info = tickers.tickers[ticker].info
                        result["info"][ticker] = {
                            "name": info.get("shortName"),
                            "sector": info.get("sector"),
                            "industry": info.get("industry"),
                            "website": info.get("website"),
                            "market_cap": info.get("marketCap"),
                            "pe_ratio": info.get("trailingPE")
                        }
                    except Exception as e:
                        result["info"][ticker] = {"error": str(e)}
            
            return json.dumps(result, indent=2, cls=CustomJSONEncoder)
        except Exception as e:
            return f"Error retrieving stock data: {str(e)}" 