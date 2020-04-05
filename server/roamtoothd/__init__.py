"""RoamToothd is a server facilitating moving of bluetooth devices from one device to another."""

import flask

import roamtoothd.app as app

def create_app() -> flask.Flask:
    """Create the app function for Flask framework"""
    return app.create()

if __name__ == '__main__':
    create_app().run()
