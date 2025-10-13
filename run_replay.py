#!/usr/bin/env python3
"""
Script to run the replay engine (Part 1).
"""
import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.apps.replay_app import main

if __name__ == "__main__":
    asyncio.run(main())
