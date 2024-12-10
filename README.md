### Things to Ponder:
Data-driven approaches to compiler optimizations has been explored as an alternative to traditional rule-based heuristics. 

### OBJECTIVE:
1. Recreate LLM-Vectorizer described in: https://arxiv.org/pdf/2406.04693
2. Reproduce results.


### Workflow/Description of LLM-Vectorizer

These figures are not mine! Taken from (https://arxiv.org/pdf/2406.04693).
1. User as proxy agent initiating a dialogue with a vectorizer assistant agent, providing code for vectorization and dependence analysis from the Clang compiler, highlighting why Clang cannot vectorize the loop, i.e. if there is a read-after-write, write-after-read data dependence across loop iterations.
This analysis also determines loop carries dependence i.e. if an iteration depends on the result of the previous iteration.

2. User instructs the vectorizer agent to eliminate the dependence for successful vectorization.
Internally, the vectorizer agent consults the LLM and forwards both the original and vectorized code to the compiler tester assistant agent, which employs checksum-based testing to verify the plausibility of the vectorized code.

3. If discrepancies arise, the compiler tester assistant provides feedback to the vectorizer agent, prompting code re-vectorization.
This process repeats up to ten times or until a plausible solution is found.
Checksum-based testing involves setting a loop upper bound, initializing input arrays with random values, executing both versions, and comparing output arrays.
If the vectorized code fails to compile, it's returned to the LLM for correction.


### TODO:
1. **DONE** Find the test suite for vectorizing compilers (TSVC) benchmark: https://ieeexplore.ieee.org/document/6113845.
    - Problem 1: The original link to the TSVC benchmark suite (http://polaris.cs.uiuc.edu/rmaleki/TSVC.tar.gz) is no longer accessable.
    - Resolution 1: University of Bristol's High Performance Computing group has developed an updated version of the Test Suite for Vectorizing Compilers (TSVC): https://github.com/UoB-HPC/TSVC_2

2. **DONE** Determine timing mechanism used, was timing done in software or hardware?
    - Timing mechanism is included in test bench.

3. Map/UML function calls
    - Consider looking at the Purdue pipeline-- the description of the LLM-Vectorizer is similar, in fact I believe it might be "simpler".
    - LLM-Vectorizer description suggests it only uses 1 LLM agent.
        - Not completely sure.
        This must be verified before coding.
    - LLM-Vectorizer seemingly does not do iterative improvements, it only checks for correctness in the form of check-sum.
    - If check-sum validates vectorized code, then exit.
    Else, re-feed LLM with inequivelance/error? and failed-vectorized code.

4. Build prototype (Note: The feedback loop described does not include formal verification). Verify this.

Formal verification seems to be done as an afterthought.

5. Formally verify?



### Implementation Details:

We configure GPT-4 model with a temperature set to 1.0 to enable more diversity and creativity in the responses.
The API version is set to 2023-08-01-preview.

We use GCC-10.5.0, Clang-19.0.0, ICC-2021.10.0 compilers.
The details of the compiler flags to compile unvectorized and vectorized programs are listed in Table 1.
