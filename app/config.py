from _token import SECRET_KEY

class BaseConfig:
    SECRET_KEY = SECRET_KEY
    SQLALCHEMY_TRACK_MODIFICATIONS = False


class DevConfig(BaseConfig):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = (
        "mysql+pymysql://yukang:Lowyihong123@127.0.0.1/FAHUI"
    )


class ProdConfig(BaseConfig):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = (
        "mysql+pymysql://yukang:Lowyihong123@127.0.0.1/FAHUI"
    )
