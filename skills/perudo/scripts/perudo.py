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


if __name__ == "__main__":
    main()
