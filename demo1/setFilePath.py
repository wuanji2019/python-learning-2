while True:
    filename = input("Filename or path, or nothing at all to exit: ")
    if filename == '':
        break

    with open(filename, 'r') as f:
        # We could read the whole file at once, but this is
        # faster if the file is very large.
        for line in f:
            print(line.rstrip('\n'))
              
