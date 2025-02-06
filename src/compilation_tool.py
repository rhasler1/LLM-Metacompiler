from dotenv import load_dotenv
import os
import subprocess
load_dotenv()

USER_PREFIX = os.getenv('USER_PREFIX')


def compilation_tool(benchmark_dir, make_command, compiler, benchmark, compilation_out_path):
    current_path = os.getcwd()
    try:
        os.chdir(benchmark_dir)
        print(f"Attempting to run make command: make {make_command} COMPILER={compiler} BENCHMARK={benchmark}")
        result = subprocess.run(
            ["make", make_command, f"COMPILER={compiler}", f"BENCHMARK={benchmark}"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
    except FileNotFoundError as e:
        print(f"Error: Directory or Makefile not found: {e}")
    except Exception as e:
        print(f"An Unexpected error occurred: {e}")
    finally:
        os.chdir(current_path)

    if result.returncode == 0:
        print(f"Compilation return successfully. Writing output to: {compilation_out_path}")
        with open(compilation_out_path, "w") as file:
            file.write(result.stdout)
            file.write(result.stderr)
            return 1
    else:
        print(f"Compilation failed. Writing error message to: {compilation_out_path}")
        with open(compilation_out_path, "w") as file:
            file.write(result.stderr)
            return -1


if __name__ == "__main__":
    """
    TODO:
    """

# Compiler options:
#   COMPILER        VERSION         VECTORIZED FLAGS                                                        UNVECTORIZED FLAGS
#   --------        -------         ------------------                                                      ------------------
#   1. GCC          10.5.0          -W -O3 -mavx2 -lm -ftree-vectorizer-verbose=3                           -O3 -mavx2 -lm
#                                   -ftree-vectorize -fopt-info-vec-optimized
#
#   2. Clang        19.0.0          -O3 -mavx2 -fstrict-aliasing -fvectorize                                -O3 -mavx2 -lm -fno-tree-vectorize
#                                   -fslp-vectorize-aggressive -Rpass-analysis=loop-vectorize -lm

#   3. ICC          2021.10.0       -restrict -std=c99 -O3 -ip -vec -xAVX2                                  -restrict -std=c99 -O3 -ip -no-vec