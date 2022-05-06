from pathlib import Path
import zlib


def uncompress_bytes(data: bytes) -> bytes:
    """
    Uncompresses the bytes in .CivBeyondSwordSave file and returns
    the uncompressed bytes.

    There is uncompressed game data leading up to z_start and
    after z_end so it looks like this:

        | uncomp_data | compressed_data | uncomp_data |

    1. Find the byte index of the zlib magic number (z_start).
    2. Find the the byte index at the end of the zlib compressed data (z_end)
    3. Using these boundaries uncompress the compressed data
    4. Re-concat the uncomp data with compressed data
    """

    def find_zlib_start() -> int:
        """
        Find the index in where the zlib magic header is
        https://stackoverflow.com/questions/9050260/what-does-a-zlib-header-look-like
        """
        magic_number = bytes.fromhex('789c')  # default compression
        return data.find(magic_number)

    def find_zlib_end(z_start: int) -> int:
        """
        Binary search to find btye index where incomplete data stream
        becomes incorrect data stream. I'm not sure if the guess_limit
        makes sense but I do want some check to prevent infinite looping.

        https://forums.civfanatics.com/threads/need-a-little-help-with-editing-civ4-save-files.452707/
        """
        guess_limit = 100

        low, high = z_start, len(data)
        prev = 0
        guesses = 0
        while True:
            z_end = (low + high) // 2
            if z_end == prev:
                return z_end
            if guesses > guess_limit:
                return -1
            try:
                zlib.decompress(data[z_start:z_end])
            except Exception as e:
                prev = z_end
                if 'incomplete' in e.__str__():
                    low = z_end + 1
                elif 'invalid' in e.__str__():
                    high = z_end - 1
            guesses += 1

    z_start = find_zlib_start()
    z_end = find_zlib_end(z_start)
    if z_start < 0 or z_end < 0:
        raise Exception('This is not a .CivBeyondSwordSave file')

    decomp_obj = zlib.decompressobj()
    uncompressed_data = decomp_obj.decompress(data[z_start:z_end])
    return data[:z_start] + uncompressed_data + data[z_end:]


def read(file: str | Path) -> bytes:
    with open(file, 'rb') as f:
        data = f.read()
    return uncompress_bytes(data)
