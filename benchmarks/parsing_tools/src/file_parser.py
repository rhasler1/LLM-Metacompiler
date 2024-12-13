from dotenv import load_dotenv
import os
import re
load_dotenv()
USER_PREFIX = os.getenv('USER_PREFIX')

# Purpose: Parse TSVC_2 benchmark functions.
def extract_functions(file_path):
    with open(file_path, 'r') as file:
        content = file.read()
    
    # TODO: Work on regex. Do some research on pattern matching.
    # Regex pattern to match functions.
    #pattern = r'real_t\s+\w+\s*\([^)]*\)\s*\{.*?\}'
    #pattern = r'^\s*real_t\s+\w+\s*\([^)]*\)\s*\{(?:[^{}]*\{[^{}]*\})*.*?\}'
    matches = re.finditer(pattern, content, re.MULTILINE)

    functions = []
    for match in matches:
        functions.append(match.group(0))

    return functions

if __name__ == "__main__":
    print(f"Starting test...")
    file_path = f"{USER_PREFIX}/benchmarks/TSVC_2/src/tsvc.c"
    functions = extract_functions(file_path)
    print(len(functions))
    for function in functions:
        print(function)