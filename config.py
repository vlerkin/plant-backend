import os

import boto3
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

load_dotenv(".env.local")


class Configuration:
    connection_string: str = os.getenv('DATABASE_CONNECTION_STRING')

    secret_key: str = os.getenv('SECRET_KEY')
    algorithm: str = os.getenv('ALGORITHM')
    token_expire_days: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_DAYS"))
    aws_access_key_id: str = os.getenv("AWS_ACCESS_KEY")
    aws_secret_access_key: str = os.getenv("AWS_SECRET")
    aws_region_name: str = os.getenv("AWS_REGION")
    aws_bucket_name: str = os.getenv("AWS_BUCKET_NAME")

    image_hostname: str = "http://" + aws_bucket_name + ".s3." + aws_region_name + ".amazonaws.com/"


engine = create_engine(Configuration.connection_string, echo=True)
session = Session(engine)

s3 = boto3.client(
    "s3",
    aws_access_key_id=Configuration.aws_access_key_id,
    aws_secret_access_key=Configuration.aws_secret_access_key,
    region_name=Configuration.aws_region_name
)

