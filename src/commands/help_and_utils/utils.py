def print_as_csv(input_text):
    """print the input text as a comma separated values"""
    items = []
    for line in input_text.splitlines():
        items.extend([item.strip() for item in line.strip().split(" ") if item.strip()])
    return ",".join(items)
