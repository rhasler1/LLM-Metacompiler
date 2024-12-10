from dotenv import load_dotenv
from openai import OpenAI
import os
from pydantic import BaseModel

load_dotenv()
openai_key = os.getenv('API_KEY')
USER_PREFIX = os.getenv('USER_PREFIX')


def llm_vectorize(benchmark):
    source_path = f"{USER_PREFIX}/llm/llm-input-files/input-code/{benchmark}"
    with open(source_path, "r") as file:
        code_content = file.read()

    optimize_prompt = prompt + f" {code_content}"
    with open(f"{USER_PREFIX}/llm/llm-input-files/omptimize_prompt.txt", "w") as f:
        f.write(optimize_prompt)
