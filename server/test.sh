#!/bin/sh
. rt-env/bin/activate && python -m unittest discover --start-directory=roamtoothd --pattern='*.py'
