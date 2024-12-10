# Compiler to use
CC = gcc

# Compiler flags
CFLAGS = -Wall -Wextra -g

# Target executable
TARGET = hello

# Build target
all: $(TARGET)

# Rule to build the target
$(TARGET): hello.o
	$(CC) $(CFLAGS) -o $(TARGET) hello.o

# Rule to build the object file
hello.o: hello.c
	$(CC) $(CFLAGS) -c hello.c

# Clean up generated files
clean:
	rm -f $(TARGET) hello.o

# Target for running the program
run: $(TARGET)
	./$(TARGET)