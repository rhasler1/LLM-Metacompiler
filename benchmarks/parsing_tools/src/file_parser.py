from dotenv import load_dotenv
from clang.cindex import Index
from clang.cindex import Config
import os
import re
import subprocess
load_dotenv()

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

# Purpose: Parse TSVC_2 benchmark functions.
def extract_function(file_path, function_name):
    index = Index.create()
    # Parse the file
    tu = index.parse(file_path)

    # Traverse the AST to find the function
    def find_function(node):
        if node.kind.name == "FUNCTION_DECL" and node.spelling == function_name:
            return node
        for child in node.get_children():
            result = find_function(child)
            if result:
                return result
        return None

    target_function = find_function(tu.cursor)
    if not target_function:
        print(f"Function '{function_name}' not found in {file_path}.")
        return -1

    # Extract the function source code
    with open(file_path, "r") as file:
        content = file.read()
    start = target_function.extent.start.offset
    end = target_function.extent.end.offset
    function_code = content[start:end]

    print(f"Function '{function_name}' extracted successfully:\n")
    function_code = f"{INCLUDES}\n{function_code}\n\n{TIME_FUNCTION}"
    #print(function_code)

    with open(OUTPUT_FILE, "w") as file:
        file.write(function_code)

    return 1


if __name__ == "__main__":
    print(f"Starting function extraction...")
    file_path = f"{USER_PREFIX}/benchmarks/TSVC_2/src/tsvc.c"
    extract_function(file_path, "s000")


# TODO:
#   1. Support dynamic compilation: e.g., Use user defined compiler.
#   2. I think I will rename with module to compile_tester. Parser will be a sub-module.
#   3. At the top level (main_script) the user should be able to define the function, k-value, and compiler.
#       -> Maybe should work on this first.
#   4. On second thought, maybe it is best to get the pipeline working with default values (s000, 1, GNUs) first.
#
#
