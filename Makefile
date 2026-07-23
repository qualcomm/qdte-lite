# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear
#
# Developer and CI entry points. Works on Linux, macOS, and Windows under a
# bash-providing environment (Git Bash, WSL, or MSYS2); all recipes and the
# helper scripts under scripts/ are POSIX bash.

.DEFAULT_GOAL := help
SHELL         := bash
.ONESHELL:
.SHELLFLAGS   := -eu -o pipefail -c

.PHONY: help init run check-all ascii test lint format format-check type markdown

help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| sed 's/:.*## /\t/' \
		| column -ts$$'\t'

init: ## Install all dependencies (base + GUI extra)
	uv sync --all-extras

run: ## Launch the qdte-lite GUI
	uv run --extra qt qdte-lite

check-all: ascii lint format-check type markdown test ## Run every enforced check

ascii: ## Check that all sources are ASCII-only
	./scripts/check_unicode_symbols.sh --check --all-files

test: ## Headless (--nogui) smoke test against real boot images
	uv run ./scripts/nogui-smoketest.sh

lint: ## Lint with ruff
	uv run ruff check .

type: ## Type-check with mypy
	uv run mypy qdte_lite

format: ## Auto-format with ruff
	uv run ruff format .

format-check: ## Check formatting without modifying files (part of check-all)
	uv run ruff format --check .

markdown: ## Lint Markdown docs with PyMarkdown (.github/ boilerplate skipped)
	uv run pymarkdown scan $$(git ls-files '*.md' ':(exclude).github/')
