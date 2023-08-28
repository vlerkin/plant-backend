import os

from dotenv import load_dotenv

load_dotenv(".env.local")


class Configuration:
    connectionString: str = os.getenv('DATABASE_CONNECTION_STRING')

    secretKey: str = os.getenv('SECRET_KEY')
    algorithm: str = os.getenv('ALGORITHM')
    tokenExpireDays: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_DAYS"))
