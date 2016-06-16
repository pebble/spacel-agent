def read_file(path, default):
    try:
        with open(path) as file_in:
            return file_in.read().rstrip()
    except IOError:
        return default
