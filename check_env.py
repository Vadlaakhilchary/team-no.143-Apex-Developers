import os
from dotenv import load_dotenv

load_dotenv()

print("HF_TOKEN:", os.getenv("HF_TOKEN"))
print("HF_MODEL:", os.getenv("HF_MODEL"))
