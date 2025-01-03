from dotenv import load_dotenv
import os
import subprocess
load_dotenv()

USER_PREFIX = os.getenv('USER_PREFIX')

# TODO:
#   1. Support more complex make commands.
#   2. Figure out exactly what those are.
#
def compile_test(src_path, vectorized):
    current_path = os.getcwd()
    try:
        # Change cwd to Makefile location.
        os.chdir(src_path)

        if vectorized:
            make_command = "benchmark_llm_vec"
        else:
            make_command = "benchmark"
        
        print(f"Attempting to execute command make {make_command}")
        # Execute make command and capture output.            
        result = subprocess.run(
            ["make", make_command],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        # Captured results
        print(f"Compilation output: \n{result.stdout}.")
        print(f"Compilation errors: \n{result.stderr}.")
        if result.returncode == 0:
            print("Compilation returned successfully.")
        else:
            print("Compilation failed. Check the errors above.")

    except FileNotFoundError as e:
        print(f"Error: Directory or Makefile not found: {e}")
    except Exception as e:
        print(f"An Unexpected error occurred: {e}")
    finally:
        os.chdir(current_path)

if __name__ == "__main__":
    print(f"Starting compilation test...")
    src_path = f"{USER_PREFIX}/benchmarks/TSVC_2"
    compile_test(src_path, False)
    print(f"Compilation test complete")