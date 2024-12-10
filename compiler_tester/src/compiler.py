import subprocess
import os
import shutil
from dotenv import load_dotenv
load_dotenv()
USER_PREFIX = os.getenv('USER_PREFIX')

BENCHMARK_DIRECTORY = f"{USER_PREFIX}/benchmarks"
MAKEFILE_PATH = f"{USER_PREFIX}/benchmarks/Makefile"

def compile_program(benchmark, optimized): 
    if not optimized:
        # Copy original benchmark from llm module to compiler module.
        shutil.copyfile(
            f"{USER_PREFIX}/benchmarks/{benchmark}",
            f"{USER_PREFIX}/compiler_tester/non_llm_vectorized/{benchmark}"
        )
        print("File copied")
        # Compile.
        os.chdir(BENCHMARK_DIRECTORY)
        print(f"Changing directory to: {BENCHMARK_DIRECTORY}")
        result = subprocess.run(
            ["make", "hello"],
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

    if result.returncode != 0:
        print(f"Makefile compile failed: \n")
        return False
    else:
        print("Makefile compile successfully.\n")
        return True


def run_program(exec_filename, output_file, optimized):
    exec_filepath = f"{BENCHMARK_DIRECTORY}/{exec_filename}"
    print(f"Execution filepath: {exec_filepath}")
    os.chdir(BENCHMARK_DIRECTORY)
    print(f"Changing directory to: {BENCHMARK_DIRECTORY}")
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
    if result.returncode != 0:
        print(f"Runtime error on {exec_filepath} with error message: {result.stderr}")
        return False

    print(f"Run successful, TODO: write to output.")
    # Filter out the unwanted lines
    filtered_output = "\n".join(
        line for line in result.stdout.splitlines()
        if not (line.startswith("make[") or line.startswith("./"))
    )
    # Write the filtered output to the file
    with open(output_file, 'w+') as f:
        f.write(filtered_output)
    return True





