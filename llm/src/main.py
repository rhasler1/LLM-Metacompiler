from dotenv import load_dotenv
import os
import shutil
import subprocess
import sys


valid_benchmarks = [
    "s11.c"
]


def master_script(benchmark):
    # Copy benchmark to ../llm-input-files/input-code/.
    shutil.copyfile(
        f"{USER_PREFIX}/llm/benchmarks/{benchmark}",
        f"{USER_PREFIX}/llm/llm-input-files/input-code/{benchmark.split('.')[0]}/{benchmark.split('.')[0]}.original.{'.'.join(benchmark.split('.')[1:])}"
    )

    # Compile benchmark w/o LLM-optimizations.
    compile_program(benchmark, False)

    # Send benchmark to LLM ("LLM-Vectorize" benchmark).
    llm_vectorize(benchmark)

    # Compile optimized benchmark.
    compile_program(f"{benchmark}_optimized", True)

    # If compilation not successful... report and exit.

    # If compilation successful... do checksum analysis.

    # Report results of checksum analysis.





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
