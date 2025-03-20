import os
import json
from datetime import date
import anthropic
import yfinance as yf
from fredapi import Fred
import numpy as np
import pandas as pd

# Add a custom JSON encoder class
class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (np.integer, np.floating, np.bool_)):
            return obj.item()
        if isinstance(obj, pd.Timestamp):
            return obj.strftime('%Y-%m-%d')
        if pd.isna(obj):
            return None
        return super(CustomJSONEncoder, self).default(obj)

class ToolRegistry:
    def __init__(self):
        self.tools = {
            "memory": {
                "name": "memory",
                "description": "Save a message to the memory. Useful to remember context between conversations.",
                "input_schema": {
                    "type": "object",
                    "properties": {"message": {"type": "string"}}
                }
            },
            "stock_info": {
                "name": "stock_info",
                "description": "Get information about stocks using their ticker symbols.",
                "input_schema": {
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
            },
            "fred_data": {
                "name": "fred_data",
                "description": "Get economic data from the Federal Reserve Economic Database (FRED).",
                "input_schema": {
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
            }
        }
    
    async def execute(self, name, input_data):
        try:
            if name == "memory":
                with open("memory.txt", "a") as f:
                    f.write(f"---\n{input_data['message']}\n")
                return "Message added to memory"
            elif name == "stock_info":
                ticker_symbols = input_data.get("tickers", [])
                period = input_data.get("period", "1mo")
                include_info = input_data.get("info", True)
                
                if not ticker_symbols:
                    return "Error: No ticker symbols provided"
                
                result = {}
                
                # Get ticker information
                try:
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
            elif name == "fred_data":
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
            else:
                return f"Error: Tool {name} not found"
        except Exception as e:
            return f"Error: {str(e)}"
    
    def get_tools(self):
        return [{
            "name": tool,
            "description": self.tools[tool]["description"],
            "input_schema": self.tools[tool]["input_schema"]
        } for tool in self.tools]

class Chatbot:
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
        self.registry = ToolRegistry()
        self.messages = []
        
        # Initialize with system message
        memory_content = ""
        try:
            with open("memory.txt", "r") as f:
                memory_content = f.read()
        except FileNotFoundError:
            # Create the file if it doesn't exist
            with open("memory.txt", "w") as f:
                pass
        
        self.messages.append({
            "role": "user",
            "content": f"""
You are an AI chat bot named Astro, being interacted with in a terminal chat application.
You are a "robo advisor" that is helping a user manage their investments.
You can use the information to make investment recommendations or answer user questions.

<current_date>
{date.today().strftime("%m/%d/%Y")}
</current_date>

<memory>
{memory_content}
</memory>

<capabilities>
You have access to real-time stock market data through yfinance. 
You can retrieve historical stock prices, company information, and performance metrics for any publicly traded company.
When users ask about stock performance or specific companies, use the stock_info tool to get accurate information.

You also have access to economic data from the Federal Reserve Economic Database (FRED).
You can retrieve data for economic indicators like GDP, inflation rates, unemployment rates, and more.
When users ask about economic indicators or trends, use the fred_data tool to get accurate information.

<fred_series_reference>
Common FRED Series IDs:
- GDP: Gross Domestic Product (Quarterly)
- GDPC1: Real Gross Domestic Product (Quarterly)
- CPIAUCSL: Consumer Price Index for All Urban Consumers (Monthly)
- CPILFESL: Core Consumer Price Index (Monthly, excludes food and energy)
- UNRATE: Unemployment Rate (Monthly)
- FEDFUNDS: Federal Funds Effective Rate (Monthly)
- DGS10: 10-Year Treasury Constant Maturity Rate (Daily)
- HOUST: Housing Starts (Monthly)
- INDPRO: Industrial Production Index (Monthly)
- PCE: Personal Consumption Expenditures (Monthly)
- RSAFS: Retail Sales (Monthly)
- MORTGAGE30US: 30-Year Fixed Rate Mortgage Average (Weekly)
- SP500: S&P 500 Index (Daily)
- NASDAQCOM: NASDAQ Composite Index (Daily)
- DJIA: Dow Jones Industrial Average (Daily)
</fred_series_reference>
</capabilities>

<behavior>
Use a professional and friendly tone in communication.
When you are not sure about the answer, say so.
For stock recommendations, always consider the user's specific needs and preferences if known.
When providing stock information, include relevant metrics like recent performance and company details.

When discussing economic data:
- Focus on trends rather than single data points
- Explain the significance of economic indicators in a clear, accessible way
- Consider how economic factors may affect investment decisions
- Relate economic data to potential market impacts when appropriate
</behavior>

<style>
Use plain text in communication.
If you want to provide emphasis, use *asterisks* around the text.
Use spacing and newlines to make the text easier to read.
</style>
            """.strip()
        })
    
    async def send_message(self, message):
        result = []
        
        self.messages.append({
            "role": "user",
            "content": message
        })
        
        tool_used = True
        while tool_used:
            tool_used = False
            
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",  # 'claude-3-7-sonnet-20250219'
                max_tokens=8192,
                system="You are an AI chat bot named Astro...",
                messages=self.messages,
                tools=self.registry.get_tools()
            )
            
            for content in response.content:
                if content.type == "text":
                    self.messages.append({
                        "role": "assistant",
                        "content": content.text
                    })
                    result.append(content.text)
                elif content.type == "tool_use":
                    tool_used = True
                    self.messages.append({
                        "role": "assistant",
                        "content": [{
                            "type": "tool_use",
                            "id": content.id,
                            "name": content.name,
                            "input": content.input
                        }]
                    })
                    
                    tool_result = await self.registry.execute(content.name, content.input)
                    
                    self.messages.append({
                        "role": "user",
                        "content": [{
                            "type": "tool_result",
                            "tool_use_id": content.id,
                            "content": tool_result
                        }]
                    })
        
        return "\n".join(result)

async def main():
    bot = Chatbot()
    
    while True:
        user_input = input("You: ")
        print("")
        response = await bot.send_message(user_input)
        print("Astro:", response)
        print("")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
