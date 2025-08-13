import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect, Integer, String, Column, func
from sqlalchemy.pool import NullPool
from sqlalchemy.orm import declarative_base, sessionmaker

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

engine, conn = db_connect()
Base = declarative_base()
Session = sessionmaker(bind=engine)
session = Session()

def create_show_class(show_title):
    return type(
        show_title.capitalize(),
        (Base,),
        {
            '__table_args__': {'extend_existing': True},
            '__tablename__': show_title,
            'id': Column(Integer, primary_key=True),
            'question': Column(String),
            'response': Column(String),
        }
    )

inspector = inspect(engine)
def submit_responses(show_title, data):
    show = create_show_class(show_title)
    index = 0
    Base.metadata.create_all(engine)
    if show_title in inspector.get_table_names():
        index = session.query(func.max(show.id)).scalar()
    for entry in data:
        index += 1
        stmt = show(id=index, question=entry[0], response=entry[1])
        session.add(stmt)
    session.commit()
