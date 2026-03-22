# Perudo Game Skill Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Claude Code skill that orchestrates Perudo (Liar's Dice) games between persistent AI agents, with the main session as oracle/narrator.

**Architecture:** Deterministic Python game engine (`perudo.py`) handles all mechanics via stdin/stdout JSON. SKILL.md provides oracle orchestration instructions and agent prompt templates. Persistent Agent subprocesses act as players.

**Tech Stack:** Python 3 (stdlib only), Claude Code skills (SKILL.md), Claude Code Agent/SendMessage

**Spec:** `docs/superpowers/specs/2026-03-22-perudo-game-skill-design.md`

---

### Task 1: Game State and Init Command

**Files:**
- Create: `skills/perudo/scripts/perudo.py`
- Create: `skills/perudo/tests/test_perudo.py`

Build the game state model and `init` command.

- [ ] **Step 1: Write failing test for init**

```python
# skills/perudo/tests/test_perudo.py
import json
import subprocess
import sys
from pathlib import Path

SCRIPT = str(Path(__file__).resolve().parent.parent / "scripts" / "perudo.py")


def run_engine(command: str, args: list[str] | None = None, stdin_data: str | None = None) -> dict:
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/mike.dementyev/Projects/my-claude-harness && python3 -m pytest skills/perudo/tests/test_perudo.py::TestInit -v`
Expected: FAIL (script doesn't exist yet)

- [ ] **Step 3: Implement init command**

```python
# skills/perudo/scripts/perudo.py
#!/usr/bin/env python3
"""Perudo (Liar's Dice) game engine. Deterministic, no AI logic."""

import argparse
import json
import random
import sys


def error_exit(message: str) -> None:
    """Print error JSON to stderr and exit with code 1."""
    json.dump({"error": message}, sys.stderr)
    sys.stderr.write("\n")
    sys.exit(1)


def roll_dice(count: int, rng: random.Random) -> list[int]:
    """Roll `count` dice, returning list of face values 1-6."""
    return [rng.randint(1, 6) for _ in range(count)]


def create_initial_state(player_count: int, seed: int | None = None) -> dict:
    """Create a fresh game state with all players having 5 dice."""
    if not 2 <= player_count <= 6:
        error_exit(f"Player count must be 2-6, got {player_count}")

    rng = random.Random(seed)
    players = []
    for i in range(1, player_count + 1):
        players.append({
            "id": i,
            "name": f"Agent-{i}",
            "dice_count": 5,
            "dice": roll_dice(5, rng),
            "eliminated": False,
            "palifico_used": False,
        })

    return {
        "players": players,
        "current_player_id": 1,
        "round": 1,
        "current_bid": None,
        "bid_history": [],
        "palifico": False,
        "palifico_starter_id": None,
        "palifico_locked_face": None,
        "palifico_face_unlocked": False,
        "phase": "awaiting_action",
        "total_dice": player_count * 5,
        "seed": seed,
    }


def read_state_from_stdin() -> dict:
    """Read and parse JSON game state from stdin."""
    data = sys.stdin.read().strip()
    if not data:
        error_exit("No state provided on stdin")
    try:
        return json.loads(data)
    except json.JSONDecodeError as e:
        error_exit(f"Invalid JSON on stdin: {e}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Perudo game engine")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init")
    init_parser.add_argument("player_count", type=int)
    init_parser.add_argument("--seed", type=int, default=None)

    args = parser.parse_args()

    if args.command == "init":
        state = create_initial_state(args.player_count, args.seed)
        json.dump(state, sys.stdout, indent=2)
        sys.stdout.write("\n")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/mike.dementyev/Projects/my-claude-harness && python3 -m pytest skills/perudo/tests/test_perudo.py::TestInit -v`
Expected: All PASS

- [ ] **Step 5: Commit**

```bash
git add skills/perudo/scripts/perudo.py skills/perudo/tests/test_perudo.py
git commit -m "feat(perudo): add game engine with init command"
```

---

### Task 2: Bid Validation

**Files:**
- Modify: `skills/perudo/scripts/perudo.py`
- Modify: `skills/perudo/tests/test_perudo.py`

Add `validate_bid` command that reads state from stdin and checks if a bid is legal.

- [ ] **Step 1: Write failing tests for validate_bid**

```python
# Add to skills/perudo/tests/test_perudo.py

def make_state_with_bid(current_bid: dict | None = None, palifico: bool = False,
                        palifico_locked_face: int | None = None,
                        palifico_face_unlocked: bool = False,
                        palifico_starter_id: int | None = None) -> str:
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/mike.dementyev/Projects/my-claude-harness && python3 -m pytest skills/perudo/tests/test_perudo.py::TestValidateBid -v`
Expected: FAIL

- [ ] **Step 3: Implement validate_bid**

Add to `perudo.py`:

```python
def validate_bid(state: dict, quantity: int, face_value: int) -> dict:
    """Check if a bid is legal given current state. Returns {"valid": bool, "reason": str}."""
    if quantity < 1:
        return {"valid": False, "reason": "Quantity must be at least 1"}
    if not 1 <= face_value <= 6:
        return {"valid": False, "reason": "Face value must be 1-6"}

    current_bid = state["current_bid"]
    if current_bid is None:
        return {"valid": True, "reason": "First bid of round"}

    # Palifico face lock check
    if state["palifico"] and state["palifico_locked_face"] is not None and not state["palifico_face_unlocked"]:
        if face_value != state["palifico_locked_face"]:
            return {"valid": False, "reason": f"Palifico: face value locked to {state['palifico_locked_face']}, only raise quantity"}
        if quantity <= current_bid["quantity"]:
            return {"valid": False, "reason": f"Must bid higher quantity than {current_bid['quantity']}"}
        return {"valid": True, "reason": "Valid Palifico bid"}

    # Normal bid ordering
    if quantity > current_bid["quantity"]:
        return {"valid": True, "reason": "Higher quantity"}
    if quantity == current_bid["quantity"] and face_value > current_bid["face_value"]:
        return {"valid": True, "reason": "Same quantity, higher face value"}

    return {"valid": False, "reason": f"Bid must be higher than {current_bid['quantity']}x {current_bid['face_value']}s"}
```

Add the `validate_bid` subcommand to `main()`:

```python
    validate_parser = subparsers.add_parser("validate_bid")
    validate_parser.add_argument("quantity", type=int)
    validate_parser.add_argument("face_value", type=int)
```

And the handler:

```python
    elif args.command == "validate_bid":
        state = read_state_from_stdin()
        result = validate_bid(state, args.quantity, args.face_value)
        json.dump(result, sys.stdout)
        sys.stdout.write("\n")
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/mike.dementyev/Projects/my-claude-harness && python3 -m pytest skills/perudo/tests/test_perudo.py::TestValidateBid -v`
Expected: All PASS

- [ ] **Step 5: Commit**

```bash
git add skills/perudo/scripts/perudo.py skills/perudo/tests/test_perudo.py
git commit -m "feat(perudo): add bid validation with Palifico support"
```

---

### Task 3: Resolve Call (Round Resolution)

**Files:**
- Modify: `skills/perudo/scripts/perudo.py`
- Modify: `skills/perudo/tests/test_perudo.py`

Add `resolve_call` command. This is the most complex piece — count dice, determine winner/loser, remove die, detect elimination, detect Palifico, re-roll, set next round starter.

- [ ] **Step 1: Write failing tests for resolve_call**

```python
# Add to skills/perudo/tests/test_perudo.py

def make_game_state(players_data: list[dict], current_bid: dict,
                    palifico: bool = False, round_num: int = 1,
                    seed: int | None = 42) -> str:
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
        """Bid: 3x fours. Player 1 has [4,4,2], Player 2 has [4,3,5]. Total fours = 3. Bid met → caller loses."""
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
        """Bid: 4x fours. Player 1 has [4,4,2], Player 2 has [4,3,5]. Total fours = 3. Not met → bidder loses."""
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
        """Bid: 3x fours. Player 1 has [1,4,2], Player 2 has [1,3,5]. Ones are wild → count = 2 fours + 2 ones = 4. Bid met."""
        state_json = make_game_state(
            players_data=[
                {"id": 1, "dice": [1, 4, 2]},
                {"id": 2, "dice": [1, 3, 5]},
            ],
            current_bid={"quantity": 3, "face_value": 4, "bidder_id": 1},
        )
        result = run_engine("resolve_call", ["2"], stdin_data=state_json)
        assert result["call_result"]["actual_count"] == 4
        assert result["call_result"]["loser_id"] == 2

    def test_ones_not_wild_during_palifico(self):
        """Palifico round. Bid: 2x fours. Player 1 has [1,4], Player 2 has [1,4]. Ones NOT wild → count = 2. Bid met."""
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
        # Bidder claimed 2x twos but only 1 exists → bidder (1) loses
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
                {"id": 1, "dice": [2]},  # will lose and be eliminated
                {"id": 2, "dice": [5, 6]},
                {"id": 3, "dice": [3, 4]},
            ],
            current_bid={"quantity": 3, "face_value": 2, "bidder_id": 1},
        )
        result = run_engine("resolve_call", ["2"], stdin_data=state_json)
        assert result["call_result"]["loser_id"] == 1
        assert result["new_state"]["current_player_id"] == 2  # next active after 1

    def test_palifico_triggered_when_reduced_to_one_die(self):
        state_json = make_game_state(
            players_data=[
                {"id": 1, "dice": [2, 3]},  # will lose 1 die → 1 die → palifico
                {"id": 2, "dice": [5, 6, 4]},
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
            ],
            current_bid={"quantity": 4, "face_value": 2, "bidder_id": 1},
        )
        result = run_engine("resolve_call", ["2"], stdin_data=state_json)
        assert result["new_state"]["palifico"] is False

    def test_palifico_skipped_with_two_players(self):
        state_json = make_game_state(
            players_data=[
                {"id": 1, "dice": [2, 3]},
                {"id": 2, "dice": [5, 6, 4]},
            ],
            current_bid={"quantity": 4, "face_value": 2, "bidder_id": 1},
        )
        result = run_engine("resolve_call", ["2"], stdin_data=state_json)
        # Only 2 active players → no palifico even though player goes to 1 die
        active_count = sum(1 for p in result["new_state"]["players"] if not p["eliminated"])
        if active_count == 2:
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/mike.dementyev/Projects/my-claude-harness && python3 -m pytest skills/perudo/tests/test_perudo.py::TestResolveCall -v`
Expected: FAIL

- [ ] **Step 3: Implement resolve_call**

Add to `perudo.py`:

```python
def count_matching_dice(state: dict, face_value: int) -> int:
    """Count total dice matching face_value across all active players. Ones are wild unless Palifico."""
    count = 0
    for player in state["players"]:
        if player["eliminated"]:
            continue
        for die in player["dice"]:
            if die == face_value:
                count += 1
            elif die == 1 and not state["palifico"] and face_value != 1:
                count += 1
    return count


def get_active_players(state: dict) -> list[dict]:
    """Return non-eliminated players in order."""
    return [p for p in state["players"] if not p["eliminated"]]


def next_active_player_after(state: dict, player_id: int) -> int:
    """Find next non-eliminated player after given player_id, wrapping around."""
    active = get_active_players(state)
    ids = [p["id"] for p in active]
    if player_id in ids:
        idx = ids.index(player_id)
        return ids[(idx + 1) % len(ids)]
    # player_id is eliminated, find next active after their position
    all_ids = [p["id"] for p in state["players"]]
    pos = all_ids.index(player_id)
    for i in range(1, len(all_ids) + 1):
        candidate = all_ids[(pos + i) % len(all_ids)]
        if candidate in ids:
            return candidate
    return ids[0]


def resolve_call(state: dict, calling_player_id: int) -> dict:
    """Resolve a Dudo call. Returns call result and new game state."""
    current_bid = state["current_bid"]
    if current_bid is None:
        error_exit("Cannot call on first bid of round")

    bidder_id = current_bid["bidder_id"]
    bid_quantity = current_bid["quantity"]
    bid_face = current_bid["face_value"]

    actual_count = count_matching_dice(state, bid_face)

    # Reveal all dice
    revealed_dice = [
        {"id": p["id"], "name": p["name"], "dice": p["dice"]}
        for p in state["players"] if not p["eliminated"]
    ]

    # Determine loser
    if actual_count >= bid_quantity:
        loser_id = calling_player_id  # bid was met, caller loses
    else:
        loser_id = bidder_id  # bid was not met, bidder loses

    # Apply die loss
    rng = random.Random(state.get("seed"))
    # Advance RNG past initial rolls to avoid repeating dice
    for p in state["players"]:
        for _ in range(p["dice_count"]):
            rng.randint(1, 6)
    # Advance more based on round to ensure different dice each round
    for _ in range(state["round"] * 100):
        rng.randint(1, 6)

    new_players = []
    for player in state["players"]:
        p = dict(player)
        if p["id"] == loser_id and not p["eliminated"]:
            p["dice_count"] -= 1
            if p["dice_count"] <= 0:
                p["dice_count"] = 0
                p["dice"] = []
                p["eliminated"] = True
            else:
                p["dice"] = roll_dice(p["dice_count"], rng)
        elif not p["eliminated"]:
            p["dice"] = roll_dice(p["dice_count"], rng)
        new_players.append(p)

    active_players = [p for p in new_players if not p["eliminated"]]
    total_dice = sum(p["dice_count"] for p in active_players)

    # Check game over
    if len(active_players) <= 1:
        winner_id = active_players[0]["id"] if active_players else None
        new_state = {
            **state,
            "players": new_players,
            "current_bid": None,
            "bid_history": [],
            "round": state["round"] + 1,
            "phase": "game_over",
            "total_dice": total_dice,
            "palifico": False,
            "palifico_starter_id": None,
            "palifico_locked_face": None,
            "palifico_face_unlocked": False,
        }
        return {
            "call_result": {
                "caller_id": calling_player_id,
                "bidder_id": bidder_id,
                "bid": current_bid,
                "actual_count": actual_count,
                "loser_id": loser_id,
                "revealed_dice": revealed_dice,
                "winner_id": winner_id,
            },
            "new_state": new_state,
        }

    # Determine next round starter
    loser_player = next(p for p in new_players if p["id"] == loser_id)
    if loser_player["eliminated"]:
        starter_id = next_active_player_after({"players": new_players}, loser_id)
    else:
        starter_id = loser_id

    # Check Palifico
    palifico = False
    palifico_starter_id = None
    if len(active_players) > 2:  # skip Palifico with 2 players
        loser_p = next(p for p in new_players if p["id"] == loser_id)
        if loser_p["dice_count"] == 1 and not loser_p["palifico_used"]:
            palifico = True
            palifico_starter_id = loser_id
            loser_p["palifico_used"] = True
            starter_id = loser_id  # Palifico player starts

    new_state = {
        **state,
        "players": new_players,
        "current_player_id": starter_id,
        "current_bid": None,
        "bid_history": [],
        "round": state["round"] + 1,
        "phase": "awaiting_action",
        "total_dice": total_dice,
        "palifico": palifico,
        "palifico_starter_id": palifico_starter_id,
        "palifico_locked_face": None,
        "palifico_face_unlocked": False,
    }

    return {
        "call_result": {
            "caller_id": calling_player_id,
            "bidder_id": bidder_id,
            "bid": current_bid,
            "actual_count": actual_count,
            "loser_id": loser_id,
            "revealed_dice": revealed_dice,
        },
        "new_state": new_state,
    }
```

Add the subcommand to `main()`:

```python
    resolve_parser = subparsers.add_parser("resolve_call")
    resolve_parser.add_argument("calling_player_id", type=int)
```

And the handler:

```python
    elif args.command == "resolve_call":
        state = read_state_from_stdin()
        result = resolve_call(state, args.calling_player_id)
        json.dump(result, sys.stdout, indent=2)
        sys.stdout.write("\n")
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/mike.dementyev/Projects/my-claude-harness && python3 -m pytest skills/perudo/tests/test_perudo.py::TestResolveCall -v`
Expected: All PASS

- [ ] **Step 5: Commit**

```bash
git add skills/perudo/scripts/perudo.py skills/perudo/tests/test_perudo.py
git commit -m "feat(perudo): add call resolution with Palifico and elimination"
```

---

### Task 4: Player View and Status Commands

**Files:**
- Modify: `skills/perudo/scripts/perudo.py`
- Modify: `skills/perudo/tests/test_perudo.py`

Add `player_view` (hides other players' dice) and `status` commands.

- [ ] **Step 1: Write failing tests**

```python
# Add to skills/perudo/tests/test_perudo.py

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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/mike.dementyev/Projects/my-claude-harness && python3 -m pytest skills/perudo/tests/test_perudo.py::TestPlayerView skills/perudo/tests/test_perudo.py::TestStatus -v`
Expected: FAIL

- [ ] **Step 3: Implement player_view and status**

Add to `perudo.py`:

```python
def player_view(state: dict, player_id: int) -> dict:
    """Return game state from one player's perspective. Own dice visible, others hidden."""
    me = None
    opponents = []
    for player in state["players"]:
        if player["id"] == player_id:
            me = {
                "id": player["id"],
                "name": player["name"],
                "dice_count": player["dice_count"],
                "dice": player["dice"],
            }
        else:
            opp = {
                "id": player["id"],
                "name": player["name"],
                "dice_count": player["dice_count"],
                "eliminated": player["eliminated"],
            }
            opponents.append(opp)

    if me is None:
        error_exit(f"Player {player_id} not found")

    return {
        "you": me,
        "opponents": opponents,
        "round": state["round"],
        "current_bid": state["current_bid"],
        "bid_history": state["bid_history"],
        "palifico": state["palifico"],
        "total_dice": state["total_dice"],
        "current_player_id": state["current_player_id"],
    }


def status(state: dict) -> dict:
    """Return summary of active players, dice counts, whose turn."""
    active = [
        {"id": p["id"], "name": p["name"], "dice_count": p["dice_count"]}
        for p in state["players"] if not p["eliminated"]
    ]
    return {
        "active_players": active,
        "current_player_id": state["current_player_id"],
        "round": state["round"],
        "total_dice": state["total_dice"],
        "phase": state["phase"],
    }
```

Add subcommands and handlers to `main()`:

```python
    subparsers.add_parser("player_view").add_argument("player_id", type=int)
    subparsers.add_parser("status")
```

Handlers:

```python
    elif args.command == "player_view":
        state = read_state_from_stdin()
        result = player_view(state, args.player_id)
        json.dump(result, sys.stdout, indent=2)
        sys.stdout.write("\n")
    elif args.command == "status":
        state = read_state_from_stdin()
        result = status(state)
        json.dump(result, sys.stdout, indent=2)
        sys.stdout.write("\n")
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/mike.dementyev/Projects/my-claude-harness && python3 -m pytest skills/perudo/tests/test_perudo.py::TestPlayerView skills/perudo/tests/test_perudo.py::TestStatus -v`
Expected: All PASS

- [ ] **Step 5: Commit**

```bash
git add skills/perudo/scripts/perudo.py skills/perudo/tests/test_perudo.py
git commit -m "feat(perudo): add player_view and status commands"
```

---

### Task 5: Apply Bid Command

**Files:**
- Modify: `skills/perudo/scripts/perudo.py`
- Modify: `skills/perudo/tests/test_perudo.py`

Add `apply_bid` command — validates and applies a bid to the game state (adds to bid history, advances current player, updates Palifico face lock). The oracle needs this to advance state after a valid bid without calling `resolve_call`.

- [ ] **Step 1: Write failing tests**

```python
# Add to skills/perudo/tests/test_perudo.py

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
        # 3-player game, palifico starter is player 1, locked face is 4
        # Player 2 bids, player 3 bids, now it's player 1's turn again
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
        # Player 3 bids — next player is 1 (the starter), so face lock lifts
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
        assert result["new_state"]["current_player_id"] == 3  # skips eliminated player 2
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/mike.dementyev/Projects/my-claude-harness && python3 -m pytest skills/perudo/tests/test_perudo.py::TestApplyBid -v`
Expected: FAIL

- [ ] **Step 3: Implement apply_bid**

Add to `perudo.py`:

```python
def apply_bid(state: dict, player_id: int, quantity: int, face_value: int) -> dict:
    """Validate and apply a bid. Returns validation result and new state if valid."""
    validation = validate_bid(state, quantity, face_value)
    if not validation["valid"]:
        return validation

    new_state = {**state}
    new_state["current_bid"] = {
        "quantity": quantity,
        "face_value": face_value,
        "bidder_id": player_id,
    }
    new_state["bid_history"] = state["bid_history"] + [
        {"player_id": player_id, "action": "bid", "quantity": quantity, "face_value": face_value}
    ]

    # Set Palifico locked face on first bid
    if state["palifico"] and state["palifico_locked_face"] is None:
        new_state["palifico_locked_face"] = face_value

    # Advance to next active player
    next_id = next_active_player_after(state, player_id)
    new_state["current_player_id"] = next_id

    # Check if face lock should lift (next player is the Palifico starter)
    if state["palifico"] and not state["palifico_face_unlocked"]:
        if next_id == state["palifico_starter_id"]:
            new_state["palifico_face_unlocked"] = True

    return {"valid": True, "new_state": new_state}
```

Add subcommand and handler to `main()`:

```python
    apply_parser = subparsers.add_parser("apply_bid")
    apply_parser.add_argument("player_id", type=int)
    apply_parser.add_argument("quantity", type=int)
    apply_parser.add_argument("face_value", type=int)
```

Handler:

```python
    elif args.command == "apply_bid":
        state = read_state_from_stdin()
        result = apply_bid(state, args.player_id, args.quantity, args.face_value)
        json.dump(result, sys.stdout, indent=2)
        sys.stdout.write("\n")
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/mike.dementyev/Projects/my-claude-harness && python3 -m pytest skills/perudo/tests/test_perudo.py::TestApplyBid -v`
Expected: All PASS

- [ ] **Step 5: Run ALL tests to verify nothing broke**

Run: `cd /Users/mike.dementyev/Projects/my-claude-harness && python3 -m pytest skills/perudo/tests/test_perudo.py -v`
Expected: All PASS

- [ ] **Step 6: Commit**

```bash
git add skills/perudo/scripts/perudo.py skills/perudo/tests/test_perudo.py
git commit -m "feat(perudo): add apply_bid command with Palifico face lock"
```

---

### Task 6: Write SKILL.md (Oracle Skill)

**Files:**
- Create: `skills/perudo/SKILL.md`

Write the oracle orchestration skill that instructs the main Claude session how to run the game.

- [ ] **Step 1: Write SKILL.md**

The SKILL.md should contain:
- YAML frontmatter with `name: perudo`, `description`, `user-invocable: true`
- Complete Perudo rules (from spec)
- Agent base prompt template (rules, secret playstyle instruction, mental model instruction, response format)
- Oracle orchestration protocol:
  - Game startup sequence (ask player count, init, spawn agents, narrate intro)
  - Turn loop (player_view → SendMessage → validate/apply → narrate → next)
  - Round resolution flow (resolve_call → narrate reveal → check elimination → next round)
  - Error handling (invalid bids, max 3 retries then forced call)
- Narration guidelines (dramatic poker-broadcast style, paraphrase reasoning)
- Engine CLI reference (all commands with stdin/stdout patterns)
- The script path: use `SKILL_DIR` to reference `scripts/perudo.py` relative to the skill directory

Key details for the SKILL.md:
- The agent prompt template must instruct agents to choose a secret playstyle and never reveal it
- The agent prompt must instruct agents to build mental models of opponents from observed behavior
- The oracle must use `echo '<state>' | python3 "$SKILL_DIR/scripts/perudo.py" <command> [args]` pattern
- Agents respond with JSON: `{"action": "bid"|"call", "quantity": N, "face_value": N, "reasoning": "..."}`
- The oracle paraphrases agent reasoning in narration — agents never see each other's reasoning

- [ ] **Step 2: Verify skill file has valid YAML frontmatter**

Run: `cd /Users/mike.dementyev/Projects/my-claude-harness && python3 -c "import yaml; yaml.safe_load(open('skills/perudo/SKILL.md').read().split('---')[1])"`
Expected: No error (valid YAML)

- [ ] **Step 3: Commit**

```bash
git add skills/perudo/SKILL.md
git commit -m "feat(perudo): add oracle orchestration skill"
```

---

### Task 7: Install and Smoke Test

**Files:**
- None modified (verification only)

- [ ] **Step 1: Run install.sh**

Run: `cd /Users/mike.dementyev/Projects/my-claude-harness && ./install.sh`
Expected: Output includes `linking: perudo` or `ok: perudo`

- [ ] **Step 2: Verify symlink**

Run: `ls -la ~/.claude/skills/perudo`
Expected: Symlink pointing to repo's `skills/perudo/`

- [ ] **Step 3: Run full test suite**

Run: `cd /Users/mike.dementyev/Projects/my-claude-harness && python3 -m pytest skills/perudo/tests/test_perudo.py -v`
Expected: All tests PASS

- [ ] **Step 4: Smoke test each engine command manually**

```bash
cd /Users/mike.dementyev/Projects/my-claude-harness

# Init
python3 skills/perudo/scripts/perudo.py init 3 --seed 42

# Player view (pipe init output)
python3 skills/perudo/scripts/perudo.py init 3 --seed 42 | python3 skills/perudo/scripts/perudo.py player_view 1

# Status
python3 skills/perudo/scripts/perudo.py init 3 --seed 42 | python3 skills/perudo/scripts/perudo.py status

# Validate bid
python3 skills/perudo/scripts/perudo.py init 3 --seed 42 | python3 skills/perudo/scripts/perudo.py validate_bid 2 4

# Apply bid
python3 skills/perudo/scripts/perudo.py init 3 --seed 42 | python3 skills/perudo/scripts/perudo.py apply_bid 1 2 4
```

Expected: All produce valid JSON output, no errors

- [ ] **Step 5: Commit any fixes if needed**
