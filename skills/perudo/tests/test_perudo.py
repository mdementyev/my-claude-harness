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
