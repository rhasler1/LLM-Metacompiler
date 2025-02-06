from dotenv import load_dotenv
import os
import shutil
import sys
from datetime import datetime
import argparse

from llm import llm_vectorize, llm_compile_failure, llm_checksum_failure, LLMAgent
from benchmark import BenchmarkSuite, TSVC2Suite
from config import valid_models, valid_compilers, valid_benchmarks, valid_benchmark_suites, valid_instruction_sets 
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from parsing_tool import extraction_script
from compilation_tool import compilation_tool
from execution_tool import compare_checksums, execution_tool, generate_benchmark_report

load_dotenv()
USER_PREFIX = os.getenv('USER_PREFIX')
OPENAI_KEY = os.getenv('API_KEY')

MAKE_NOVEC = "build_benchmark_novec"
MAKE_VEC = "build_benchmark_vec"
MAKE_LLM_VEC = "build_benchmark_llm_vec"


def build_dir(dir_path: str):
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
        print(f"Built directory: {dir_path}")
        return 1
    else:
        print(f"Directory: {dir_path} already exists.")
        return -1


def tear_down_dir(dir_path: str):
    """
    Return Values:
    - -1: The specified path does not exist.
    - -2: The specified path exists but is not a directory.
    - -3: The user chose not to proceed with the deletion.
    - -4: The user chose to delete the directory but a problem occurred.
    -  1: The directory and its contents were successfully deleted.
    """
    if not os.path.exists(dir_path):
        return -1
    if not os.path.isdir(dir_path):
        return -2
    
    contents = os.listdir(dir_path)
    print(f"Directory {dir_path} contains {len(contents)} items.")

    confirm = input(f"Are you sure you want to delete {dir_path} and all its contents (yes/no): ").strip().lower()
    if confirm != "yes":
        return -3
    
    shutil.rmtree(dir_path)
    if os.path.exists(dir_path):
        return -4
    return 1


def ignore_hidden_files(dir, files):
    """
    The ignore_hidden_files function is a helper to copy_suite_to_gen.
    """
    return [f for f in files if f.startswith('.')]


def copy_suite_to_gen(suite_path, gen_path):
    """
    The copy_suite_to_gen function attempts to copy the `suite_path` directory and all its contents
    to the `gen_path` directory.

    Parameters:
    - suite_path (str): The path to the suite directory.
    - gen_path (str):   The path to the gen directory.

    Return Values:
    - -1: The specified path for the suite does not exist.
    - -2: The specified path for the gen directory does not exist.
    - -3: An error occurred when attempting to copy the suite directory to the gen directory.
    -  1: The suite directory was successfully copied to the gen directory.
    """
    if not os.path.exists(suite_path):
        return -1
    if not os.path.exists(gen_path):
        return -2
    
    dest = os.path.join(gen_path, os.path.basename(suite_path))

    # Copying suite directory and its contents to gen directory. Hidden files (files beginning with '.' are ignored)
    try:
        shutil.copytree(suite_path, dest, ignore=ignore_hidden_files, dirs_exist_ok=True)
        print(f"{suite_path} successfully coppied to {gen_path}")
        return 1
    except Exception as e:
        print(f"An error occurred: {e}")
        return -3


def main_script(benchmark_obj: BenchmarkSuite, llm_agent: LLMAgent, k_max: int):

    # Prompt paths
    checksum_missmatch_path = f"{USER_PREFIX}/prompts/checksum_mismatch.txt"
    segfault_path = f"{USER_PREFIX}/prompts/seg_fault.txt"

    #1:Init benchmark
    if benchmark_obj.init_benchmark() != 1:
        print(f"Failed to initialize benchmark: {benchmark_obj.benchmark} from {benchmark_obj.benchmark_suite}")
        return -1
    
    #2:Compile & Execute NOVEC
    if benchmark_obj.compile_benchmark(MAKE_NOVEC) != 1:
        print(f"Failed to compile benchmark: {benchmark_obj.benchmark} from: {benchmark_obj.benchmark_suite} using compilation type: {MAKE_NOVEC}")
        return -1
    if benchmark_obj.execute_benchmark("novec") != 1:
        print(f"Failed to execute benchmark baseline, exiting script.")
        return -1
    
    #3: Compile & Execute VEC
    if benchmark_obj.compile_benchmark(MAKE_VEC) != 1:
        print(f"Failed to compile benchmark: {benchmark_obj.benchmark} from: {benchmark_obj.benchmark_suite} using compilation type: {MAKE_VEC}")
        return -1
    if benchmark_obj.execute_benchmark("vec") != 1:
        print(f"Failed to execute benchmark baseline, exiting script.")
        return -1

    
    # Add compilation output to llm memory (this output includes vector dependency analysis).
    with open(benchmark_obj.comp_dest(MAKE_VEC), 'r') as file:
        compilation_out = file.read()
    llm_msg_temp = f"Here is compilation information from the {benchmark_obj.compiler} compiler. Use this information to help you vectorize {benchmark_obj.benchmark}:\n{compilation_out}"
    llm_agent.add_to_memory("user", llm_msg_temp)

    #6: Vectorize benchmark. Note: llm_vectorize only returns -1 if there is some sort of communication error with the llm.
    if llm_vectorize(benchmark_obj.benchmark, llm_agent, instruction_set) == -1:
            print(f"Exiting script.")
            return -1
    
    global k
    # Feedback loop
    while k < k_max:
        #8: Compile llm-vectorized.
        compile_status = benchmark_obj.compile_benchmark(MAKE_LLM_VEC)
        if compile_status == -1:
            print(f"Failed to compile {benchmark_obj.benchmark} from {benchmark_obj.benchmark_suite} with {MAKE_LLM_VEC}.")
            llm_inference_status = llm_compile_failure(benchmark, llm_agent, benchmark_obj.comp_dest(MAKE_LLM_VEC))
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
        execution_status = benchmark_obj.execute_benchmark("llm_vec")
        if execution_status == -1:
            print(f"Exeuction of {benchmark_obj.benchmark}_llm_vec failed.\nError unhandled, exiting main script.")
            return -1
        else:
            print("Successful execution")
        
        #10: Checksum test.
        checksum_status = compare_checksums(benchmark_obj.exec_dest("novec"), benchmark_obj.exec_dest("llm_vec"))
        if checksum_status == -1:
            print(f"Checksum test failed: Checksum mismatch.")
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
            k += 1
            return 1
        
    print(f"Failed to llm-vectorize {benchmark} with {compiler} after {k} attempts.\nExiting main script.")


if __name__ == "__main__":
    # Parsing program arguments.
    parser = argparse.ArgumentParser(description="Parsing arguments to the LLM-Metacompiler.")
    parser.add_argument(
        "-i",
        "--instruction_set",
        type=str,
        choices=valid_instruction_sets,
        default="AVX2",
        help="The instruction set to use. Choose from: " + ", ".join(valid_instruction_sets)
    )
    parser.add_argument(
        "-b",
        "--benchmark_suite",
        type=str,
        choices=valid_benchmark_suites,
        required=True,
        help="The benchmark to use (required). Choose from: " + ", ".join(valid_benchmarks.keys()),
    )
    parser.add_argument(
        "-f",
        "--function",
        type=str,
        choices=valid_benchmarks.keys(),
        required=True,
        help="The benchmark to use (required). Choose from: " + ", ".join(valid_benchmarks.keys()),
    )
    parser.add_argument(
        "-c",
        "--compiler",
        type=str,
        choices=valid_compilers,
        default="GNU",
        help="The compiler to use (default: GNU). Choose from: " + ", ".join(valid_compilers),
    )
    parser.add_argument(
        "-m",
        "--model",
        type=str,
        choices=valid_models,
        default="gpt-4o",
        help="The model to use (default: gpt-4). Choose from: " + ", ".join(valid_models),
    )
    parser.add_argument(
        "-k",
        "--k_max",
        type=int,
        default=5,
        help="The maximum number of inferences (default: 5)",
    )
    args = parser.parse_args()
    instruction_set = args.instruction_set
    suite = args.benchmark_suite
    benchmark = args.function
    compiler = args.compiler
    model = args.model
    k_max = args.k_max
    print(f"Using instruction set: {instruction_set}")
    print(f"Using benchmark suite: {suite}")
    print(f"Using benchmark: {benchmark}")
    print(f"Using compiler: {compiler}")
    print(f"Using model: {model}")
    print(f"Using max inference value: {k_max}")

    # Setting required paths and building required directories.
    print(f"Initializing path to benchmark suite.")
    path_to_suite = f"{USER_PREFIX}/benchmarks/{suite}"
    print(f"Initializing path to generated directory.")
    path_to_gen = f"{USER_PREFIX}/generated"
    print(f"Building directory: {path_to_gen}")
    gen_build_status = build_dir(path_to_gen)
    if gen_build_status == -1:
        print(f"Directory: {path_to_gen} already exists. Using existing directory.")
    else:
        print(f"Directory: {path_to_gen} successfully built.")
    
    # Copying suite directory to gen directory.
    copy_status = copy_suite_to_gen(path_to_suite, path_to_gen)
    if copy_status == -1:
        print(f"Directory: {path_to_suite} does not exist.")
        sys.exit(1)
    elif copy_status == -2:
        print(f"Directory: {path_to_gen} does not exist.")
        sys.exit(1)
    elif copy_status == -3:
        print("Copy error")
        sys.exit(1)

    # Inits
    benchmark_args = valid_benchmarks.get(benchmark) # Arguments to the benchmark function. E.g., s000(Null).

    # Creating Benchmark Object
    if suite == "TSVC_2":
        print(f"Building benchmark object for {suite}")
        benchmark_obj = TSVC2Suite(benchmark, benchmark_args, instruction_set, compiler)
    
    #0: Setup--building compilation & execution result directories.
    build_dir(f"{benchmark_obj.PATH_TO_GEN_SUITE}/compilation/{compiler}")
    build_dir(f"{benchmark_obj.PATH_TO_GEN_SUITE}/execution/{compiler}")

    # Creating LLM Object
    llm_agent = LLMAgent(model, OPENAI_KEY) # Initializing LLMAgent.
    global k # `k` tracks the number of inferences made.
    k = 0

    # Starting main script.
    status = main_script(benchmark_obj, llm_agent, k_max)

    # Generating reports.
    now = datetime.now()
    date_time_str = now.strftime("%Y-%m-%d %H:%M:%S")
    report_dest = f"{USER_PREFIX}/reports/{compiler}/{benchmark}_{date_time_str}.txt"
    with open(report_dest, "w") as f:
        f.write(llm_agent.format_memory())
    if status == 1:
        novec_result_path = f"{USER_PREFIX}/generated/{suite}/execution/{compiler}/{benchmark}_novec.txt"
        vec_result_path = f"{USER_PREFIX}/generated/{suite}/execution/{compiler}/{benchmark}_vec.txt"
        llm_vec_result_path = f"{USER_PREFIX}/generated/{suite}/execution/{compiler}/{benchmark}_llm_vec.txt"
        result = generate_benchmark_report(novec_result_path, vec_result_path, llm_vec_result_path)
        with open(report_dest, "a") as f:
            f.write(f"Succeeded in LLM-Vectorizing {benchmark} in {k} attempts\nResults:\n{result}")
    else:
        with open(report_dest, "a") as f:
            f.write(f"Failed to LLM-Vectorize {benchmark} in {k} attempts.\nNo benchmark report to generate.")

    # Tearing down generate dir.
    tear_down_dir(benchmark_obj.PATH_TO_GEN)

    print(f"All done.")