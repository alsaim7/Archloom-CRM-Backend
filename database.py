from sqlmodel import Session, create_engine
from dotenv import load_dotenv
import os

DATABASE_URL = "sqlite:///./archloom.db"

# Load environment variables from .env file
load_dotenv()

# Prod_DB_URL = os.getenv("Prod_DB_URL")


engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
# engine = create_engine(Prod_DB_URL)


# get a seesion
def get_session():
    try:
        with Session(engine) as session:
            yield session
    except Exception as e:
        # log error appropriately
        raise