import hashlib

def sha256_hash(file):
    """
    Chris Advena
    source: https://www.geeksforgeeks.org/compare-two-files-using-hashing-in-python/
    :param file: path of file_util to hash
    :return: sha256 hash of file_util
    """
    # A arbitrary (but fixed) buffer
    # size (change accordingly)
    # 65536 = 65536 bytes = 64 kilobytes
    BUF_SIZE = 65536

    # Initializing the sha256() method
    sha256 = hashlib.sha256()

    # Opening the file_util provided as
    # the first commandline arguement
    with open(file, 'rb') as f:

        while True:

            # reading data = BUF_SIZE from
            # the file_util and saving it in a
            # variable
            data = f.read(BUF_SIZE)

            # True if eof = 1
            if not data:
                break

            # Passing that data to that sh256 hash
            # function (updating the function with
            # that data)
            sha256.update(data)

            # sha256.hexdigest() hashes all the input
    # data passed to the sha256() via sha256.update()
    # Acts as a finalize method, after which
    # all the input data gets hashed hexdigest()
    # hashes the data, and returns the output
    # in hexadecimal format
    return sha256.hexdigest()


def md5_hash(file_path):
    """
    :param file_path:
    :return:
    """
    with open(file_path, 'rb') as file:
        md5_obj = hashlib.md5()
        while True:
            buffer = file.read(8096)
            if not buffer:
                break
            md5_obj.update(buffer)
        hash_code = md5_obj.hexdigest()
    md5 = str(hash_code).lower()
    return md5


def hash_match(filename1, filename2, hash_method: int = 0):
    """

    :param filename1:
    :param filename2:
    :param hash_method:
    :return: boolean - True is match, False if mismatch
    """
    # hash_methods is a dictionary of file_util-hashing functions that are defined above
    # in this module.
    hash_methods = {0: sha256_hash, 1: md5_hash}
    func = hash_methods[hash_method]
    return func(filename1) == func(filename2)


def main():
    pass


def examples():
    # Example: sha256_hash()
    files = 'delete.me', 'delete.me2', 'delete.me3'
    bstr = b'hello world',  b'hello world',  b'bye-bye world'
    for i in range(len(files)):
        with open(files[i], 'wb') as writer:
            writer.write(bstr[i])
    print('expect True:  ', sha256_hash(files[0]) == sha256_hash(files[1]))
    print('expect False: ', sha256_hash(files[0]) == sha256_hash(files[2]))

    # Example: hash_match()
    print('expect True:  ', hash_match(files[0], files[1]))
    print('expect False: ', hash_match(files[0], files[2]))

    hash0 = sha256_hash(files[0])
    print(hash0)
    pass

if __name__ == '__main__':
    main()
    examples()
