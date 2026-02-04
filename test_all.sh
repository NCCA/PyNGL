#!/usr/bin/env zsh

uv run pytest
uv run pytest -m opengl
uv run pytest -m webgpu
uv run pytest -m qt
