# Use an official Ubuntu base image
FROM ubuntu:22.04

# Set the working directory
WORKDIR /workspace

# Install required system dependencies
RUN apt-get update && apt-get install -y \
    software-properties-common \
    wget \
    build-essential \
    curl \
    libssl-dev \
    zlib1g-dev \
    libbz2-dev \
    libreadline-dev \
    libsqlite3-dev \
    libffi-dev \
    libapr1-dev \
    python3.10 \
    python3.10-venv \
    python3-pip \
    vim \
    && apt-get clean

# Set Python 3.10 as default
RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.10 10 && \
    update-alternatives --install /usr/bin/python python /usr/bin/python3.10 10

# Install GCC 10.5.0
RUN add-apt-repository ppa:ubuntu-toolchain-r/test && \
    apt-get update && \
    apt-get install -y gcc-10 g++-10 && \
    update-alternatives --install /usr/bin/gcc gcc /usr/bin/gcc-10 10 && \
    update-alternatives --install /usr/bin/g++ g++ /usr/bin/g++-10 10

# Install Clang 19.0.0
RUN wget https://apt.llvm.org/llvm.sh && \
    chmod +x llvm.sh && \
    ./llvm.sh 19 && \
    update-alternatives --install /usr/bin/clang clang /usr/bin/clang-19 10 && \
    update-alternatives --install /usr/bin/clang++ clang++ /usr/bin/clang++-19 10

# Copy Python dependencies and install them
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files into the container
COPY . /workspace

# Verify installations
RUN gcc --version && g++ --version && clang --version && python3 --version && pip --version

# Default command
CMD ["/bin/bash"]

