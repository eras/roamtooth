#!/bin/sh
args="$@"
[ -z "$args" ] && args=roamtoothd
. rt-env/bin/activate && pyflakes $args
