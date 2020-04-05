#!/bin/sh
. rt-env/bin/activate
FLASK_APP=roamtoothd FLASK_ENV=development flask run
