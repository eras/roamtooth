#!/bin/sh
. rt-env/bin/activate && mypy --no-implicit-optional --strict-optional --warn-unreachable --warn-return-any --warn-no-return --strict roamtoothd
