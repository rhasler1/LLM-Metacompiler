from dotenv import load_dotenv
import os
import re
import subprocess
load_dotenv()
USER_PREFIX = os.getenv('USER_PREFIX')

# IMPORTANT: Functions were written very quickly as proof of concept. Will need to be rewritten.
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
    except Exception as e:
        print(f"Error: {e}")
    
    with open(stdout_dest, "w") as file:
        file.write(result.stdout)


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
                print("Match")
            else:
                comparison_results[function] = f"Mismatch (Checksum1: {checksum1}, Checksum2: {checksum2})"
                print("Mismatch")

    except FileNotFoundError as e:
        return {"error": f"File not found: {e.filename}"}
    except Exception as e:
        return {"error": str(e)}

    return comparison_results

if __name__ == "__main__":
    execute_benchmark(f"{USER_PREFIX}/benchmarks/TSVC_2/bin/GNU/benchmark", f"{USER_PREFIX}/benchmarks/benchmark_outs/nollmvec.txt")
    execute_benchmark(f"{USER_PREFIX}/benchmarks/TSVC_2/bin/GNU/benchmark_llm_vec", f"{USER_PREFIX}/benchmarks/benchmark_outs/llmvec.txt")
    compare_checksums(f"{USER_PREFIX}/benchmarks/benchmark_outs/nollmvec.txt", f"{USER_PREFIX}/benchmarks/benchmark_outs/llmvec.txt")