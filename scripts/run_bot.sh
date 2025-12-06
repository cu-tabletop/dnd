#!/bin/bash

uv venv .venv --allow-existing
source .venv/bin/activate
uv sync --extra dev

set -o allexport
source .env
uv run main.py
