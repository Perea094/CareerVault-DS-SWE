#!/usr/bin/env bash
set -e

echo "========================================================"
echo "  Career Vault - Setup & Dependency Bootstrapper"
echo "========================================================"
echo ""

if command -v python3 &>/dev/null; then
    PY_CMD="python3"
elif command -v python &>/dev/null; then
    PY_CMD="python"
else
    echo "[ERROR] Python 3 was not found in your PATH."
    echo "Please install Python 3.11+ via your package manager (brew, apt, etc.)."
    exit 1
fi

"$PY_CMD" setup_vault.py --interactive --install-deps "$@"
