### Initial objective
Implement LLM-Vectorizer as described in: https://arxiv.org/pdf/2406.04693

### Installation & Setup using Docker
1. Clone This repository.
2. Clone the following repo into the benchmarks directory: https://github.com/rhasler1/TSVC_2. CD into TSVC_2 and git checkout indiv-test-exec.
3. Create a .env file at /LLM-Metacompiler/.env
4. Set variables API_KEY and USER_PREFIX
    - API_KEY is an OpenAI API key.
    - USER_PREFIX set to /workspace.
5. docker build -t metacompiler-img:0.1 .
6. docker run -it metacompiler-img:0.1 bash
    - Consider using bind mounts or volumes
7. make run -- -i AVX2 -b TSVC_2 -f s000 -c clang

### TODO
1. Optimize dockerfile/image
2. Add ARM Neon support
