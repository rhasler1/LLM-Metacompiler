from dotenv import load_dotenv
import os
import subprocess
load_dotenv()

USER_PREFIX = os.getenv('USER_PREFIX')

def compile_test(benchmark_dir, make_command, compiler, benchmark):
    compilation_out_path = f"{USER_PREFIX}/benchmarks/benchmark_outs/compilation/{compiler}/{make_command}_{benchmark}.txt"

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
            return 1
    else:
        print(f"Compilation failed. Writing error message to: {compilation_out_path}")
        with open(compilation_out_path, "w") as file:
            file.write(result.stderr)
            return -1


if __name__ == "__main__":
    print(f"Starting compilation test...")
    src_path = f"{USER_PREFIX}/benchmarks/TSVC_2"
    compile_test(src_path, False)
    print(f"Compilation test complete")