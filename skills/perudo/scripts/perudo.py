#!/usr/bin/env python3
"""Perudo (Liar's Dice) game engine. Deterministic, no AI logic."""

from __future__ import annotations

import argparse
import json
import random
import sys
from typing import List, Optional


def error_exit(message: str) -> None:
    """Print error JSON to stderr and exit with code 1."""
    json.dump({"error": message}, sys.stderr)
    sys.stderr.write("\n")
    sys.exit(1)


def roll_dice(count: int, rng: random.Random) -> List[int]:
    """Roll `count` dice, returning list of face values 1-6."""
    return [rng.randint(1, 6) for _ in range(count)]


def create_initial_state(player_count: int, seed: Optional[int] = None) -> dict:
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


def validate_bid(state, quantity, face_value):
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


def get_active_players(state: dict) -> list:
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

    # Apply die loss — use seed + round as RNG seed for each new round's dice
    round_seed = None
    if state.get("seed") is not None:
        round_seed = state["seed"] + state["round"] * 1000
    rng = random.Random(round_seed)

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

    validate_parser = subparsers.add_parser("validate_bid")
    validate_parser.add_argument("quantity", type=int)
    validate_parser.add_argument("face_value", type=int)

    resolve_parser = subparsers.add_parser("resolve_call")
    resolve_parser.add_argument("calling_player_id", type=int)

    args = parser.parse_args()

    if args.command == "init":
        state = create_initial_state(args.player_count, args.seed)
        json.dump(state, sys.stdout, indent=2)
        sys.stdout.write("\n")
    elif args.command == "validate_bid":
        state = read_state_from_stdin()
        result = validate_bid(state, args.quantity, args.face_value)
        json.dump(result, sys.stdout)
        sys.stdout.write("\n")
    elif args.command == "resolve_call":
        state = read_state_from_stdin()
        result = resolve_call(state, args.calling_player_id)
        json.dump(result, sys.stdout, indent=2)
        sys.stdout.write("\n")


if __name__ == "__main__":
    main()
