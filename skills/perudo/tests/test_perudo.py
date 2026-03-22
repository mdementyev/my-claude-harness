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
