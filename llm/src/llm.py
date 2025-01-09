from dotenv import load_dotenv
from openai import OpenAI
import openai
import os
from pydantic import BaseModel

load_dotenv()
OPENAI_KEY = os.getenv('API_KEY')
USER_PREFIX = os.getenv('USER_PREFIX')

def llm_revectorize(benchmark, model, llm_input_error_path):
    vect_code_path = f"{USER_PREFIX}/llm/llm_output_files/{benchmark}_vectorized.c"
    revec_p1_path = f"{USER_PREFIX}/llm/llm_input_files/nl_prompts/revectorize_instructions_p1.txt"
    revec_p2_path = f"{USER_PREFIX}/llm/llm_input_files/nl_prompts/revectorize_instructions_p2.txt"
    revec_p3_path = f"{USER_PREFIX}/llm/llm_input_files/nl_prompts/revectorize_instructions_p3.txt"
    with open(revec_p1_path, "r") as file:
        prompt_1 = file.read()
    with open(revec_p2_path, "r") as file:
        prompt_2 = file.read()
    with open(revec_p3_path, "r") as file:
        prompt_3 = file.read()
    with open(vect_code_path, "r") as file:
        prev_code = file.read()
    with open(llm_input_error_path, "r") as file:
        error_message = file.read()
    prompt = f"{prompt_1}\n{prev_code}\n\n{prompt_2}\n{error_message}\n\n{prompt_3}"

    client = OpenAI(api_key=OPENAI_KEY)
    print(f"Attempting to inference with model")
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}]
        )
        print("Successful inference")
    except Exception as e:
        print(f"Error: {e}")
        return -1
    
    vectorized_code = response.choices[0].message.content
    
    if vectorized_code.startswith("```"):
    # Find the first newline after the opening ``` and remove it
        vectorized_code = vectorized_code.split("\n", 1)[1]
    
    if vectorized_code.endswith("```"):
        # Remove the trailing ```
        vectorized_code = vectorized_code.rsplit("\n", 1)[0]

    dest_path = f"{USER_PREFIX}/llm/llm_output_files/{benchmark}_vectorized.c"
    print(f"Writing llm-vectorized code to {dest_path}")
    with open(dest_path, "w") as file:
        file.write(vectorized_code)
    
    return 1
    

def llm_vectorize(benchmark, model):
    src_path = f"{USER_PREFIX}/llm/llm_input_files/input_code/{benchmark}_unvectorized.c"
    with open(src_path, "r") as file:
        code_content = file.read()

    prompt_path = f"{USER_PREFIX}/llm/llm_input_files/nl_prompts/vectorizer_instructions.txt"
    with open(prompt_path, "r") as file:
        prompt = file.read()

    print(f"Combining nl prompt with benchmark {benchmark} function for model message")
    optimize_prompt = f"{prompt}\n{code_content}"
    client = OpenAI(api_key=OPENAI_KEY)
    print(f"Attempting to inference with {model}")
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": optimize_prompt}]
        )
        print(f"Successful inference")
    
    except Exception as e:
        print(f"Error: {e}")
        return -1
    
    #print(response.choices[0].message)

    vectorized_code = response.choices[0].message.content
    
    if vectorized_code.startswith("```"):
    # Find the first newline after the opening ``` and remove it
        vectorized_code = vectorized_code.split("\n", 1)[1]
    
    if vectorized_code.endswith("```"):
        # Remove the trailing ```
        vectorized_code = vectorized_code.rsplit("\n", 1)[0]

    dest_path = f"{USER_PREFIX}/llm/llm_output_files/{benchmark}_vectorized.c"
    print(f"Writing llm-vectorized code to {dest_path}")
    with open(dest_path, "w") as file:
        file.write(vectorized_code)
    
    return 1


# TODO:
if __name__ == "__main__":
    benchmark = "s000"
    model = "gpt-4o"
    llm_vectorize(benchmark, model)
