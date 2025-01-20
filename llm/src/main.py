from dotenv import load_dotenv
import os
import shutil
import sys
from datetime import datetime
#import argparse

from llm import llm_vectorize, llm_compile_failure, llm_checksum_failure, LLMAgent
from config import valid_models, valid_compilers, valid_benchmarks
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from benchmarks.benchmark_tools.src.file_parser import parse_script
from benchmarks.benchmark_tools.src.compile_checker import compile_test
from benchmarks.benchmark_tools.src.checksum import compare_checksums, execute_benchmark, generate_benchmark_report

load_dotenv()
USER_PREFIX = os.getenv('USER_PREFIX')
OPENAI_KEY = os.getenv('API_KEY')

PATH_TO_TSVC = f"{USER_PREFIX}/benchmarks/TSVC_2"
MAKE_NOVEC = "build_benchmark_novec"
MAKE_VEC = "build_benchmark_vec"
MAKE_LLM_VEC = "build_benchmark_llm_vec"

#class Report:
#    def __init__(self, benchmark: str, model: str, compiler: str, datetime: str,):
#        self.title = f"{benchmark} using {model} and {compiler} at {datetime}"
#        self.report = {}
#    
#    def add_to_report(self, section: str, content: str):
#        if section not in self.report:
#            self.report[section] = content
#        else:
#            self.report[section].append(content)
#    
#    def gen_report(self) -> str:
#        report_str = self.title + "\n"
#        for section, contents in self.report.items():
#            report_str += f"## {section} ##\n"
#            report_str += "\n".join(contents) + "\n\n"
#        return report_str
#    
#    def save_to_file(self, filepath: str):
#        with open(filepath, "w") as f:
#            f.write(self.gen_report())

#def build_gen_dir(gen_repo):
#    if os.path.exists(gen_repo):
#        print(f"Cleaning up existing {gen_repo} direcotry")
#        shutil.rmtree(gen_repo)
#    print(f"{gen_repo} setup complete")

#def cpy_bench_dir(src_repo, gen_repo):
#    print(f"Copying {src_repo} to {gen_repo}")
#    shutil.copy(src_repo, gen_repo)


# TODO:
#   0. Continue work on report summary.
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
    # Add compilation output to llm memmory (this output includes vector dependency analysis).
    compilation_file = f"{USER_PREFIX}/benchmarks/benchmark_outs/compilation/{compiler}/{MAKE_VEC}_{benchmark}.txt"
    with open(compilation_file, 'r') as file:
        compilation_out = file.read()
    llm_msg_temp = f"Here is compilation information from the {compiler} compiler. Use this information to help you vectorize {benchmark}:\n{compilation_out}"
    llm_agent.add_to_memmory("user", llm_msg_temp)
    
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
        compile_status = compile_test(PATH_TO_TSVC, MAKE_LLM_VEC, compiler, benchmark)
        if compile_status == -1:
            print(f"Failed to compile {benchmark} from {PATH_TO_TSVC} with {MAKE_LLM_VEC} and {compiler}.\nCopying error message to {llm_input_error_path}")
            shutil.copyfile(
                compilation_out_path,
                llm_input_error_path
            )
            llm_inference_status = llm_compile_failure(benchmark, llm_agent, llm_input_error_path)
            if llm_inference_status == -1:
                print("Error when attempting to revectorize. Exiting main script.")
                return -1
            else:
                print("Re-attempting to compile.")
                k += 1
                continue
        else:
            print("Successful compilation")

        #9: Execute llm vectorized benchmark.
        execution_status = execute_benchmark(f"{PATH_TO_TSVC}/bin/{compiler}/{benchmark}_llm_vec", f"{USER_PREFIX}/benchmarks/benchmark_outs/execution/{compiler}/{benchmark}_llm_vec.txt")
        if execution_status == -1:
            print(f"Exeuction of {benchmark}_llm_vec failed.\nError unhandled, exiting main script.")
            return -1
        else:
            print("Successful execution")
        
        #10: Checksum test.
        checksum_status = compare_checksums(baseline_dest, f"{USER_PREFIX}/benchmarks/benchmark_outs/execution/{compiler}/{benchmark}_llm_vec.txt")
        if checksum_status == -1:
            print(f"Checksum test failed: Checksum mismatch.")
            checksum_missmatch_path = f"{USER_PREFIX}/llm/llm_input_files/nl_prompts/checksum_mismatch.txt"
            llm_inference_status = llm_checksum_failure(benchmark, llm_agent, checksum_missmatch_path)
            if llm_inference_status == -1:
                print(f"Unhandled error, exiting main script")
                return -1
            else:
                print(f"Successful inference.")
                k += 1
                continue
        elif checksum_status == -2:
            print(f"Checksum test failed: Execution of vectorized code resulted in segfault")
            segfault_path = f"{USER_PREFIX}/llm/llm_input_files/nl_prompts/seg_fault.txt"
            llm_inference_status = llm_checksum_failure(benchmark, llm_agent, segfault_path)
            if llm_inference_status == -1:
                print(f"Unhandled error, exiting main script")
                return -1
            else:
                print(f"Successful inference.")
                k += 1
                continue
        else:
            print("Checksum test passed.")
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
    model = "gpt-4"
    if len(sys.argv) > 4 and sys.argv[4] in valid_models:
        model = sys.argv[4]
    elif len(sys.argv) > 4 and sys.argv[4] not in valid_models:
        print(f"{sys.argv[4]} not in valid models, select from:")
        for model in valid_models:
            print(f"- {model}")
        sys.exit(1)
    print(f"Using model: {model}")

    # Set k_max variable
    k_max = 5
    if len(sys.argv) > 5:
        temp = int(sys.argv[5])
        if temp > 100:
            print(f"Provided k max value is greater than 100, setting to default instead: {k_max}")
        elif temp < 1:
            print(f"Provided k max value is less than 1, setting to default instead: {k_max}")
        else:
            k_max = temp
    print(f"k max: {k_max}")

    # Instantiating LLMAgent.    
    llm_agent = LLMAgent(model, OPENAI_KEY)

    # Instantiating Report.
    #now = datetime.now()
    #date_time_str = now.strftime("%Y-%m-%d %H:%M:%S")
    #report = Report(benchmark, model, compiler, date_time_str)

    # Starting main script.
    status = main_script(benchmark, benchmark_args, compiler, llm_agent, k_max)

    # Generating reports.
    now = datetime.now()
    date_time_str = now.strftime("%Y-%m-%d %H:%M:%S")
    report_dest = f"{USER_PREFIX}/reports/{compiler}/{benchmark}_{date_time_str}.txt"
    with open(report_dest, "w") as f:
        f.write(llm_agent.format_memmory())

    if status == 1:
        novec_result_path = f"{USER_PREFIX}/benchmarks/benchmark_outs/execution/{compiler}/{benchmark}_novec.txt"
        vec_result_path = f"{USER_PREFIX}/benchmarks/benchmark_outs/execution/{compiler}/{benchmark}_vec.txt"
        llm_vec_result_path = f"{USER_PREFIX}/benchmarks/benchmark_outs/execution/{compiler}/{benchmark}_llm_vec.txt"
        result = generate_benchmark_report(novec_result_path, vec_result_path, llm_vec_result_path)
        with open(report_dest, "a") as f:
            f.write(result)

    print(f"All done.")


#TODO:
# Compiler options:
#   COMPILER        VERSION         VECTORIZED FLAGS                                                        UNVECTORIZED FLAGS
#   --------        -------         ------------------                                                      ------------------
#   1. GCC          10.5.0          -W -O3 -mavx2 -lm -ftree-vectorizer-verbose=3                           -O3 -mavx2 -lm
#                                   -ftree-vectorize -fopt-info-vec-optimized
#
#   2. Clang        19.0.0          -O3 -mavx2 -fstrict-aliasing -fvectorize                                -O3 -mavx2 -lm -fno-tree-vectorize
#                                   -fslp-vectorize-aggressive -Rpass-analysis=loop-vectorize -lm

#   3. ICC          2021.10.0       -restrict -std=c99 -O3 -ip -vec -xAVX2                                  -restrict -std=c99 -O3 -ip -no-vec 
# /usr/lib/llvm-19/lib/libclang-19.so.1