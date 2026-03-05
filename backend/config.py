import os
from dotenv import load_dotenv

load_dotenv()
MODEL_API_KEY = os.getenv("MODEL_API_KEY")
MODEL_URL = os.getenv("MODEL_URL")
MODEL_NAME = os.getenv("MODEL_NAME")
