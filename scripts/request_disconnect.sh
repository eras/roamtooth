#!/bin/sh
curl -i -H "Content-Type: application/json" -d '{ "device": "42" }' http://aiee.mf:5000/cmd/device_disconnect
