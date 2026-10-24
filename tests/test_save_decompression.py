import struct
import zlib

import pytest

from civ4save import NotASaveFile
from civ4save.save_file import _read_savefile


def make_save(payload, chunk_size):
    compressor = zlib.compressobj()
    compressed = compressor.compress(payload) + compressor.flush(zlib.Z_SYNC_FLUSH)
    chunks = [
        compressed[i : i + chunk_size]
        for i in range(0, len(compressed), chunk_size)
    ]
    framed = b"".join(struct.pack("<I", len(chunk)) + chunk for chunk in chunks)
    return b"header" + framed + struct.pack("<I", 0) + b"trailer", len(chunks[0])


@pytest.mark.parametrize("chunk_size", [7, 65536])
def test_decompress_framed_stream(tmp_path, chunk_size):
    payload = bytes(range(256)) * 100
    data, first_size = make_save(payload, chunk_size)
    path = tmp_path / "framed-save"
    path.write_bytes(data)

    assert _read_savefile(path) == (
        b"header" + struct.pack("<I", first_size) + payload + b"trailer"
    )


@pytest.mark.parametrize(
    "data,message",
    [
        (b"not a save", "not a .CivBeyondSwordSave"),
        (b"\x78\x9c", "not a .CivBeyondSwordSave"),
        (struct.pack("<I", 100) + b"\x78\x9c", "Truncated compressed chunk"),
        (struct.pack("<I", 2) + b"\x78\x9c\x00\x00", "Missing compressed chunk length"),
        (struct.pack("<I", 3) + b"\x78\x9c\x07", "Invalid compressed chunk"),
    ],
)
def test_invalid_compressed_framing(tmp_path, data, message):
    path = tmp_path / "invalid-save"
    path.write_bytes(data)
    with pytest.raises(NotASaveFile, match=message):
        _read_savefile(path)
