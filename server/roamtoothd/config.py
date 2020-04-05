"""Configuration for RoamToothd"""

import os
BASEDIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    """Configuration for RoamToothd"""
    DEBUG = False
    TESTING = False
    CSRF_ENABLED = True
    SECRET_KEY = 'this-really-needs-to-be-changed'


class ProductionConfig(Config):
    """Production config for RoamToothd"""
    DEBUG = False


class StagingConfig(Config):
    """Staging config for RoamToothd"""
    DEVELOPMENT = True
    DEBUG = True


class DevelopmentConfig(Config):
    """Development config for RoamToothd"""
    DEVELOPMENT = True
    DEBUG = True


class TestingConfig(Config):
    """Testing config for RoamToothd"""
    TESTING = True
