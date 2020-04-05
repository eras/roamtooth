#!/bin/sh
[ -z "$FLASK_ENV" ] && export FLASK_ENV=development
. rt-env/bin/activate
FLASK_APP=roamtoothd flask run "$@"
