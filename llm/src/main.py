from dotenv import load_dotenv
import os
import shutil
import subprocess
import sys

from llm import llm_vectorize, llm_revectorize
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from benchmarks.benchmark_tools.src.file_parser import extract_function, parse_script
from benchmarks.benchmark_tools.src.compile_checker import compile_test
from benchmarks.benchmark_tools.src.checksum_checker import compare_checksums

load_dotenv()
USER_PREFIX = os.getenv('USER_PREFIX')

OUTPUT_DIR = f"{USER_PREFIX}/output_log"

PATH_TO_TSVC = f"{USER_PREFIX}/benchmarks/TSVC_2"

MAKE_NOVEC = "build_benchmark_novec"
MAKE_VEC = "build_benchmark_vec"
MAKE_LLM_VEC = "build_benchmark_llm_vec"

valid_compilers = [
    "GNU",
    "clang",
    "intel"
]

# TODO: Add func arguments to strings.
valid_benchmarks = [
    "s000",
    "s162",
    "s278",
    "s331",
    "s332",
    "s341",
    "s482",
    "s115",
    "s116",
    "s212",
    "s243",
    "s2244",
    "s1251",
    "s3251",
    "s252",
    "s1281",
    "s3251",
    "s252",
    "s1281",
    "s3251",
    "s252",
    "s1281",
    "s273",
    "s274",
    "s1119",
    "s121",
    "s131",
    "s241",
    "s292",
    "s2101",
    "s352",
    "s421",
    "s431",
    "s452",
    "s453",
    "va",
    "vpv",
    "vtv",
    "vpvtv",
    "vtvtv",
    "vbor",
    "s311",
    "s319",
    "vsumr",
    "vdotr",
    "s314",
    "s315",
    "s316",
    "s318",
    "s3110",
    "s13110",
    "s3111",
    "s3113"
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



Results = []
def main_script(benchmark, compiler):
    #1: Extract benchmark from TSVC_2
    if parse_script(PATH_TO_TSVC, benchmark, "NULL") == -1:
        print(f"Failed to parse {benchmark} from {PATH_TO_TSVC}... Exiting main script.")
        return -1

    #2: Compile benchmark without vectorization flags.
    if compile_test(PATH_TO_TSVC, MAKE_NOVEC, compiler, benchmark) == -1:
        print(f"Failed to compile {benchmark} from {PATH_TO_TSVC} with {MAKE_NOVEC} and {compiler}")
        print("Exiting main script.")
        return -1
    
    #3: Compile benchmark with vectorization flags.
    if compile_test(PATH_TO_TSVC, MAKE_VEC, compiler, benchmark) == -1:
        print(f"Failed to compile {benchmark} from {PATH_TO_TSVC} with {MAKE_VEC} and {compiler}")
        print("Exiting main script")
        return -1
    
    print(f"Copying: {USER_PREFIX}/benchmarks/TSVC_2/src/benchmark_{benchmark}.c \nto: {USER_PREFIX}/llm/llm_input_files/input_code/{benchmark.split('.')[0]}_unvectorized.c")
    shutil.copyfile(
        f"{USER_PREFIX}/benchmarks/TSVC_2/src/benchmark_{benchmark}.c",
        f"{USER_PREFIX}/llm/llm_input_files/input_code/{benchmark.split('.')[0]}_unvectorized.c"
    )

    #4: Vectorize benchmark
    if llm_vectorize(benchmark, "gpt-4o") == -1:
            print(f"Exiting script")
            return -1
    k = 0
    k_max = 5 # Change this to be set by user.
    while k < k_max:
        #5: Copy vectorized benchmark to TSVC.
        shutil.copyfile(
            f"{USER_PREFIX}/llm/llm_output_files/{benchmark}_vectorized.c",
            f"{USER_PREFIX}/benchmarks/TSVC_2/src/benchmark_{benchmark}_llm_vec.c"
        )

        #6: Compile llm-vectorized.
        #compilation_out_path = f"{benchmark_dir}/benchmark_outs/compilation/{compiler}/{make_command}_{benchmark}.txt"
        if compile_test(PATH_TO_TSVC, MAKE_LLM_VEC, compiler, benchmark) == -1:
            print(f"Failed to compile {benchmark} from {PATH_TO_TSVC} with {MAKE_VEC} and {compiler}")
            print(f"Copying error message to llm input")
            compilation_out_path = f"{USER_PREFIX}/benchmarks/benchmark_outs/compilation/{compiler}/{MAKE_LLM_VEC}_{benchmark}.txt"
            llm_input_error_path = f"{USER_PREFIX}/llm_input_files/error_messages/{compiler}_{MAKE_LLM_VEC}_{benchmark}.txt"
            shutil.copyfile(
                compilation_out_path,
                llm_input_error_path
            )
            if llm_revectorize(benchmark, "gpt-4o", llm_input_error_path) == -1:
                print("Error when attempting to revectorize. Exiting main script.")
            else:
                print("Revectorization successful, re-attempting to compile.")
                k += 1
        
        #7: Compare checksum values.
        #elif compare_checksums() == -1:
        #    print(f"Checksum test failed. Attempting to revectorize...")
        #    llm_revectorize(benchmark, "gpt-4o")
        #    k += 1
        
        else:
            print(f"Compilation and checksum tests passed in {k} attempts.\nExiting main script.")
            return 1
        
    print(f"Failed to llm-vectorize {benchmark} with {compiler} after {k} attempts.\nExiting main script.")


if __name__ == "__main__":
    # Validate benchmark
    benchmark = sys.argv[2]
    if benchmark not in valid_benchmarks:
        print("Please provide one of the following valid benchmarks:")
        for valid in valid_benchmarks:
            print(f"- {valid}")
        sys.exit(1)
    print(f"Using benchmark: {benchmark}")

    # Set compiler variable
    compiler = "GNU"
    if len(sys.argv) > 3 and sys.argv[3] in valid_compilers:
        compiler = sys.argv[3]
    elif len(sys.argv) > 3 and sys.argv[3] not in valid_compilers:
        print(f"{sys.argv[3]} not in valid compilers, select from:")
        for compiler in valid_compilers:
            print(f"- {compiler}")
        sys.exit(1)
    print(f"Using compiler: {compiler}")
    
    main_script(benchmark, compiler)
    print(f"Exiting main script")



# Compiler options:
#   COMPILER        VERSION         VECTORIZED FLAGS                                                        UNVECTORIZED FLAGS
#   --------        -------         ------------------                                                      ------------------
#   1. GCC          10.5.0          -W -O3 -mavx2 -lm -ftree-vectorizer-verbose=3                           -O3 -mavx2 -lm
#                                   -ftree-vectorize -fopt-info-vec-optimized
#
#   2. Clang        19.0.0          -O3 -mavx2 -fstrict-aliasing -fvectorize                                -O3 -mavx2 -lm -fno-tree-vectorize
#                                   -fslp-vectorize-aggressive -Rpass-analysis=loop-vectorize -lm

#   3. ICC          2021.10.0       -restrict -std=c99 -O3 -ip -vec -xAVX2                                  -restrict -std=c99 -O3 -ip -no-vec 