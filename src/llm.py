from dotenv import load_dotenv
from openai import OpenAI
import openai
import os
from pydantic import BaseModel

load_dotenv()
OPENAI_KEY = os.getenv('API_KEY')
USER_PREFIX = os.getenv('USER_PREFIX')

class LLMAgent:
    def __init__(self, model, key, system_message="You are a helpful assistant."):
        if not model:
            raise ValueError("A model must be specified when creating a LLM Agent.")
        self.model = model
        self.memmory = [{"role": "system", "content": system_message}]
        try:
            print(f"Creating client.")
            self.client = OpenAI(api_key=key)
        except Exception as e:
            print(f"Failed to create client.")
    
    def add_to_memmory(self, role, content):
        self.memmory.append({"role": role, "content": content})
    
    def generate_response(self):
        try:
            response = self.client.chat.completions.create(
                model = self.model,
                messages = self.memmory
            )
        except Exception as e:
            print(f"Error when generating response: {e}")
            return -1
        content = response.choices[0].message.content
        self.add_to_memmory("assistant", content)
        return 1
    
    def get_last_msg(self):
        if self.memmory:
            return self.memmory[-1]
        return None
    
    def clean_msg_content(self, message):
        content = message["content"]
        if content.startswith("```"):
            # Find the first newline after the opening ``` and remove it
            content = content.split("\n", 1)[1]
        if content.endswith("```"):
            # Remove the trailing ```
            content = content.rsplit("\n", 1)[0]
        return content
    
    def get_memmory(self):
        return self.memmory
    
    def format_memmory(self):
        formatted = []
        for entry in self.memmory:
            role = entry["role"]
            content = entry["content"]
            formatted.append(f"{role}:\n{content}\n{'-'*40}\n")
        return "".join(formatted)
    

def llm_compile_failure(benchmark, llm_agent, compilation_error_path):
    prompt_path = f"{USER_PREFIX}/prompts/compilation_failure.txt"
    vectorized_code_path = f"{USER_PREFIX}/generated/TSVC_2/src/benchmark_{benchmark}_llm_vec.c"

    with open(prompt_path, "r") as file:
        initial_prompt = file.read()
    with open(compilation_error_path, "r") as file:
        error_msg = file.read()
    error_prompt = f"{initial_prompt}\n{error_msg}"

    llm_agent.add_to_memmory("user", error_prompt)
    llm_agent.generate_response()
    if llm_agent.get_last_msg() is not None:
        content = llm_agent.clean_msg_content(llm_agent.get_last_msg())
    else:
        print(f"No message to clean.")
        return -1
    print(f"Writing llm-vectorized code to {vectorized_code_path}")
    with open(vectorized_code_path, "w") as file:
        file.write(content)
    return 1
      
def llm_vectorize(benchmark, llm_agent, instruction_set):
    benchmark_path = f"{USER_PREFIX}/generated/TSVC_2/src/benchmark_{benchmark}.c"
    instructions_path = f"{USER_PREFIX}/prompts/vectorizer_instructions.txt"
    vectorized_code_path = f"{USER_PREFIX}/generated/TSVC_2/src/benchmark_{benchmark}_llm_vec.c"

    print(f"Reading code content from {benchmark_path}")
    with open(benchmark_path, "r") as file:
        code_content = file.read()

    print(f"Reading instructions for LLM from {instructions_path}")
    with open(instructions_path, "r") as file:
        prompt = file.read()
    updated_prompt = prompt.replace('{instruction_set}', instruction_set)
    
    print(f"Combining nl prompt with benchmark {benchmark} function for model message.")
    optimize_prompt = f"{updated_prompt}\n{code_content}"

    #print(f"Adding {optimize_prompt} to LLM memmory.")
    llm_agent.add_to_memmory("user", optimize_prompt)
    print(f"Inferencing with LLM.")
    llm_agent.generate_response()
    if llm_agent.get_last_msg() is not None:
        content = llm_agent.clean_msg_content(llm_agent.get_last_msg())
    else:
        print(f"No message to clean.")
        return -1
    print(f"Writing llm-vectorized code to {vectorized_code_path}")
    with open(vectorized_code_path, "w") as file:
        file.write(content)
    return 1

def llm_checksum_failure(benchmark, llm_agent, prompt_path):
    #prompt_path = f"{USER_PREFIX}/llm/llm_input_files/nl_prompts/checksum_failure.txt"
    vectorized_code_path = f"{USER_PREFIX}/generated/TSVC_2/src/benchmark_{benchmark}_llm_vec.c"

    with open(prompt_path, "r") as file:
        failure_prompt = file.read()

    prompt = f"{failure_prompt}"
    llm_agent.add_to_memmory("user", prompt)
    llm_agent.generate_response()
    if llm_agent.get_last_msg() is not None:
        content = llm_agent.clean_msg_content(llm_agent.get_last_msg())
    else:
        print(f"No message to clean.")
        return -1
    print(f"Writing llm-vectorized code to {vectorized_code_path}")
    with open(vectorized_code_path, "w") as file:
        file.write(content)
    return 1

# TODO:
if __name__ == "__main__":
    """
    TODO:
    """