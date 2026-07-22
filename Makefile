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

.PHONY: help init run check-all ascii test lint format format-check type

help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| sed 's/:.*## /\t/' \
		| column -ts$$'\t'

init: ## Install all dependencies (base + GUI extra)
	uv sync --all-extras

run: ## Launch the qdte GUI
	uv run --extra qt qdte

check-all: ascii lint format-check type test ## Run every check (CI)

ascii: ## Check that all sources are ASCII-only
	./scripts/check_unicode_symbols.sh --check --all-files

test: ## Headless (--nogui) smoke test against real boot images
	uv run ./scripts/nogui-smoketest.sh

# The lint/format/type targets are stubs until the corresponding tooling is
# configured; they succeed so check-all stays green in the meantime.

lint: ## Lint with ruff (stub: not configured yet)
	@echo "lint: ruff is not configured yet (stub)"

format: ## Auto-format with ruff (stub: not configured yet)
	@echo "format: ruff is not configured yet (stub)"

format-check: ## Check formatting in CI mode (stub: not configured yet)
	@echo "format-check: ruff is not configured yet (stub)"

type: ## Type-check with mypy (stub: not configured yet)
	@echo "type: mypy is not configured yet (stub)"
