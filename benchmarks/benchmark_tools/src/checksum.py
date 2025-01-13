from dotenv import load_dotenv
import os
import subprocess

load_dotenv()
USER_PREFIX = os.getenv('USER_PREFIX')


def execute_benchmark(executable_path, stdout_dest):
    command = executable_path
    try:
        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

    except FileNotFoundError as e:
        print(f"Error: {e}")
        return -1
    except Exception as e:
        print(f"Error: {e}")
        return -1
    
    with open(stdout_dest, "w") as file:
        file.write(result.stdout)
    return 1

def generate_benchmark_report(novec_results_path, vec_results_path, llm_vec_results_path):
    result = ""
    result1 = "NO VEC:\t"
    result2 = "VEC:\t"
    result3 = "LLM VEC:\t"
    try:
        with open(novec_results_path, 'r') as file:
            result1 += file.read()
            baseline = float(result1.split('\t')[2])
        with open(vec_results_path, 'r') as file:
            result2 += file.read()
            vec = float(result2.split('\t')[2])
        with open(llm_vec_results_path, 'r') as file:
            result3 += file.read()
            llm_vec = float(result3.split('\t')[2])
        speedup_base = baseline/baseline
        result1 += f"Speedup = {speedup_base}"
        speedup_vec = baseline/vec
        result2 += f"Speedup = {speedup_vec}"
        speedup_llm_vec = baseline/llm_vec
        result3 += f"Speedup = {speedup_llm_vec}"
        result = f"{result1}\n{result2}\n{result3}"
        print(f"{result}")
        return result
    except Exception as e:
        print(f"An error occurred in function: generate_benchmark_report.\nError: {e}")
        return None

def compare_checksums(checksum1_path, checksum2_path):
    comparison_results = {}

    try:
        # Read and parse the first file
        with open(checksum1_path, 'r') as file1:
            data1 = {
                line.split('\t')[0]: line.split('\t')[2].strip()  # {function_name: checksum}
                for line in file1 if line.strip()
            }

        # Read and parse the second file
        with open(checksum2_path, 'r') as file2:
            data2 = {
                line.split('\t')[0]: line.split('\t')[2].strip()  # {function_name: checksum}
                for line in file2 if line.strip()
            }

        # Compare checksums between the two files
        all_functions = set(data1.keys()).union(set(data2.keys()))
        for function in all_functions:
            checksum1 = data1.get(function, None)
            checksum2 = data2.get(function, None)

            if checksum1 == checksum2:
                comparison_results[function] = "Match"
                print(f"Match Checksum1: {checksum1}, Checksum2: {checksum2}")
            else:
                #comparison_results[function] = f"Mismatch (Checksum1: {checksum1}, Checksum2: {checksum2})"
                print(f"Mismatch Checksum1: {checksum1}, Checksum2: {checksum2}")
                return -1

    except FileNotFoundError as e:
        print(f"Error: File not found: {e.filename}")
        return -1
        #return {"error": f"File not found: {e.filename}"}
    except Exception as e:
        print(f"Error: {str(e)}")
        return -1
        #return {"error": str(e)}

    return 1

if __name__ == "__main__":
    execute_benchmark(f"{USER_PREFIX}/benchmarks/TSVC_2/bin/GNU/benchmark", f"{USER_PREFIX}/benchmarks/benchmark_outs/nollmvec.txt")
    execute_benchmark(f"{USER_PREFIX}/benchmarks/TSVC_2/bin/GNU/benchmark_llm_vec", f"{USER_PREFIX}/benchmarks/benchmark_outs/llmvec.txt")
    compare_checksums(f"{USER_PREFIX}/benchmarks/benchmark_outs/nollmvec.txt", f"{USER_PREFIX}/benchmarks/benchmark_outs/llmvec.txt")