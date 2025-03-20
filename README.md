# Python Chatbot with Claude

A simple terminal-based chatbot using Anthropic's Claude API and tool capabilities.

## Setup

1. Install the required dependencies:

   ```
   pip install -r requirements.txt
   ```

2. Set your Anthropic API key as an environment variable:

   ```
   export ANTHROPIC_API_KEY=your_api_key_here
   ```

3. Run the chatbot:
   ```
   python main.py
   ```

## Features

- Terminal-based chat interface
- Memory tool to save important information
- Styled output with ANSI terminal colors
- Formal conversation style

The bot will automatically create a `memory.txt` file to store information between conversations.
