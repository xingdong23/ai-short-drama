#!/usr/bin/env bash

set -euo pipefail

python3 -m pip install -r requirements.txt
mkdir -p output assets/characters assets/bgm assets/voices assets/lora

echo "Environment ready."
