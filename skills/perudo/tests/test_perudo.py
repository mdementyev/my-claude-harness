# skills/perudo/tests/test_perudo.py
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Optional

SCRIPT = str(Path(__file__).resolve().parent.parent / "scripts" / "perudo.py")


def run_engine(command: str, args: Optional[list[str]] = None, stdin_data: Optional[str] = None) -> dict:
    """Run perudo.py with given command and return parsed JSON output."""
    cmd = [sys.executable, SCRIPT, command] + (args or [])
    result = subprocess.run(cmd, input=stdin_data, capture_output=True, text=True)
    assert result.returncode == 0, f"Engine error: {result.stderr}"
    return json.loads(result.stdout)


class TestInit:
    def test_creates_correct_number_of_players(self):
        state = run_engine("init", ["3"])
        assert len(state["players"]) == 3

    def test_each_player_has_5_dice(self):
        state = run_engine("init", ["4"])
        for player in state["players"]:
            assert player["dice_count"] == 5
            assert len(player["dice"]) == 5

    def test_dice_values_are_1_to_6(self):
        state = run_engine("init", ["2"])
        for player in state["players"]:
            for die in player["dice"]:
                assert 1 <= die <= 6

    def test_player_ids_are_sequential(self):
        state = run_engine("init", ["4"])
        ids = [p["id"] for p in state["players"]]
        assert ids == [1, 2, 3, 4]

    def test_player_names(self):
        state = run_engine("init", ["3"])
        names = [p["name"] for p in state["players"]]
        assert names == ["Agent-1", "Agent-2", "Agent-3"]

    def test_initial_state_fields(self):
        state = run_engine("init", ["2"])
        assert state["current_player_id"] == 1
        assert state["round"] == 1
        assert state["current_bid"] is None
        assert state["bid_history"] == []
        assert state["palifico"] is False
        assert state["palifico_starter_id"] is None
        assert state["palifico_locked_face"] is None
        assert state["palifico_face_unlocked"] is False
        assert state["phase"] == "awaiting_action"
        assert state["total_dice"] == 10

    def test_players_not_eliminated(self):
        state = run_engine("init", ["3"])
        for player in state["players"]:
            assert player["eliminated"] is False
            assert player["palifico_used"] is False

    def test_seed_produces_reproducible_dice(self):
        state1 = run_engine("init", ["3", "--seed", "42"])
        state2 = run_engine("init", ["3", "--seed", "42"])
        for p1, p2 in zip(state1["players"], state2["players"]):
            assert p1["dice"] == p2["dice"]

    def test_different_seeds_produce_different_dice(self):
        state1 = run_engine("init", ["3", "--seed", "42"])
        state2 = run_engine("init", ["3", "--seed", "99"])
        all_same = all(
            p1["dice"] == p2["dice"]
            for p1, p2 in zip(state1["players"], state2["players"])
        )
        assert not all_same

    def test_invalid_player_count_too_low(self):
        cmd = [sys.executable, SCRIPT, "init", "1"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        assert result.returncode != 0
        error = json.loads(result.stderr)
        assert "error" in error

    def test_invalid_player_count_too_high(self):
        cmd = [sys.executable, SCRIPT, "init", "7"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        assert result.returncode != 0
        error = json.loads(result.stderr)
        assert "error" in error


def make_state_with_bid(current_bid=None, palifico=False,
                        palifico_locked_face=None,
                        palifico_face_unlocked=False,
                        palifico_starter_id=None):
    """Create a minimal game state JSON string for bid validation tests."""
    state = {
        "players": [
            {"id": 1, "name": "Agent-1", "dice_count": 5, "dice": [1, 2, 3, 4, 5], "eliminated": False, "palifico_used": False},
            {"id": 2, "name": "Agent-2", "dice_count": 5, "dice": [2, 3, 4, 5, 6], "eliminated": False, "palifico_used": False},
        ],
        "current_player_id": 2 if current_bid else 1,
        "round": 1,
        "current_bid": current_bid,
        "bid_history": [],
        "palifico": palifico,
        "palifico_starter_id": palifico_starter_id,
        "palifico_locked_face": palifico_locked_face,
        "palifico_face_unlocked": palifico_face_unlocked,
        "phase": "awaiting_action",
        "total_dice": 10,
        "seed": None,
    }
    return json.dumps(state)


class TestValidateBid:
    def test_first_bid_any_value_is_valid(self):
        state_json = make_state_with_bid(current_bid=None)
        result = run_engine("validate_bid", ["1", "3"], stdin_data=state_json)
        assert result["valid"] is True

    def test_first_bid_minimum_quantity(self):
        state_json = make_state_with_bid(current_bid=None)
        result = run_engine("validate_bid", ["1", "2"], stdin_data=state_json)
        assert result["valid"] is True

    def test_higher_quantity_is_valid(self):
        bid = {"quantity": 3, "face_value": 4, "bidder_id": 1}
        state_json = make_state_with_bid(current_bid=bid)
        result = run_engine("validate_bid", ["4", "2"], stdin_data=state_json)
        assert result["valid"] is True

    def test_same_quantity_higher_face_is_valid(self):
        bid = {"quantity": 3, "face_value": 4, "bidder_id": 1}
        state_json = make_state_with_bid(current_bid=bid)
        result = run_engine("validate_bid", ["3", "5"], stdin_data=state_json)
        assert result["valid"] is True

    def test_same_quantity_same_face_is_invalid(self):
        bid = {"quantity": 3, "face_value": 4, "bidder_id": 1}
        state_json = make_state_with_bid(current_bid=bid)
        result = run_engine("validate_bid", ["3", "4"], stdin_data=state_json)
        assert result["valid"] is False

    def test_lower_quantity_is_invalid(self):
        bid = {"quantity": 3, "face_value": 4, "bidder_id": 1}
        state_json = make_state_with_bid(current_bid=bid)
        result = run_engine("validate_bid", ["2", "6"], stdin_data=state_json)
        assert result["valid"] is False

    def test_same_quantity_lower_face_is_invalid(self):
        bid = {"quantity": 3, "face_value": 4, "bidder_id": 1}
        state_json = make_state_with_bid(current_bid=bid)
        result = run_engine("validate_bid", ["3", "3"], stdin_data=state_json)
        assert result["valid"] is False

    def test_face_value_out_of_range_high(self):
        state_json = make_state_with_bid(current_bid=None)
        result = run_engine("validate_bid", ["1", "7"], stdin_data=state_json)
        assert result["valid"] is False

    def test_face_value_out_of_range_low(self):
        state_json = make_state_with_bid(current_bid=None)
        result = run_engine("validate_bid", ["1", "0"], stdin_data=state_json)
        assert result["valid"] is False

    def test_quantity_zero_is_invalid(self):
        state_json = make_state_with_bid(current_bid=None)
        result = run_engine("validate_bid", ["0", "3"], stdin_data=state_json)
        assert result["valid"] is False

    def test_palifico_same_face_higher_quantity_valid(self):
        bid = {"quantity": 2, "face_value": 4, "bidder_id": 1}
        state_json = make_state_with_bid(
            current_bid=bid, palifico=True,
            palifico_locked_face=4, palifico_starter_id=1,
        )
        result = run_engine("validate_bid", ["3", "4"], stdin_data=state_json)
        assert result["valid"] is True

    def test_palifico_different_face_is_invalid_while_locked(self):
        bid = {"quantity": 2, "face_value": 4, "bidder_id": 1}
        state_json = make_state_with_bid(
            current_bid=bid, palifico=True,
            palifico_locked_face=4, palifico_starter_id=1,
        )
        result = run_engine("validate_bid", ["3", "5"], stdin_data=state_json)
        assert result["valid"] is False

    def test_palifico_face_unlocked_allows_different_face(self):
        bid = {"quantity": 2, "face_value": 4, "bidder_id": 1}
        state_json = make_state_with_bid(
            current_bid=bid, palifico=True,
            palifico_locked_face=4, palifico_starter_id=1,
            palifico_face_unlocked=True,
        )
        result = run_engine("validate_bid", ["3", "5"], stdin_data=state_json)
        assert result["valid"] is True


def make_game_state(players_data, current_bid, palifico=False, round_num=1, seed=42):
    """Create a full game state for resolve_call tests.
    players_data: list of {"id", "dice", "eliminated"} dicts.
    """
    players = []
    total_dice = 0
    for pd in players_data:
        dice = pd["dice"]
        eliminated = pd.get("eliminated", False)
        players.append({
            "id": pd["id"],
            "name": f"Agent-{pd['id']}",
            "dice_count": len(dice) if not eliminated else 0,
            "dice": dice if not eliminated else [],
            "eliminated": eliminated,
            "palifico_used": pd.get("palifico_used", False),
        })
        if not eliminated:
            total_dice += len(dice)

    return json.dumps({
        "players": players,
        "current_player_id": current_bid["bidder_id"],
        "round": round_num,
        "current_bid": current_bid,
        "bid_history": [],
        "palifico": palifico,
        "palifico_starter_id": None,
        "palifico_locked_face": None,
        "palifico_face_unlocked": False,
        "phase": "awaiting_action",
        "total_dice": total_dice,
        "seed": seed,
    })


class TestResolveCall:
    def test_bid_met_caller_loses_die(self):
        """Bid: 3x fours. Player 1 has [4,4,2], Player 2 has [4,3,5]. Total fours = 3. Bid met -> caller loses."""
        state_json = make_game_state(
            players_data=[
                {"id": 1, "dice": [4, 4, 2]},
                {"id": 2, "dice": [4, 3, 5]},
            ],
            current_bid={"quantity": 3, "face_value": 4, "bidder_id": 1},
        )
        result = run_engine("resolve_call", ["2"], stdin_data=state_json)
        assert result["call_result"]["loser_id"] == 2
        assert result["call_result"]["actual_count"] == 3

    def test_bid_not_met_bidder_loses_die(self):
        """Bid: 4x fours. Player 1 has [4,4,2], Player 2 has [4,3,5]. Total fours = 3. Not met -> bidder loses."""
        state_json = make_game_state(
            players_data=[
                {"id": 1, "dice": [4, 4, 2]},
                {"id": 2, "dice": [4, 3, 5]},
            ],
            current_bid={"quantity": 4, "face_value": 4, "bidder_id": 1},
        )
        result = run_engine("resolve_call", ["2"], stdin_data=state_json)
        assert result["call_result"]["loser_id"] == 1
        assert result["call_result"]["actual_count"] == 3

    def test_ones_are_wild(self):
        """Bid: 3x fours. Player 1 has [1,4,2], Player 2 has [1,3,5]. Ones are wild -> count = 1 four + 2 ones = 3. Bid met."""
        state_json = make_game_state(
            players_data=[
                {"id": 1, "dice": [1, 4, 2]},
                {"id": 2, "dice": [1, 3, 5]},
            ],
            current_bid={"quantity": 3, "face_value": 4, "bidder_id": 1},
        )
        result = run_engine("resolve_call", ["2"], stdin_data=state_json)
        assert result["call_result"]["actual_count"] == 3
        assert result["call_result"]["loser_id"] == 2

    def test_ones_not_wild_during_palifico(self):
        """Palifico round. Bid: 2x fours. Player 1 has [1,4], Player 2 has [1,4]. Ones NOT wild -> count = 2. Bid met."""
        state_json = make_game_state(
            players_data=[
                {"id": 1, "dice": [1, 4]},
                {"id": 2, "dice": [1, 4]},
            ],
            current_bid={"quantity": 2, "face_value": 4, "bidder_id": 1},
            palifico=True,
        )
        result = run_engine("resolve_call", ["2"], stdin_data=state_json)
        assert result["call_result"]["actual_count"] == 2

    def test_loser_has_fewer_dice_next_round(self):
        state_json = make_game_state(
            players_data=[
                {"id": 1, "dice": [2, 3, 4]},
                {"id": 2, "dice": [5, 6, 2]},
            ],
            current_bid={"quantity": 5, "face_value": 4, "bidder_id": 1},
        )
        result = run_engine("resolve_call", ["2"], stdin_data=state_json)
        loser_id = result["call_result"]["loser_id"]
        new_state = result["new_state"]
        loser = next(p for p in new_state["players"] if p["id"] == loser_id)
        assert loser["dice_count"] == 2
        assert len(loser["dice"]) == 2

    def test_player_eliminated_at_zero_dice(self):
        state_json = make_game_state(
            players_data=[
                {"id": 1, "dice": [2]},
                {"id": 2, "dice": [5, 6]},
            ],
            current_bid={"quantity": 2, "face_value": 2, "bidder_id": 1},
        )
        result = run_engine("resolve_call", ["2"], stdin_data=state_json)
        assert result["call_result"]["loser_id"] == 1
        loser = next(p for p in result["new_state"]["players"] if p["id"] == 1)
        assert loser["eliminated"] is True
        assert loser["dice_count"] == 0
        assert loser["dice"] == []

    def test_loser_starts_next_round(self):
        state_json = make_game_state(
            players_data=[
                {"id": 1, "dice": [2, 3, 4]},
                {"id": 2, "dice": [5, 6, 2]},
            ],
            current_bid={"quantity": 5, "face_value": 4, "bidder_id": 1},
        )
        result = run_engine("resolve_call", ["2"], stdin_data=state_json)
        loser_id = result["call_result"]["loser_id"]
        assert result["new_state"]["current_player_id"] == loser_id

    def test_eliminated_loser_next_active_player_starts(self):
        """If loser is eliminated, next active player starts."""
        state_json = make_game_state(
            players_data=[
                {"id": 1, "dice": [2]},
                {"id": 2, "dice": [5, 6]},
                {"id": 3, "dice": [3, 4]},
            ],
            current_bid={"quantity": 3, "face_value": 2, "bidder_id": 1},
        )
        result = run_engine("resolve_call", ["2"], stdin_data=state_json)
        assert result["call_result"]["loser_id"] == 1
        assert result["new_state"]["current_player_id"] == 2

    def test_palifico_triggered_when_reduced_to_one_die(self):
        state_json = make_game_state(
            players_data=[
                {"id": 1, "dice": [2, 3]},
                {"id": 2, "dice": [5, 6, 4]},
                {"id": 3, "dice": [1, 2, 3]},
            ],
            current_bid={"quantity": 4, "face_value": 2, "bidder_id": 1},
        )
        result = run_engine("resolve_call", ["2"], stdin_data=state_json)
        assert result["call_result"]["loser_id"] == 1
        assert result["new_state"]["palifico"] is True
        assert result["new_state"]["palifico_starter_id"] == 1

    def test_palifico_not_triggered_twice(self):
        state_json = make_game_state(
            players_data=[
                {"id": 1, "dice": [2, 3], "palifico_used": True},
                {"id": 2, "dice": [5, 6, 4]},
                {"id": 3, "dice": [1, 2, 3]},
            ],
            current_bid={"quantity": 4, "face_value": 2, "bidder_id": 1},
        )
        result = run_engine("resolve_call", ["2"], stdin_data=state_json)
        assert result["new_state"]["palifico"] is False

    def test_palifico_skipped_with_two_players(self):
        """With only 2 players, Palifico should not trigger even when a player drops to 1 die."""
        state_json = make_game_state(
            players_data=[
                {"id": 1, "dice": [2, 3]},
                {"id": 2, "dice": [5, 6, 4]},
            ],
            current_bid={"quantity": 4, "face_value": 2, "bidder_id": 1},
        )
        result = run_engine("resolve_call", ["2"], stdin_data=state_json)
        assert result["call_result"]["loser_id"] == 1
        loser = next(p for p in result["new_state"]["players"] if p["id"] == 1)
        assert loser["dice_count"] == 1
        assert result["new_state"]["palifico"] is False

    def test_game_over_when_one_player_left(self):
        state_json = make_game_state(
            players_data=[
                {"id": 1, "dice": [2]},
                {"id": 2, "dice": [5, 6]},
            ],
            current_bid={"quantity": 3, "face_value": 2, "bidder_id": 1},
        )
        result = run_engine("resolve_call", ["2"], stdin_data=state_json)
        assert result["new_state"]["phase"] == "game_over"

    def test_new_round_has_fresh_dice(self):
        state_json = make_game_state(
            players_data=[
                {"id": 1, "dice": [2, 3, 4]},
                {"id": 2, "dice": [5, 6, 2]},
            ],
            current_bid={"quantity": 5, "face_value": 4, "bidder_id": 1},
        )
        result = run_engine("resolve_call", ["2"], stdin_data=state_json)
        new_state = result["new_state"]
        assert new_state["current_bid"] is None
        assert new_state["bid_history"] == []
        assert new_state["round"] == 2

    def test_all_dice_revealed_in_result(self):
        state_json = make_game_state(
            players_data=[
                {"id": 1, "dice": [2, 3, 4]},
                {"id": 2, "dice": [5, 6, 2]},
            ],
            current_bid={"quantity": 5, "face_value": 4, "bidder_id": 1},
        )
        result = run_engine("resolve_call", ["2"], stdin_data=state_json)
        revealed = result["call_result"]["revealed_dice"]
        assert revealed[0]["id"] == 1
        assert revealed[0]["dice"] == [2, 3, 4]
        assert revealed[1]["id"] == 2
        assert revealed[1]["dice"] == [5, 6, 2]


class TestPlayerView:
    def test_own_dice_visible(self):
        state = run_engine("init", ["3", "--seed", "42"])
        state_json = json.dumps(state)
        view = run_engine("player_view", ["1"], stdin_data=state_json)
        assert view["you"]["dice"] == state["players"][0]["dice"]
        assert view["you"]["id"] == 1

    def test_other_dice_hidden(self):
        state = run_engine("init", ["3", "--seed", "42"])
        state_json = json.dumps(state)
        view = run_engine("player_view", ["1"], stdin_data=state_json)
        for opponent in view["opponents"]:
            assert "dice" not in opponent
            assert "dice_count" in opponent

    def test_opponents_have_names_and_counts(self):
        state = run_engine("init", ["3", "--seed", "42"])
        state_json = json.dumps(state)
        view = run_engine("player_view", ["2"], stdin_data=state_json)
        assert len(view["opponents"]) == 2
        names = {o["name"] for o in view["opponents"]}
        assert names == {"Agent-1", "Agent-3"}

    def test_includes_game_context(self):
        state = run_engine("init", ["2", "--seed", "42"])
        state_json = json.dumps(state)
        view = run_engine("player_view", ["1"], stdin_data=state_json)
        assert "round" in view
        assert "current_bid" in view
        assert "bid_history" in view
        assert "palifico" in view
        assert "total_dice" in view

    def test_eliminated_opponents_marked(self):
        state = run_engine("init", ["3", "--seed", "42"])
        state["players"][2]["eliminated"] = True
        state["players"][2]["dice_count"] = 0
        state["players"][2]["dice"] = []
        state_json = json.dumps(state)
        view = run_engine("player_view", ["1"], stdin_data=state_json)
        eliminated = [o for o in view["opponents"] if o["eliminated"]]
        assert len(eliminated) == 1
        assert eliminated[0]["name"] == "Agent-3"


class TestStatus:
    def test_shows_active_players(self):
        state = run_engine("init", ["3", "--seed", "42"])
        state_json = json.dumps(state)
        status = run_engine("status", stdin_data=state_json)
        assert len(status["active_players"]) == 3

    def test_shows_current_player(self):
        state = run_engine("init", ["3", "--seed", "42"])
        state_json = json.dumps(state)
        status = run_engine("status", stdin_data=state_json)
        assert status["current_player_id"] == 1

    def test_shows_dice_counts(self):
        state = run_engine("init", ["2", "--seed", "42"])
        state_json = json.dumps(state)
        status = run_engine("status", stdin_data=state_json)
        for p in status["active_players"]:
            assert p["dice_count"] == 5

    def test_shows_total_dice(self):
        state = run_engine("init", ["4", "--seed", "42"])
        state_json = json.dumps(state)
        status = run_engine("status", stdin_data=state_json)
        assert status["total_dice"] == 20


class TestApplyBid:
    def test_applies_bid_and_advances_player(self):
        state_json = make_state_with_bid(current_bid=None)
        result = run_engine("apply_bid", ["1", "3", "4"], stdin_data=state_json)
        new_state = result["new_state"]
        assert new_state["current_bid"]["quantity"] == 3
        assert new_state["current_bid"]["face_value"] == 4
        assert new_state["current_bid"]["bidder_id"] == 1
        assert new_state["current_player_id"] == 2

    def test_adds_to_bid_history(self):
        state_json = make_state_with_bid(current_bid=None)
        result = run_engine("apply_bid", ["1", "3", "4"], stdin_data=state_json)
        assert len(result["new_state"]["bid_history"]) == 1
        assert result["new_state"]["bid_history"][0]["player_id"] == 1
        assert result["new_state"]["bid_history"][0]["action"] == "bid"

    def test_rejects_invalid_bid(self):
        bid = {"quantity": 3, "face_value": 4, "bidder_id": 1}
        state_json = make_state_with_bid(current_bid=bid)
        result = run_engine("apply_bid", ["2", "2", "3"], stdin_data=state_json)
        assert result["valid"] is False

    def test_palifico_sets_locked_face_on_first_bid(self):
        state_json = make_state_with_bid(
            current_bid=None, palifico=True, palifico_starter_id=1,
        )
        result = run_engine("apply_bid", ["1", "2", "4"], stdin_data=state_json)
        assert result["new_state"]["palifico_locked_face"] == 4

    def test_palifico_face_unlocks_after_going_around(self):
        """When bid passes the Palifico starter, face lock should lift."""
        state = {
            "players": [
                {"id": 1, "name": "Agent-1", "dice_count": 1, "dice": [4], "eliminated": False, "palifico_used": True},
                {"id": 2, "name": "Agent-2", "dice_count": 3, "dice": [2, 4, 5], "eliminated": False, "palifico_used": False},
                {"id": 3, "name": "Agent-3", "dice_count": 3, "dice": [1, 3, 4], "eliminated": False, "palifico_used": False},
            ],
            "current_player_id": 3,
            "round": 2,
            "current_bid": {"quantity": 2, "face_value": 4, "bidder_id": 2},
            "bid_history": [
                {"player_id": 1, "action": "bid", "quantity": 1, "face_value": 4},
                {"player_id": 2, "action": "bid", "quantity": 2, "face_value": 4},
            ],
            "palifico": True,
            "palifico_starter_id": 1,
            "palifico_locked_face": 4,
            "palifico_face_unlocked": False,
            "phase": "awaiting_action",
            "total_dice": 7,
            "seed": None,
        }
        result = run_engine("apply_bid", ["3", "3", "4"], stdin_data=json.dumps(state))
        assert result["new_state"]["palifico_face_unlocked"] is True

    def test_skips_eliminated_players(self):
        state = {
            "players": [
                {"id": 1, "name": "Agent-1", "dice_count": 3, "dice": [2, 4, 5], "eliminated": False, "palifico_used": False},
                {"id": 2, "name": "Agent-2", "dice_count": 0, "dice": [], "eliminated": True, "palifico_used": False},
                {"id": 3, "name": "Agent-3", "dice_count": 3, "dice": [1, 3, 4], "eliminated": False, "palifico_used": False},
            ],
            "current_player_id": 1,
            "round": 1,
            "current_bid": None,
            "bid_history": [],
            "palifico": False,
            "palifico_starter_id": None,
            "palifico_locked_face": None,
            "palifico_face_unlocked": False,
            "phase": "awaiting_action",
            "total_dice": 6,
            "seed": None,
        }
        result = run_engine("apply_bid", ["1", "2", "3"], stdin_data=json.dumps(state))
        assert result["new_state"]["current_player_id"] == 3
