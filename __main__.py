"""Entry point for running MyBGInfo as a module or script.

Usage::

    python __main__.py [--gui] [--interval N]
    python -m mybginfo [--gui] [--interval N]
"""
from src.bginfo import main

if __name__ == "__main__":
    main()
