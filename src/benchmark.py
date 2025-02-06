from dotenv import load_dotenv
import os
import shutil
import sys

from clang.cindex import Index
from clang.cindex import Config
from compilation_tool import compilation_tool
from execution_tool import execution_tool
load_dotenv()


#def main_script(path_to_gen: str, suite: str, benchmark: str, benchmark_args: str, instruction_set: str, compiler: str, llm_agent: LLMAgent, k_max: int):
class BenchmarkSuite:
    USER_PREFIX = os.getenv("USER_PREFIX")
    PATH_TO_GEN = f"{USER_PREFIX}/generated"

    def __init__(self, benchmark_suite, benchmark):
        self.benchmark_suite = benchmark_suite
        self.benchmark = benchmark
    
    def compile_benchmark(self, make_command):
        raise NotImplementedError("Subclasses should implement this method.")
    
    def execute_benchmark(self, suffix):
        raise NotImplementedError("Subclasses should implement this method.")

    def init_benchmark(self):
        raise NotImplementedError("Subclasses should implement this method.")
    
    def comp_dest(self, make_command):
        raise NotImplementedError("Subclasses should implement this method.")
    
    def exec_path(self, suffix):
        raise NotImplementedError("Subclasses should implement this method.")
    
    def exec_dest(self, suffix):
        raise NotImplementedError("Subclasses should implement this method.")
    


class TSVC2Suite(BenchmarkSuite):
    PATH_TO_SUITE = f"{BenchmarkSuite.USER_PREFIX}/benchmarks/TSVC_2"
    PATH_TO_GEN_SUITE = f"{BenchmarkSuite.PATH_TO_GEN}/TSVC_2"

    def __init__(self, benchmark, benchmark_args, instruction_set, compiler):
        super().__init__("TSVC_2", benchmark)
        self.benchmark_args = benchmark_args
        self.instruction_set = instruction_set
        self.compiler = compiler

    def comp_dest(self, make_command):
        return f"{self.PATH_TO_GEN_SUITE}/compilation/{self.compiler}/{make_command}_{self.benchmark}.txt"
    
    def exec_path(self, suffix):
        return f"{self.PATH_TO_GEN_SUITE}/bin/{self.compiler}/{self.benchmark}_{suffix}"
    
    def exec_dest(self, suffix):
        return f"{self.PATH_TO_GEN_SUITE}/execution/{self.compiler}/{self.benchmark}_{suffix}.txt"

    def compile_benchmark(self, make_command):
        # Setting paths
        comp_dest = self.comp_dest(make_command)

        # Compiling
        status = compilation_tool(self.PATH_TO_GEN_SUITE, make_command, self.compiler, self.benchmark, comp_dest)
        if status != 1:
            return -1
        return 1

    def execute_benchmark(self, suffix):
        # Setting paths
        # Suffix should be novec, vec, llm_vec
        exec_path = self.exec_path(suffix)
        exec_dest = self.exec_dest(suffix)
    
        # Executing
        status = execution_tool(exec_path, exec_dest)
        if status != 1:
            return -1
        return 1

    def init_benchmark(self):
        if self.parse_benchmark() != 1:
            return -1
        if self.generate_header() != 1:
            return -1
        if self.generate_driver() != 1:
            return -1
        return 1

    def generate_header(self):
        header_dest = f"{self.PATH_TO_GEN_SUITE}/src/benchmark.h"
        try:
            header_code = f'''#include "common.h"

    real_t {self.benchmark}(struct args_t * func_args);

    typedef real_t(*test_function_t)(struct args_t *);
    void time_function(test_function_t vector_func, void * arg_info);
    '''
            with open(header_dest, "w") as header_file:
                header_file.write(header_code)     
            print(f"Header file for benchmark {self.benchmark} written to: {header_dest}")
            return 1
        except Exception as e:
            print(f"An error occurred: {e}")
        return -1
    
    def generate_driver(self):
        driver_dest = f"{self.PATH_TO_GEN_SUITE}/src/driver.c"
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
        
        time_function(&{self.benchmark}, {self.benchmark_args if self.benchmark_args else 'NULL'});
        return 0;
    }}
    '''
            with open(driver_dest, "w") as driver_file:
                driver_file.write(driver_code)
                print(f"Driver code for {self.benchmark} written to: {driver_dest}")
                return 1 
        except Exception as e:
            print(f"An error occurred: {e}")
            return -1

    def parse_benchmark(self):
        # Setting paths needed to parse
        # Initial path to the c file containing benchmarks
        benchmark_src_path = f"{self.PATH_TO_GEN_SUITE}/src/tsvc.c"
        # Destination path to place the extracted benchmark
        benchmark_dest = f"{self.PATH_TO_GEN_SUITE}/src/benchmark_{self.benchmark}.c"

        #1:Extract benchmark::Start
        index = Index.create()
        tu = index.parse(benchmark_src_path)

        # Traverse the AST to find the function
        def find_function(node):
            if node.kind.name == "FUNCTION_DECL" and node.spelling == self.benchmark:
                return node
            for child in node.get_children():
                result = find_function(child)
                if result:
                    return result
            return None

        target_function = find_function(tu.cursor)
        if not target_function:
            print(f"Function '{self.benchmark}' not found in {benchmark_src_path}.")
            return -1

        # Extract the function source code
        with open(benchmark_src_path, "r") as file:
            content = file.read()
        start = target_function.extent.start.offset
        end = target_function.extent.end.offset
        function_code = content[start:end]
        print(f"Function '{self.benchmark}' extracted successfully:\n")

        print(f"Adding necessary include(s) and timing function to function code")        
        function_code = f"{self.function_prelude()}\n{function_code}\n\n{self.time_function()}"

        print(f"Writing function code to {benchmark_dest}")
        with open(benchmark_dest, "w") as file:
            file.write(function_code)

        #1:Extract benchmark::End
        return 1
        
    def function_prelude(self):
        return r"""#include <time.h>
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

    def time_function(self):
        return r"""typedef real_t(*test_function_t)(struct args_t *);
void time_function(test_function_t vector_func, void * arg_info)
{
    struct args_t func_args = {.arg_info=arg_info};

    double result = vector_func(&func_args);

    double tic=func_args.t1.tv_sec+(func_args.t1.tv_usec/1000000.0);
    double toc=func_args.t2.tv_sec+(func_args.t2.tv_usec/1000000.0);

    double taken = toc-tic;

    printf("%10.3f\t%f\n", taken, result);
}"""