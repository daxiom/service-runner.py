"""Configuration for the Application."""
import os

from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv())


class Config:
    """Base class configuration that should set reasonable defaults.
    Used as the base for all the other configurations.
    """

    SECRET_KEY = 'a secret'

    TESTING = False
    DEBUG = False
