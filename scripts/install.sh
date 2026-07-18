#!/bin/bash
# Kept for compatibility — everything now goes through ONE builder.
# Prefer: ./build-installer.sh  (repo root)
set -e
cd "$(dirname "$0")/.."
node scripts/build-installer.js
