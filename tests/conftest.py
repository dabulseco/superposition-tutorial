"""Shared test setup: keep tests away from real secrets and the real Ollama."""

import os

import pytest

import tutor
from tests.fake_ollama import FakeOllama

# A port nothing listens on, so "Ollama is off" is the default in tests.
DEAD_URL = "http://127.0.0.1:9"


@pytest.fixture(autouse=True)
def isolated_settings(monkeypatch):
    """
    Read settings from the environment only. Without this, tests would pick
    up a real API key from .streamlit/secrets.toml on the developer's laptop.
    """
    monkeypatch.setattr(
        tutor, "setting",
        lambda name, default="": os.environ.get(name, default).strip())
    for name in ("OLLAMA_API_KEY", "APP_PASSWORD", "OLLAMA_MODELS",
                 "OLLAMA_MODE", "OLLAMA_DEFAULT_MODEL"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("OLLAMA_URL", DEAD_URL)
    tutor.load_settings()
    yield
    monkeypatch.undo()
    tutor.load_settings()


@pytest.fixture
def ollama(monkeypatch):
    """A running stand-in Ollama that the app is pointed at."""
    fake = FakeOllama().start()
    monkeypatch.setenv("OLLAMA_URL", fake.url)
    tutor.load_settings()
    yield fake
    fake.stop()
