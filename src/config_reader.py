"""
config_reader.py
Author: Nima Shafie

Reads config.ini and merges with environment variable overrides.
Environment variables always win over config file values.
"""

import configparser
import os


def fetch_config_dict() -> dict:
    cfg = configparser.ConfigParser()
    cfg_path = os.path.join(os.path.dirname(__file__), "..", "config.ini")
    cfg.read(cfg_path)

    details = {}
    if cfg.has_section("OLLAMA_DETAILS"):
        details = dict(cfg["OLLAMA_DETAILS"])

    # Environment variables override config file
    env_overrides = {
        "model_name": os.environ.get("OLLAMA_MODEL"),
        "ollama_host": os.environ.get("OLLAMA_HOST"),
        "device": os.environ.get("DEVICE"),
    }
    for key, val in env_overrides.items():
        if val:
            details[key] = val

    return details
