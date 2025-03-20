"""Chatbot implementation for interacting with users and executing tools."""

import os
from datetime import date
from typing import Any, Dict, List

import anthropic

from robots.registry import ToolRegistry


class Chatbot:
    """Chatbot for interacting with users and executing tools."""

    def __init__(self, registry: ToolRegistry):
        """Initialize the chatbot.
        
        Args:
            registry: The tool registry to use for executing tools.
        """
        self.client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
        self.registry = registry
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

        user_info = ""
        try:
            with open("user_info.md", "r") as f:
                user_info = f.read()
        except FileNotFoundError:
            # Create the file if it doesn't exist
            with open("user_info.md", "w") as f:
                pass
        
        history = ""
        try:
            with open("history.txt", "r") as f:
                history = f.read()
        except FileNotFoundError:
            # Create the file if it doesn't exist
            with open("history.txt", "w") as f:
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

<user_info>
{user_info}
</user_info>

<history>
{history}
</history>

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
    
    async def send_message(self, message: str) -> str:
        """Send a message to the chatbot and get a response.
        
        Args:
            message: The message to send.
            
        Returns:
            The chatbot's response.
        """
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
                tools=self.registry.get_tools_info()
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