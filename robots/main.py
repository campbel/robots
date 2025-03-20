"""Main entry point for the robots application."""

import asyncio
import colorama
import shutil
from colorama import Fore, Back, Style

from robots.bot import Chatbot
from robots.registry import ToolRegistry
from robots.tools.fred_data_tool import FredDataTool
from robots.tools.memory_tool import MemoryTool
from robots.tools.stock_info_tool import StockInfoTool


# Initialize colorama
colorama.init(autoreset=True)

# Dracula theme colors
DRACULA_PURPLE = Fore.MAGENTA
DRACULA_GREEN = Fore.GREEN
DRACULA_CYAN = Fore.CYAN
DRACULA_YELLOW = Fore.YELLOW
DRACULA_PINK = Fore.LIGHTMAGENTA_EX
DRACULA_ORANGE = Fore.LIGHTYELLOW_EX
DRACULA_BACKGROUND = ""  # Default terminal background


def print_header():
    """Print a stylish header for the application."""
    terminal_width = shutil.get_terminal_size().columns
    
    print(DRACULA_PURPLE + Style.BRIGHT + "╔" + "═" * (terminal_width - 2) + "╗" + Style.RESET_ALL)
    
    title = "ASTRO BOT - Your Financial AI Assistant"
    padding = (terminal_width - len(title) - 2) // 2
    print(DRACULA_PURPLE + Style.BRIGHT + "║" + " " * padding + DRACULA_PINK + title + DRACULA_PURPLE + " " * (terminal_width - len(title) - padding - 2) + "║" + Style.RESET_ALL)
    
    subtitle = "Powered by FRED and YFinance"
    padding = (terminal_width - len(subtitle) - 2) // 2
    print(DRACULA_PURPLE + Style.BRIGHT + "║" + " " * padding + DRACULA_CYAN + subtitle + DRACULA_PURPLE + " " * (terminal_width - len(subtitle) - padding - 2) + "║" + Style.RESET_ALL)
    
    print(DRACULA_PURPLE + Style.BRIGHT + "╚" + "═" * (terminal_width - 2) + "╝" + Style.RESET_ALL)
    print("")


async def main():
    """Main entry point for the application."""
    # Create registry
    registry = ToolRegistry()
    
    # Register tools
    registry.register(MemoryTool())
    registry.register(StockInfoTool())
    registry.register(FredDataTool())
    
    # Create and run chatbot
    bot = Chatbot(registry)
    
    # Print stylish header
    print_header()
    
    # Print welcome message
    print(f"{DRACULA_CYAN}Type {DRACULA_YELLOW}{Style.BRIGHT}'exit'{Style.RESET_ALL}{DRACULA_CYAN} to quit the application.{Style.RESET_ALL}\n")
    
    while True:
        # User prompt with formatting
        user_input = input(f"{DRACULA_GREEN}{Style.BRIGHT}You{Style.RESET_ALL}\n")
        if user_input.lower() == "exit":
            print(f"\n{DRACULA_PURPLE}{Style.BRIGHT}Astro{Style.RESET_ALL}\nGoodbye! Thanks for using Astro Bot.\n")
            break
        
        print("")
        # Show typing indicator
        print(f"{DRACULA_PURPLE}{Style.BRIGHT}Astro{Style.RESET_ALL} {DRACULA_CYAN}thinking...{Style.RESET_ALL}", end="\r")
        
        response = await bot.send_message(user_input)
        
        # Clear the thinking indicator and print the response
        print(" " * shutil.get_terminal_size().columns, end="\r")  # Clear the line
        print(f"{DRACULA_PURPLE}{Style.BRIGHT}Astro{Style.RESET_ALL}\n{response}\n")
        print(f"{DRACULA_ORANGE}─{Style.RESET_ALL}" * shutil.get_terminal_size().columns)  # Separator line


if __name__ == "__main__":
    asyncio.run(main()) 