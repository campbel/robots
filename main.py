import os
import json
from datetime import date
import anthropic
import yfinance as yf

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
                    
                    return json.dumps(result, indent=2)
                except Exception as e:
                    return f"Error retrieving stock data: {str(e)}"
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
</capabilities>

<behavior>
Use a professional and friendly tone in communication.
When you are not sure about the answer, say so.
For stock recommendations, always consider the user's specific needs and preferences if known.
When providing stock information, include relevant metrics like recent performance and company details.
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
