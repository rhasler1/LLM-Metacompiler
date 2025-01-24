from dotenv import load_dotenv
from clang.cindex import Index
from clang.cindex import Config
import os

load_dotenv()
USER_PREFIX = os.getenv('USER_PREFIX')
OUTPUT_FILE = f"{USER_PREFIX}/benchmarks/TSVC_2/src/test.c"

# Needed for clang parsing.
#"/usr/lib/llvm-19/lib/libclang-19.so.1"
#"/usr/lib/llvm-18/lib/libclang.so"
config_lib = "/usr/lib/llvm-19/lib/libclang-19.so.1"
try:
    Config.set_library_file(config_lib)
except Exception as e:
    print(f"An error occurred when setting clang.cindex Config library at: {config_lib}")

TSVC_2_PRELUDE = r"""#include <time.h>
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <sys/time.h>
#include "benchmark.h"
#include "common.h"
#include "array_defs.h"

// array definitions
__attribute__((aligned(ARRAY_ALIGNMENT))) real_t flat_2d_array[LEN_2D*LEN_2D];

__attribute__((aligned(ARRAY_ALIGNMENT))) real_t x[LEN_1D];

__attribute__((aligned(ARRAY_ALIGNMENT))) real_t a[LEN_1D],b[LEN_1D],c[LEN_1D],d[LEN_1D],e[LEN_1D],
                                   aa[LEN_2D][LEN_2D],bb[LEN_2D][LEN_2D],cc[LEN_2D][LEN_2D],tt[LEN_2D][LEN_2D];

__attribute__((aligned(ARRAY_ALIGNMENT))) int indx[LEN_1D];

real_t* __restrict__ xx;
real_t* yy;
"""

TSVC_2_TIME_FUNCTION = r"""typedef real_t(*test_function_t)(struct args_t *);
void time_function(test_function_t vector_func, void * arg_info)
{
    struct args_t func_args = {.arg_info=arg_info};

    double result = vector_func(&func_args);

    double tic=func_args.t1.tv_sec+(func_args.t1.tv_usec/1000000.0);
    double toc=func_args.t2.tv_sec+(func_args.t2.tv_usec/1000000.0);

    double taken = toc-tic;

    printf("%10.3f\t%f\n", taken, result);
}"""

 
def extraction_script(path_to_gen_suite: str, benchmark: str, benchmark_args: str):
    """
    The extraction_script function calls three (3) sub-functions.
    (1) extract_benchmark
    (2) write_benchmark_header
    (3) write_benchmark_driver

    Parameters:
    - suite_path (str)
    - benchmark (str)
    - benchmark_args (str)

    Return Values:
    - -1: If extract_benchmark encounters an error.
    - -2: If write_benchmark_header encounters an error.
    - -3: If write_benchmark_driver encounters an error. 
    """

    if path_to_gen_suite == f"{USER_PREFIX}/generated/TSVC_2":
        main_src_path = f"{path_to_gen_suite}/src/tsvc.c"
        benchmark_dest = f"{path_to_gen_suite}/src/benchmark_{benchmark}.c"
        header_dest = f"{path_to_gen_suite}/src/benchmark.h"
        driver_dest = f"{path_to_gen_suite}/src/driver.c"
        if extract_benchmark(main_src_path, benchmark_dest, benchmark) == -1:
            return -1
        if write_benchmark_header(benchmark, header_dest) == -1:
            return -2
        if write_benchmark_driver(benchmark, benchmark_args, driver_dest) == -1:
            return -3
    return 1


def write_benchmark_driver(benchmark_name: str, benchmark_args: str, driver_dest: str):
    """
    The write_benchmark_driver function is currently "hard coded" to only work with the TSVC_2 benchmark suite.

    Parameters:
    - benchmark_name (str):   The benchmark/function name.
    - benchmark_args (str):   The arguments to the benchmark/function.
    - driver_dest (str):      The path to write the driver code.
    """
    print(f"Attempting to write driver code for benchmark: {benchmark_name}")
    try:
        driver_code = f'''#include "benchmark.h"
#include <stdio.h>

int main()
{{
    int n1 = 1;
    int n3 = 1;
    int* ip;
    real_t s1,s2;

    init(&ip, &s1, &s2);
    
    time_function(&{benchmark_name}, {benchmark_args if benchmark_args else 'NULL'});
    return 0;
}}
'''
        
        with open(driver_dest, "w") as driver_file:
            driver_file.write(driver_code)
        print(f"Driver code for {benchmark_name} written to: {driver_dest}")
        return 1 
    except Exception as e:
        print(f"An error occurred: {e}")
        return -1


def write_benchmark_header(benchmark_name, header_dest):
    """
    The write_benchmark_header function is currently hard coded to only work with benchmark suite TSVC_2.
    """
    print(f"Attempting to write header file for benchmark {benchmark_name}")
    try:
        header_code = f'''#include "common.h"

real_t {benchmark_name}(struct args_t * func_args);

typedef real_t(*test_function_t)(struct args_t *);
void time_function(test_function_t vector_func, void * arg_info);
'''
        
        with open(header_dest, "w") as header_file:
            header_file.write(header_code)     
        print(f"Header file for benchmark {benchmark_name} written to: {header_dest}")
        return 1
    except Exception as e:
        print(f"An error occurred: {e}")
        return -1


def extract_benchmark(src_path, dest_path, func_name):
    """
    The extract_benchmark function extracts a function from a provided src file and writes to
    a destination file. This function is currently "hard coded" to only work with TSVC_2.
    To generalize this, consider writing the function prelude and timing function conditionally.

    Return values:
    - -1: Benchmark/function not found in source file.
    -  1: Successful benchmark/function extraction.
    """
    print(f"Attempting to extract benchmark function {func_name}")
    index = Index.create()
    # Parse the file
    tu = index.parse(src_path)

    # Traverse the AST to find the function
    def find_function(node):
        if node.kind.name == "FUNCTION_DECL" and node.spelling == func_name:
            return node
        for child in node.get_children():
            result = find_function(child)
            if result:
                return result
        return None

    target_function = find_function(tu.cursor)
    if not target_function:
        print(f"Function '{func_name}' not found in {src_path}.")
        return -1

    # Extract the function source code
    with open(src_path, "r") as file:
        content = file.read()
    start = target_function.extent.start.offset
    end = target_function.extent.end.offset
    function_code = content[start:end]
    print(f"Function '{func_name}' extracted successfully:\n")

    print(f"Adding necessary include(s) and timing function to function code")        
    function_code = f"{TSVC_2_PRELUDE}\n{function_code}\n\n{TSVC_2_TIME_FUNCTION}"

    print(f"Writing function code to {dest_path}")
    with open(dest_path, "w") as file:
        file.write(function_code)
    return 1


if __name__ == "__main__":
    """
    TODO: Test needs to be re-written.
    """
    print(f"Testing file parsing script...")
    benchmark = "s000"
    func_args = "NULL"
    extraction_script(f"{USER_PREFIX}/benchmarks/TSVC_2", benchmark, func_args)