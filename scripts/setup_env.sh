#!/bin/bash

curl -LsSf https://astral.sh/uv/install.sh | sh
uv venv .venv --clear
source .venv/bin/activate
uv sync --extra dev
