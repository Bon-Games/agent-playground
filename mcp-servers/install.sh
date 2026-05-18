#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")"

python3 scripts/install.py "$@"
python3 scripts/install-plugin-claude.py "$@"
