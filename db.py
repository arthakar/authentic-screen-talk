import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.pool import NullPool

load_dotenv()
def db_connect():
    USER = os.getenv("DB_USER")
    PASSWORD = os.getenv("DB_PASSWORD")
    HOST = os.getenv("DB_HOST")
    PORT = os.getenv("DB_PORT")
    DB_NAME = os.getenv("DB_NAME")

    DB_URL = f"postgresql+psycopg2://{USER}:{PASSWORD}@{HOST}:{PORT}/{DB_NAME}"
    engine = create_engine(DB_URL, poolclass=NullPool, echo=True)
    conn = None

    try:
        with engine.connect() as connnection:
            print("Connection to Database Successful")
            conn = connnection
    except Exception as e:
        print("Failed to Connect to Database")
        #print(e)

    return engine, conn

db_connect()
