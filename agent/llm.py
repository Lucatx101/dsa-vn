"""Anthropic client construction and model selection.

Model tiering (per the approved spec): a cheaper model runs the six strategy
agents; a stronger model writes the single final dashboard.
"""

import os

import anthropic
from dotenv import load_dotenv

load_dotenv()

DEFAULT_STRATEGY_MODEL = "claude-sonnet-5"
DEFAULT_DECISION_MODEL = "claude-opus-5"


def get_client() -> anthropic.Anthropic:
    """The SDK resolves ANTHROPIC_API_KEY (or an `ant auth login` profile) itself."""
    return anthropic.Anthropic()


def strategy_model() -> str:
    return os.getenv("STRATEGY_MODEL", DEFAULT_STRATEGY_MODEL)


def decision_model() -> str:
    return os.getenv("DECISION_MODEL", DEFAULT_DECISION_MODEL)
