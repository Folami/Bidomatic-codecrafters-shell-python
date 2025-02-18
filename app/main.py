import sys


def main():
    # Uncomment this block to pass the first stage
    sys.stdout.write("$ ")

    # Wait for user input
    while True:
        command = input()
        #if command == "exit":
         #   break
        print(f"{command}: command not found")
        sys.stdout.write("$ ")


if __name__ == "__main__":
    main()
