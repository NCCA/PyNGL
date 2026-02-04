#!/usr/bin/env zsh

set -euo pipefail
uv run pytest || exit 1
uv run pytest -m opengl || exit 1
uv run pytest -m webgpu || exit 1
uv run pytest -m qt || exit 1
