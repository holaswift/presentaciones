#!/bin/bash
# Regenera holaswift-presentaciones.skill (un zip) a partir de skills/holaswift-presentaciones/.
set -euo pipefail
cd "$(dirname "$0")"
rm -f holaswift-presentaciones.skill
(cd skills && zip -qr -X ../holaswift-presentaciones.skill holaswift-presentaciones -x '*.DS_Store' -x '*__pycache__*' -x '*.pyc')
unzip -l holaswift-presentaciones.skill | tail -1
