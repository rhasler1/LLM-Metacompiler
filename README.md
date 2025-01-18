### Initial objective
Implement LLM-Vectorizer as described in: https://arxiv.org/pdf/2406.04693

### Installation & Setup
1. Clone This repository. Then git checkout dev.
2. Clone the following repo into the benchmarks directory: https://github.com/rhasler1/TSVC_2. Then git checkout indiv-test-exec.
3. Create a .env file at /LLM-Metacompiler/.env
4. Set variables API_KEY and USER_PREFIX
    - API_KEY is an OpenAI API key.
    - USER_PREFIX set to /workspace.
5. docker build -t metacompiler-img:0.1 .
6. docker run -it metacompiler-img:0.1 bash
7. make run s000

### Execution
Execution command: make run <benchmark> <compiler> <model> <k_max> 
s000 clang

s000: function name
clang: compiler
