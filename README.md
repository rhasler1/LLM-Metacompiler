### Initial objective
Implement LLM-Vectorizer as described in: https://arxiv.org/pdf/2406.04693

### Installation & Setup
1. Clone This repository.
2. Clone the following repo into the benchmarks directory: https://github.com/rhasler1/TSVC_2
3. Create a .env file at /LLM-Metacompiler/.env
4. Set variables API_KEY and USER_PREFIX
    - API_KEY is an OpenAI API key.
    - USER_PREFIX is the absolute path to the LLM-Metacompiler directory on your system.
5. Create a python venv. E.g., python3 -m venv myenv
6. Activate myenv and run command: make setup

### Execution
Example command: make run s000 clang

s000: function name
clang: compiler
