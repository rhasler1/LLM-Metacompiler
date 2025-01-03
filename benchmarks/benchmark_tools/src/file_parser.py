from dotenv import load_dotenv
from clang.cindex import Index
from clang.cindex import Config
import os
import re
import subprocess
load_dotenv()

# Used for testing
USER_PREFIX = os.getenv('USER_PREFIX')
OUTPUT_FILE = f"{USER_PREFIX}/benchmarks/TSVC_2/src/test.c"

INCLUDES = r"""#include <time.h>
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <sys/time.h>

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

TIME_FUNCTION = r"""typedef real_t(*test_function_t)(struct args_t *);
void time_function(test_function_t vector_func, void * arg_info)
{
    struct args_t func_args = {.arg_info=arg_info};

    double result = vector_func(&func_args);

    double tic=func_args.t1.tv_sec+(func_args.t1.tv_usec/1000000.0);
    double toc=func_args.t2.tv_sec+(func_args.t2.tv_usec/1000000.0);

    double taken = toc-tic;

    printf("%10.3f\t%f\n", taken, result);
}"""

# Replace with path to libclang.so.
Config.set_library_file("/usr/lib/llvm-18/lib/libclang.so")

# TODO: COMPLETE
def parser_script(benchmark_dir, func_name, func_args):
    src_path = f"{USER_PREFIX}/benchmarks/TSVC_2/src/tsvc.c"
    dest_path = f"{USER_PREFIX}/benchmarks/TSVC_2/src/benchmark.c"
    if extract_function(src_path, dest_path, func_name) == -1:
        return -1
    
    # Might need a benchmark.h and benchmark_llm_vec.h
    header_file_path = f"{USER_PREFIX}/benchmarks/TSVC_2/src/benchmark.h"
    if write_benchmark_header(func_name, header_file_path) == -1:
        return -1
    
    # Might need a driver.c and driver_llm_vec.c
    driver_file_path = f"{USER_PREFIX}/benchmarks/TSVC_2/src/driver.c"
    if write_driver_c(func_name, func_args, driver_file_path) == -1:
        return -1
    
    return 1


def write_driver_c(func_name, func_args, driver_file_path):
    print(f"Attempting to write driver code for benchmark: {func_name}")
    try:
        driver_code = f'''#include "benchmark.h"
#include <stdio.h>

int main()
{{
    time_function(&{func_name}, {func_args if func_args else 'NULL'});
    return 0;
}}
'''
        
        with open(driver_file_path, "w") as driver_file:
            driver_file.write(driver_code)
        
        print(f"Driver code for {func_name} written to: {driver_file_path}")
        return 1
    
    except Exception as e:
        print(f"An error occurred: {e}")
        return -1


def write_benchmark_header(func_name, header_file_path):
    print(f"Attempting to write header file for benchmark {func_name}")
    try:
        header_code = f'''#include "common.h"

real_t {func_name}(struct args_t * func_args);
'''

        with open(header_file_path, "w") as header_file:
            header_file.write(header_code)
        
        print(f"Header file for benchmark {func_name} written to: {header_file_path}")
        return 1
    
    except Exception as e:
        print(f"An error occurred: {e}")
        return -1

# Purpose: Parse TSVC_2 benchmark functions.
def extract_function(src_path, dest_path, func_name):
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
    function_code = f"{INCLUDES}\n{function_code}\n\n{TIME_FUNCTION}"
    #print(function_code)

    print(f"Writing function code to {dest_path}")
    with open(dest_path, "w") as file:
        file.write(function_code)

    return 1


if __name__ == "__main__":
    print(f"Testing file parsing script...")
    benchmark = "s000"
    func_args = "NULL"
    parser_script(USER_PREFIX, benchmark, func_args)
    #print(f"Starting function extraction test...")
    #src_path = f"{USER_PREFIX}/benchmarks/TSVC_2/src/tsvc.c"
    #dest_path = f"{USER_PREFIX}/benchmarks/TSVC_2/src/benchmark.c"
    #extract_function(src_path, dest_path, "s000")
    #print(f"Function extraction test complete.")


# TODO:
#   1. Support dynamic compilation: e.g., Use user defined compiler.
#   2. I think I will rename with module to compile_tester. Parser will be a sub-module.
#   3. At the top level (main_script) the user should be able to define the function, k-value, and compiler.
#       -> Maybe should work on this first.
#   4. On second thought, maybe it is best to get the pipeline working with default values (s000, 1, GNUs) first.
#
#
