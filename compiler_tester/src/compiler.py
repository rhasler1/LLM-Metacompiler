import subprocess
import os
import shutil
from dotenv import load_dotenv
load_dotenv()
USER_PREFIX = os.getenv('USER_PREFIX')

def compile_program(benchmark, optimized, output_log):
    try: 
        if not optimized:
            # Copy original benchmark from llm module to compiler module.
            shutil.copyfile(
                f"{USER_PREFIX}/benchmarks/{benchmark}",
                f"{USER_PREFIX}/compiler_tester/non_llm_vectorized/{benchmark}"
            )
            print("File copied")
            # Compile.
            subprocess.run(
                ["make", "compile"],
                check = True,
                stdout = subprocess.PIPE,
                stderr = subprocess.PIPE
            )
        else :
            # Copy llm-vectorized benchmark from llm module to compiler module.
            shutil.copyfile(
                f"{USER_PREFIX}/benchmarks/{benchmark}",
                f"{USER_PREFIX}/compiler_tester/llm_vectorized/{benchmark}"
            )
            # Compile.
            #subprocess.run(
            #    ["make", "compile_vectorized"],
            #    check = True,
            #    stdout = output_log,
            #    stderr = output_log
            #)
        print("Makefile compile successfully.\n")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Makefile compile failed: {e}\n")
        return False


def run_program(exec_path, output_file, optimized):
    if not optimized:
        result = subprocess.run(
            ["make", "run"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
    else:
        result = subprocess.run(
            ["make", "run_vectorized"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
    )





