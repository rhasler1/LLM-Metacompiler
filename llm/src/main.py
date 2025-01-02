from dotenv import load_dotenv
import os
import shutil
import subprocess
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from compiler_tester.src.compiler import compile_program, run_program
from benchmarks.benchmark_tools.src.file_parser import extract_function, parser_script
from benchmarks.benchmark_tools.src.compile_checker import compile_test

load_dotenv()
USER_PREFIX = os.getenv('USER_PREFIX')

OUTPUT_DIR = f"{USER_PREFIX}/output_log"

PATH_TO_TSVC = f"{USER_PREFIX}/benchmarks/TSVC_2"


valid_benchmarks = [
    "s000",
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


def main_script(benchmark):

    # 1: Extract benchmark from TSVC_2
    if parser_script(PATH_TO_TSVC, benchmark, "NULL") == -1:
        return -1

    # 2: Compile check on extracted benchmark
    if compile_test(PATH_TO_TSVC) == -1:
        return -1

    # 3: Write execution time and checksum to file
    #if execution_test(PATH_TO_TSVC) == -1:
    #    return -1

    # 4: If previous (3) are successful, then copy extracted function to llm/input_code
    # Copy benchmark to ../llm-input-files/input-code/
    shutil.copyfile(
        f"{USER_PREFIX}/benchmarks/TSVC_2/src/benchmark.c",
        f"{USER_PREFIX}/llm/llm-input-files/input-code/{benchmark.split('.')[0]}_unvectorized.c"
    )

    # Compile benchmark w/o LLM-optimizations.
    #success_compilation = compile_program(benchmark, False)
    #if success_compilation:
        # Execute code
    #    run_program(f"hello", f"{OUTPUT_DIR}/unvectorized_output.txt", False)

    # Send benchmark to LLM ("LLM-Vectorize" benchmark).
    #llm_vectorize(benchmark)

    # Compile optimized benchmark.
    #compile_program(f"{benchmark}_optimized", True)

    # If compilation not successful... report and exit.

    # If compilation successful... do checksum analysis.

    # Report results of checksum analysis.

    # Remove created files.
    #clean_up(f"{USER_PREFIX}/llm/llm-input-files/input-code/{benchmark.split('.')[0]}_unvectorized.{'.'.join(benchmark.split('.')[1:])}")


if __name__ == "__main__":
    # Check if user provided benchmark is valid.
    benchmark = sys.argv[2]
    if benchmark not in valid_benchmarks:
        print("Please provide one of the following valid benchmarks:")
        for valid in valid_benchmarks:
            print(f"- {valid}")
        sys.exit(1)

    # Execute master master script with user provided benchmark.
    main_script(benchmark)
    print(f"Done")


# TODO:
#   1. Rework main script. Currently, I believe I've defined more modules then necessary.
#       The checksum_tester and compiler_tester modules can be submodules of benchmarks.
#   2.
#
#
#
#
#
#
#
#
#
