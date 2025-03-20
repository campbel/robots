"""Main entry point that imports from the robots module."""

import asyncio
from robots.main import main

if __name__ == "__main__":
    asyncio.run(main())
