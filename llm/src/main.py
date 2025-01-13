from dotenv import load_dotenv
import os
import shutil
import sys

from llm import llm_vectorize, llm_compile_failure, llm_checksum_failure, get_llm_memmory, LLMAgent
from config import valid_models, valid_compilers, valid_benchmarks
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from benchmarks.benchmark_tools.src.file_parser import extract_function, parse_script
from benchmarks.benchmark_tools.src.compile_checker import compile_test
from benchmarks.benchmark_tools.src.checksum import compare_checksums, execute_benchmark, generate_benchmark_report

load_dotenv()
USER_PREFIX = os.getenv('USER_PREFIX')
OPENAI_KEY = os.getenv('API_KEY')

PATH_TO_TSVC = f"{USER_PREFIX}/benchmarks/TSVC_2"

MAKE_NOVEC = "build_benchmark_novec"
MAKE_VEC = "build_benchmark_vec"
MAKE_LLM_VEC = "build_benchmark_llm_vec"


def clean_up(file_path):
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"Deleted: {file_path}")
        else:
            print(f"File not found: {file_path}")
    except Exception as e:
        print(f"Error deleting file {file_path}: {e}")



#Results = []
# TODO: MONDAY
#   3. Add report summary to the pipeline. (this can include llm_memmory, compilation messages, etc.)
#   4. Begin working on README.md.
#   5. Integrate compiler dependency analysis into pipeline.

# Work on calculating speed-up values
def main_script(benchmark, args, compiler, llm_agent, k_max):
    #1: Extract benchmark from TSVC_2.
    if parse_script(PATH_TO_TSVC, benchmark, args) == -1:
        print(f"Failed to parse {benchmark} from {PATH_TO_TSVC}... Exiting main script.")
        return -1

    #2: Compile benchmark without vectorization flags.
    if compile_test(PATH_TO_TSVC, MAKE_NOVEC, compiler, benchmark) == -1:
        print(f"Failed to compile {benchmark} from {PATH_TO_TSVC} with {MAKE_NOVEC} and {compiler}")
        print("Exiting main script.")
        return -1
    
    #3: Execute baseline (novec).
    baseline_path = f"{PATH_TO_TSVC}/bin/{compiler}/{benchmark}_novec"
    baseline_dest = f"{USER_PREFIX}/benchmarks/benchmark_outs/execution/{compiler}/{benchmark}_novec.txt"
    if execute_benchmark(baseline_path, baseline_dest) == -1:
        print(f"Failed to execute {benchmark} with novec.\nExiting main script")
        return -1

    #4: Compile benchmark with vectorization flags.
    if compile_test(PATH_TO_TSVC, MAKE_VEC, compiler, benchmark) == -1:
        print(f"Failed to compile {benchmark} from {PATH_TO_TSVC} with {MAKE_VEC} and {compiler}")
        print("Exiting main script")
        return -1
    
    #5: Execute compiler vectorized code (vec).
    vec_compiler_path = f"{PATH_TO_TSVC}/bin/{compiler}/{benchmark}_vec"
    vec_compiler_dest = f"{USER_PREFIX}/benchmarks/benchmark_outs/execution/{compiler}/{benchmark}_vec.txt"
    if execute_benchmark(vec_compiler_path, vec_compiler_dest) == -1:
        print(f"Failed to execute {benchmark} with compiler vectorization.\nExiting main script")
        return -1
    
    print(f"Copying: {USER_PREFIX}/benchmarks/TSVC_2/src/benchmark_{benchmark}.c \nto: {USER_PREFIX}/llm/llm_input_files/input_code/{benchmark.split('.')[0]}_unvectorized.c")
    shutil.copyfile(
        f"{USER_PREFIX}/benchmarks/TSVC_2/src/benchmark_{benchmark}.c",
        f"{USER_PREFIX}/llm/llm_input_files/input_code/{benchmark.split('.')[0]}_unvectorized.c"
    )

    #6: Vectorize benchmark.
    # (Only returns -1 if there is some sort of communication error with the llm)
    if llm_vectorize(benchmark, llm_agent) == -1:
            print(f"Exiting script")
            return -1
    
    compilation_out_path = f"{USER_PREFIX}/benchmarks/benchmark_outs/compilation/{compiler}/{MAKE_LLM_VEC}_{benchmark}.txt"
    llm_input_error_path = f"{USER_PREFIX}/llm/llm_input_files/error_messages/{compiler}_{MAKE_LLM_VEC}_{benchmark}.txt"
    k = 0
    while k < k_max:
        #7: Copy vectorized benchmark to TSVC.
        shutil.copyfile(
            f"{USER_PREFIX}/llm/llm_output_files/{benchmark}_vectorized.c",
            f"{USER_PREFIX}/benchmarks/TSVC_2/src/benchmark_{benchmark}_llm_vec.c"
        )

        #8: Compile llm-vectorized.
        #compilation_out_path = f"{benchmark_dir}/benchmark_outs/compilation/{compiler}/{make_command}_{benchmark}.txt"
        if compile_test(PATH_TO_TSVC, MAKE_LLM_VEC, compiler, benchmark) == -1:
            print(f"Failed to compile {benchmark} from {PATH_TO_TSVC} with {MAKE_VEC} and {compiler}.\nCopying error message to {llm_input_error_path}")
            shutil.copyfile(
                compilation_out_path,
                llm_input_error_path
            )
            if llm_compile_failure(benchmark, llm_agent, llm_input_error_path) == -1:
                print("Error when attempting to revectorize. Exiting main script.")
                return -1
            print("Re-attempting to compile.")
            k += 1
        
        #9: Execute llm vectorized benchmark.
        elif execute_benchmark(f"{PATH_TO_TSVC}/bin/{compiler}/{benchmark}_llm_vec", f"{USER_PREFIX}/benchmarks/benchmark_outs/execution/{compiler}/{benchmark}_llm_vec.txt") == -1:
            print(f"Exeuction of {benchmark}_llm_vec failed. Attempting to revectorize...")
            print(f"TODO: implement reprompting for execution failure.\nExiting main script for now.")
            k += 1
            return -1
        
        #10: Checksum test.
        elif compare_checksums(baseline_dest, f"{USER_PREFIX}/benchmarks/benchmark_outs/execution/{compiler}/{benchmark}_llm_vec.txt") == -1:
            print(f"Checksum test failed. Attempting to revectorize...")
            #print(f"TODO: implement reprompting for checksum failure.\nExiting main script for now.")
            if llm_checksum_failure(benchmark, llm_agent) == -1:
                print("Error when attempting to revectorize. Exiting main script.")
                return -1
            print("Re-attempting to compile")
            k += 1
        
        #11: Successful llm vectorization and exit.
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
    benchmark_args = valid_benchmarks.get(benchmark)

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

    # Set model variable
    model = "gpt-4o"
    if len(sys.argv) > 4 and sys.argv[4] in valid_models:
        model = sys.argv[4]
    elif len(sys.argv) > 4 and sys.argv[4] not in valid_models:
        print(f"{sys.argv[4]} not in valid models, select from:")
        for model in valid_models:
            print(f"- {model}")
        sys.exit(1)
    print(f"Using model: {model}")

    k_max = 5

    # Instantiating LLMAgent.    
    llm_agent = LLMAgent(model, OPENAI_KEY)
    # Starting main script.
    main_script(benchmark, benchmark_args, compiler, llm_agent, k_max)

    # Generating reports.
    get_llm_memmory(llm_agent, benchmark, compiler)
    novec_result_path = f"{USER_PREFIX}/benchmarks/benchmark_outs/execution/{compiler}/{benchmark}_novec.txt"
    vec_result_path = f"{USER_PREFIX}/benchmarks/benchmark_outs/execution/{compiler}/{benchmark}_vec.txt"
    llm_vec_result_path = f"{USER_PREFIX}/benchmarks/benchmark_outs/execution/{compiler}/{benchmark}_llm_vec.txt"
    generate_benchmark_report(novec_result_path, vec_result_path, llm_vec_result_path)

    print(f"All done.")



# Compiler options:
#   COMPILER        VERSION         VECTORIZED FLAGS                                                        UNVECTORIZED FLAGS
#   --------        -------         ------------------                                                      ------------------
#   1. GCC          10.5.0          -W -O3 -mavx2 -lm -ftree-vectorizer-verbose=3                           -O3 -mavx2 -lm
#                                   -ftree-vectorize -fopt-info-vec-optimized
#
#   2. Clang        19.0.0          -O3 -mavx2 -fstrict-aliasing -fvectorize                                -O3 -mavx2 -lm -fno-tree-vectorize
#                                   -fslp-vectorize-aggressive -Rpass-analysis=loop-vectorize -lm

#   3. ICC          2021.10.0       -restrict -std=c99 -O3 -ip -vec -xAVX2                                  -restrict -std=c99 -O3 -ip -no-vec 