#!/bin/sh
set -e
./typecheck.sh
./pylint.sh
./pyflakes.sh
./test.sh
