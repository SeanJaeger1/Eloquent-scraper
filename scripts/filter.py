import json


def load_and_print_json(filename):
    # Open the JSON file for reading
    with open(filename, "r") as file:
        # Load the data from the file
        data = json.load(file)
        # Print the loaded data
        print(data)


# Example usage
if __name__ == "__main__":
    load_and_print_json("swears.json")
