from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from src.utils.custom_app_exception import CustomAppException

from settings import config


class Database:

    def __init__(self):
        self.DATABASE_URL = (
    f"postgresql://{config.db_username}:{config.db_password}"
    f"@{config.db_host}:{config.db_port}/{config.db_name}"
)
        self.engine = create_engine(self.DATABASE_URL, echo=False,pool_size=10,max_overflow=20)

        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

      

    def get_db(self):
        try: 
            print('came here')
            return self.SessionLocal()
        except Exception as e:
            raise CustomAppException(
                content= f"Database err : {str(e)}",
                err_code="Internal Server Error",
                status_code=500
            )
    
Base = declarative_base()
def get_database():
    return Database()
