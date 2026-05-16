import os
from dotenv import load_dotenv
from dataclasses import dataclass
from typing import Optional

load_dotenv()

@dataclass
class Settings:

    db_name: str
    db_host: str
    db_port: str
    db_username: str
    db_password: str

    


def get_settings() -> Settings:
    
    return Settings(

        db_name=os.getenv("DB_NAME", "bean_and_brew"),
        db_host=os.getenv("DB_HOST", "localhost"),
        db_port=os.getenv("DB_PORT", "5432"),
        db_username=os.getenv("DB_USERNAME", "postgres"),
        db_password=os.getenv("DB_PASSWORD", "password"),

    )

config = get_settings()
