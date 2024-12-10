from dotenv import load_dotenv
import os
import shutil
import subprocess
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from compiler_tester.src.compiler import compile_program

load_dotenv()
USER_PREFIX = os.getenv('USER_PREFIX')

OUTPUT_LOG = f"{USER_PREFIX}/output_log/output.txt"

valid_benchmarks = [
    "s11.c"
]


def clean_up(file_path):
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"Deleted: {file_path}")
        else:
            print(f"File not found: {file_path}")
    except Exception as e:
        print(f"Error deleting file {file_path}: {e}")


def master_script(benchmark):
    # Copy benchmark to ../llm-input-files/input-code/
    shutil.copyfile(
        f"{USER_PREFIX}/benchmarks/{benchmark}",
        f"{USER_PREFIX}/llm/llm-input-files/input-code/{benchmark.split('.')[0]}_unvectorized.{'.'.join(benchmark.split('.')[1:])}"
    )

    # Compile benchmark w/o LLM-optimizations.
    compile_program(benchmark, False, OUTPUT_LOG)

    # Send benchmark to LLM ("LLM-Vectorize" benchmark).
    #llm_vectorize(benchmark)

    # Compile optimized benchmark.
    #compile_program(f"{benchmark}_optimized", True)

    # If compilation not successful... report and exit.

    # If compilation successful... do checksum analysis.

    # Report results of checksum analysis.

    # Remove created files.
    clean_up(f"{USER_PREFIX}/llm/llm-input-files/input-code/{benchmark.split('.')[0]}_unvectorized.{'.'.join(benchmark.split('.')[1:])}")


if __name__ == "__main__":
    # Check if user provided benchmark is valid.
    benchmark = sys.argv[2]
    if benchmark not in valid_benchmarks:
        print("Please provide one of the following valid benchmarks:")
        for valid in valid_benchmarks:
            print(f"- {valid}")
        sys.exit(1)

    # Execute master master script with user provided benchmark.
    master_script(benchmark)
    print(f"Done")
