"""capture_books.py: parsing a multi-book response, best price per card leg, and the budget guards (no network)."""
import capture_books as cb

PULLED = "2026-10-23T13:07+00:00"


def odds_response():
    """shape of an Odds API /events/{id}/odds response with several books (made-up prices)"""
    def book(key, rec_alt, yds_main, rec_main=None):
        markets = [{"key": "player_receptions_alternate",
                    "outcomes": [{"name": "Over", "description": "Puka Nacua", "point": p, "price": o} for p, o in rec_alt]},
                   {"key": "player_reception_yds",
                    "outcomes": [{"name": side, "description": "Puka Nacua", "point": 79.5, "price": o}
                                 for side, o in zip(("Over", "Under"), yds_main)]}]
        if rec_main:
            markets.append({"key": "player_receptions", "outcomes": [{"name": s, "description": "Puka Nacua", "point": 6.5, "price": o}
                                                                    for s, o in zip(("Over", "Under"), rec_main)]})
        markets.append({"key": "player_pass_yds", "outcomes": [{"name": "Over", "description": "QB", "point": 250.5, "price": -110}]})
        return {"key": key, "markets": markets}
    return {"bookmakers": [
        book("draftkings", [(4.5, -400), (5.5, -210)], (-115, -105), rec_main=(-120, -110)),
        book("fanduel", [(4.5, -360), (5.5, -220)], (-110, -110)),
        book("betmgm", [(4.5, -420)], (-105, -125)),
        book("bovada", [(4.5, -250)], (-100, -120)),           # offshore: not in the six books, must be ignored
    ]}


def rows():
    return cb.parse_event(odds_response(), "LA @ SEA", "2026-10-25T20:25:00Z", PULLED)


def test_parse_keeps_six_books_and_two_markets_only():
    r = rows()
    assert {x["Book"] for x in r} == {"draftkings", "fanduel", "betmgm"}       # bovada dropped
    assert {x["Market"] for x in r} == {"receptions", "rec_yds"}               # pass_yds dropped
    alt = [x for x in r if x["Kind"] == "alt"]
    assert all(x["Side"] == "Over" for x in alt)
    main = [x for x in r if x["Kind"] == "main" and x["Market"] == "rec_yds"]
    assert len(main) == 6 and {x["Side"] for x in main} == {"Over", "Under"}
    assert all(x["PulledAt"] == PULLED for x in r)


def test_best_price_per_card_leg():
    card = {"candidates": [dict(player="Puka Nacua", market="receptions", rung=5.0, published_odds=-400),
                           dict(player="Puka Nacua", market="receptions", rung=6.0, published_odds=-210),
                           dict(player="Puka Nacua", market="rush_yds", rung=20.0, published_odds=-300)],
            "tickets": [{"legs": [dict(player="Puka Nacua", market="receptions", rung=5.0, published_odds=-400)]}]}
    legs = {(l["market"], l["rung"]): l for l in cb.best_for_legs(card, rows())}
    assert len(legs) == 3                                                       # ticket leg de-duplicated
    a = legs[("receptions", 5.0)]
    assert a["books"] == {"draftkings": -400, "fanduel": -360, "betmgm": -420}
    assert (a["best_book"], a["best_odds"], a["dk_odds"], a["best_beats_dk"]) == ("fanduel", -360, -400, True)
    b = legs[("receptions", 6.0)]
    assert (b["best_book"], b["best_odds"], b["best_beats_dk"]) == ("draftkings", -210, False)
    assert legs[("rush_yds", 20.0)]["captured"] is False


def test_main_line_counts_as_a_rung_and_better_price_wins():
    # DK posts 7+ only as its main Over 6.5 at -120: the leg at rung 7 still gets DK's price from the main line
    card = {"candidates": [dict(player="Puka Nacua", market="receptions", rung=7.0, published_odds=-120)]}
    (leg,) = cb.best_for_legs(card, rows())
    assert leg["books"] == {"draftkings": -120} and leg["best_book"] == "draftkings"


def test_no_prices_for_a_leg():
    card = {"candidates": [dict(player="Somebody Else", market="rec_yds", rung=40.0, published_odds=-250)]}
    (leg,) = cb.best_for_legs(card, rows())
    assert leg["captured"] and leg["books"] == {} and leg["best_odds"] is None and leg["best_beats_dk"] is False


def test_guards():
    ev = [{}] * 16
    assert cb.guard([], 500_000, 100_000, 400) == "no unstarted games on this slate this week"
    assert cb.guard(ev, 500_000, 100_000, 400) is None                          # 64 credits
    assert "NFL_BOOKS_CAP" in cb.guard([{}] * 120, 500_000, 100_000, 400)
    assert "NFL_BOOKS_RESERVE" in cb.guard(ev, 100_050, 100_000, 400)
    assert cb.guard(ev, None, 100_000, 400) is None                             # header missing: cap still applies


def test_cost_per_game_is_one_credit_per_market():
    assert cb.PER_GAME == 4
