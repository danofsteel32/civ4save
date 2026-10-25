"""Handwritten wire bytes shared by parser tests; no production builders."""

from io import BytesIO
from struct import pack


def ints(*values):
    return pack(f"<{len(values)}i", *values)


def narrow(text):
    data = text.encode("utf-8")
    return ints(len(data)) + data


def wide(text):
    data = text.encode("utf-16-le")
    return ints(len(data) // 2) + data


def free_list(records):
    # Four allocated slots, two holes, and an independent active record count.
    return (
        ints(4, 3, 0, 2, 16384)
        + ints(2, -1, -1, -1)
        + ints(len(records))
        + b"".join(records)
    )


def parse_record(schema, data):
    """Every layout check also verifies that the following section is unread."""
    stream = BytesIO(data + b"next section")
    result = schema.parse_stream(stream)
    assert stream.read() == b"next section"
    return result


def plot_bytes(x=0, y=0, populated=False):
    # Fixed CvPlot fields, following CvPlot.h's member widths.
    data = pack("<Ihh i 6h i 3h", 0, x, y, 8192, 1, 2, 3, 4, 5, 6, -1, 7, 8, 9)
    data += pack(
        "<6?b6h2b",
        True,
        False,
        True,
        False,
        True,
        False,
        -1,
        2,
        0,
        -1,
        -1,
        -1,
        -1,
        -1,
        -1,
    )
    data += ints(-1, -1, -1, -1, -1, -1) + pack("<3h", 2, 1, 0)
    # Twelve signed-byte-counted arrays, each with its own element width.
    for code in ["i", "h", "b", "i", "h", "h", "h", "b", "?", "?", "h", "h"]:
        if populated:
            values = [True, False] if code == "?" else [-1, 12]
            data += pack(f"<b2{code}", 2, *values)
        else:
            data += b"\0"
    data += narrow("plot-é" if populated else "")
    data += ints(2) + pack("<2h", -1, 300) if populated else ints(0)
    if populated:
        # Two rows, including a null row, followed by two int16 rows.
        data += pack("<b", 2) + ints(2) + pack("<2b", -1, 7) + ints(0)
        data += pack("<b", 2) + ints(0) + ints(2) + pack("<2h", -1, 500)
        data += ints(2, 0, 8193, 1, 8195)
    else:
        data += b"\0\0" + ints(0)
    return data


def map_bytes(plots, width=2, height=1):
    return (
        ints(0, width, height, 2, 1, 90, -90, 7)
        + pack("<2?", True, False)
        + ints(*range(35))
        + ints(*range(100, 135))
        + b"".join(plots)
        + ints(0, -1, -1, 0, 8192, 0)  # empty area free list
    )
