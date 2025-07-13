import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    LOG_FILE_PATH = os.environ.get('LOG_FILE_PATH') or 'application.log'
