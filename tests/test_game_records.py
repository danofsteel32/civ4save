"""SDK layouts for the records nested in CvGame."""

from struct import pack

import pytest
from construct import StreamError, ValidationError

from civ4save.vanilla import enums as e
from civ4save.vanilla import structure as s
from tests.binary_helpers import free_list, ints, parse_record, wide


def trade_bytes(item, extra, offering=False, hidden=True):
    # TradeData is a raw 12-byte C++ struct: two ints, two bools, tail padding.
    return pack("<ii??", item, extra, offering, hidden) + b"\xa5\x5a"


def deal_bytes(deal_id=8193):
    first = [
        trade_bytes(e.TradeableItem.TRADE_GOLD, 50),
        trade_bytes(e.TradeableItem.TRADE_GOLD_PER_TURN, 3),
        trade_bytes(e.TradeableItem.TRADE_RESOURCES, e.BonusType.BONUS_COPPER),
        trade_bytes(e.TradeableItem.TRADE_OPEN_BORDERS, -1),
    ]
    return (
        ints(0, deal_id, 86, 0, 1, len(first))
        + b"".join(first)
        + ints(1)
        + trade_bytes(e.TradeableItem.TRADE_GOLD, 10, offering=True, hidden=False)
    )


def vote_option_bytes(text="Vote 😀"):
    return ints(0, -1, -1, 1) + wide(text)


def test_trade_flags_precede_tail_padding():
    trade = parse_record(s.TradeData, trade_bytes(e.TradeableItem.TRADE_GOLD, -1))
    assert trade.item == "TRADE_GOLD"
    assert trade.extra_data == -1
    assert trade.offering is False
    assert trade.hidden is True


def test_deal_wire_layout_and_trade_interpretation():
    data = deal_bytes()
    raw = parse_record(s.CvDeal, data)
    assert (raw._flag, raw.id, raw.initial_game_turn) == (0, 8193, 86)
    assert (raw.first_player, raw.second_player) == (0, 1)
    assert len(raw.first_trades) == 4
    assert raw.second_trades[0].offering is True
    assert raw.second_trades[0].hidden is False
    parsed = parse_record(s.CvDealList, free_list([data, deal_bytes(8195)]))
    expected = {
        "first_player": 0,
        "second_player": 1,
        "initial_game_turn": 86,
        "first_trades": [
            {"item": e.TradeableItem.TRADE_GOLD, "amount": 50},
            {"item": e.TradeableItem.TRADE_GOLD_PER_TURN, "amount": 3},
            {"item": e.BonusType.BONUS_COPPER, "amount": 1},
            {"item": e.TradeableItem.TRADE_OPEN_BORDERS, "amount": 1},
        ],
        "second_trades": [{"item": e.TradeableItem.TRADE_GOLD, "amount": 10}],
    }
    assert parsed.deals == [expected, expected]


def test_votes_and_option_strings():
    option = parse_record(s.VoteOption, vote_option_bytes())
    assert option.type == e.VoteType(0).name
    assert (option.player, option.city_id, option.other_player) == (-1, -1, 1)
    assert option.text == "Vote 😀"
    selection_data = ints(8193, 1, 2) + vote_option_bytes() + vote_option_bytes("")
    selection = parse_record(s.VoteSelection, selection_data)
    assert (selection.vote_id, selection.vote_source) == (8193, "DIPLOVOTE_POPE")
    assert [value.text for value in selection.vote_options] == ["Vote 😀", ""]
    selections = parse_record(s.VoteSelectionList, free_list([selection_data]))
    assert selections.vote_selections[0].vote_options == selection.vote_options
    triggered_data = ints(8195, 0) + vote_option_bytes()
    triggered = parse_record(s.VoteTriggeredList, free_list([triggered_data]))
    assert triggered.votes_triggered[0].vote_id == 8195
    assert triggered.votes_triggered[0].vote_source == "DIPLOVOTE_UN"
    assert triggered.votes_triggered[0].vote_option.text == "Vote 😀"


def test_replay_message_wire_layout():
    data = ints(86, 2, -1, 12, -1) + wide("A city fell 😀") + ints(2)
    message = parse_record(s.CvReplayMessage, data)
    assert (message.turn, message.type) == (86, "PLOT_OWNER_CHANGE")
    assert (message.plot_x, message.plot_y, message.player) == (-1, 12, -1)
    assert message.text == "A city fell 😀"
    assert message.e_color == "COLOR_WHITE"


def test_plot_extras_and_vote_religions():
    yields = parse_record(s.PlotExtraYield, ints(2, 3, -1, 4, 5))
    assert (yields.plot_x, yields.plot_y, yields.extra_yields) == (2, 3, [-1, 4, 5])
    cost = parse_record(s.PlotExtraCost, ints(2, 3, -8))
    assert (cost.plot_x, cost.plot_y, cost.extra_costs) == (2, 3, -8)
    religion = parse_record(s.VoteSourceReligion, ints(1, 2))
    assert religion.vote_source == "DIPLOVOTE_POPE"
    assert religion.religion == e.ReligionType(2).name


@pytest.mark.parametrize(
    "schema,field",
    [
        (s.CvDealList, "deals"),
        (s.VoteSelectionList, "vote_selections"),
        (s.VoteTriggeredList, "votes_triggered"),
    ],
)
def test_game_free_list_counts(schema, field):
    assert parse_record(schema, free_list([]))[field] == []
    for count in [-1, 5]:
        with pytest.raises(ValidationError):
            schema.parse(free_list([])[:-4] + ints(count))
    for slots in [-1, 8193]:
        with pytest.raises(ValidationError):
            schema.parse(ints(slots))


@pytest.mark.parametrize(
    "schema,data",
    [
        (s.TradeData, trade_bytes(0, 5)),
        (s.CvDeal, deal_bytes()),
        (s.VoteOption, vote_option_bytes()),
        (s.VoteSelection, ints(8193, 1, 1) + vote_option_bytes()),
        (s.VoteTriggered, ints(8193, 1) + vote_option_bytes()),
        (s.CvReplayMessage, ints(86, 2, -1, 12, -1) + wide("text") + ints(2)),
        (s.PlotExtraYield, ints(2, 3, 4, 5, 6)),
        (s.PlotExtraCost, ints(2, 3, 4)),
        (s.VoteSourceReligion, ints(1, 2)),
    ],
)
def test_truncated_game_records(schema, data):
    with pytest.raises(StreamError):
        schema.parse(data[:-1])


@pytest.mark.parametrize(
    "schema,data",
    [(s.CvDeal, ints(0, 8193, 86, 0, 1, -1)), (s.VoteSelection, ints(8193, 0, -1))],
)
def test_negative_record_counts(schema, data):
    with pytest.raises(ValidationError):
        schema.parse(data)
