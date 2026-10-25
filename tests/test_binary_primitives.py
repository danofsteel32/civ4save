"""Wire widths, string lengths, and adapters used throughout the parser."""

from struct import pack

import pytest
from construct import Array, StreamError, ValidationError

from civ4save.vanilla import enums as e
from civ4save.vanilla import structure as s
from tests.binary_helpers import ints, narrow, parse_record, wide


@pytest.mark.parametrize("schema,encode", [(s.STRING, narrow), (s.WSTRING, wide)])
@pytest.mark.parametrize("text", ["", "é", "A😀B"])
def test_string_lengths_and_unicode(schema, encode, text):
    data = encode(text)
    raw = parse_record(schema, data)
    assert raw.string == text
    assert raw._sz == (len(data) - 4) // (2 if schema is s.WSTRING else 1)
    assert parse_record(s.StringAdapter(schema), data) == text


@pytest.mark.parametrize("schema", [s.STRING, s.WSTRING])
def test_invalid_string_lengths(schema):
    with pytest.raises(ValidationError, match="_sz"):
        schema.parse(ints(-1))
    with pytest.raises(StreamError):
        schema.parse(ints(2) + b"a")


@pytest.mark.parametrize(
    "adapter,schema,encode",
    [
        (s.StringArrayAdapter, s.STRING, narrow),
        (s.WStringArrayAdapter, s.WSTRING, wide),
    ],
)
def test_string_array_adapters(adapter, schema, encode):
    values = ["", "café", "😀"]
    assert (
        parse_record(adapter(Array(3, schema)), b"".join(map(encode, values))) == values
    )


@pytest.mark.parametrize(
    "schema,code,values",
    [
        (s.CHAR_INT_ARRAY, "bi", [-2147483648, 2147483647]),
        (s.CHAR_SHORT_ARRAY, "bh", [-32768, 32767]),
        (s.CHAR_CHAR_ARRAY, "bb", [-128, 127]),
        (s.CHAR_FLAG_ARRAY, "b?", [True, False]),
        (s.INT_SHORT_ARRAY, "ih", [-32768, 32767]),
    ],
)
def test_counted_arrays(schema, code, values):
    prefix, item = code
    data = pack(f"<{prefix}2{item}", 2, *values)
    assert parse_record(schema, data).arr == values
    assert parse_record(schema, pack(f"<{prefix}", 0)).arr == []
    with pytest.raises(ValidationError):
        schema.parse(pack(f"<{prefix}", -1))
    with pytest.raises(StreamError):
        schema.parse(data[:-1])


def test_enum_arrays_exclude_negative_sentinels():
    schema = s.EnumArrayAdapter(e.VoteSourceType, s.INT[2])
    assert parse_record(schema, ints(7, -1)) == {
        e.VoteSourceType.DIPLOVOTE_UN: 7,
        e.VoteSourceType.DIPLOVOTE_POPE: -1,
    }


def test_id_info_preserves_signed_sentinels():
    city = parse_record(s.IDINFO, ints(-1, -1))
    assert (city.owner, city.i_id) == (-1, -1)
