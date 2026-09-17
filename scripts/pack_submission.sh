#!/usr/bin/env bash
# pack_submission.sh - build ./submission with exactly what a reviewer needs,
# and nothing the reviewer doesn't.
#
# The project is a pure GenLayer Intelligent Contracts project. The frontend
# that documents it (src/, index.html, package.json, node tooling) lives in
# this repository for presentation only and is deliberately excluded below.
#
#     bash scripts/pack_submission.sh
#
set -euo pipefail

OUT=submission
rm -rf "$OUT"
mkdir -p "$OUT"

for item in \
  contracts \
  tests \
  docs \
  samples \
  deployments \
  scripts/verify_deployment.py \
  README.md \
  SUBMISSION.md \
  requirements.txt \
  pytest.ini
do
  mkdir -p "$OUT/$(dirname "$item")"
  cp -r "$item" "$OUT/$item"
done

# The tests reference files one level up; the bundle is self-contained.
echo "Submission bundle written to ./submission - contents:"
find "$OUT" -type f | sort
echo
echo "The deployable artifact is submission/contracts/meridian.py - nothing else is required."
