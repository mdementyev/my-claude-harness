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
        # Can't open a regular round with ones
        if face_value == 1 and not state["palifico"]:
            return {"valid": False, "reason": "Cannot open a round with ones"}
        return {"valid": True, "reason": "First bid of round"}

    # Palifico face lock check
    if state["palifico"] and state["palifico_locked_face"] is not None and not state["palifico_face_unlocked"]:
        if face_value != state["palifico_locked_face"]:
            return {"valid": False, "reason": f"Palifico: face value locked to {state['palifico_locked_face']}, only raise quantity"}
        if quantity <= current_bid["quantity"]:
            return {"valid": False, "reason": f"Must bid higher quantity than {current_bid['quantity']}"}
        return {"valid": True, "reason": "Valid Palifico bid"}

    # Ones transition rules (only in non-Palifico rounds)
    cur_qty = current_bid["quantity"]
    cur_face = current_bid["face_value"]

    if cur_face != 1 and face_value == 1:
        # Transitioning TO ones: minimum quantity is ceil(cur_qty / 2)
        min_ones_qty = (cur_qty + 1) // 2
        if quantity >= min_ones_qty:
            return {"valid": True, "reason": f"Valid transition to ones (min {min_ones_qty})"}
        return {"valid": False, "reason": f"To bid ones, need at least {min_ones_qty} (ceil({cur_qty}/2))"}

    if cur_face == 1 and face_value != 1:
        # Transitioning FROM ones: minimum quantity is cur_qty * 2 + 1
        min_normal_qty = cur_qty * 2 + 1
        if quantity >= min_normal_qty:
            return {"valid": True, "reason": f"Valid transition from ones (min {min_normal_qty})"}
        return {"valid": False, "reason": f"From ones, need at least {min_normal_qty}x ({cur_qty}*2+1)"}

    # Same category (both ones, or both normal): standard ordering
    if quantity > cur_qty:
        return {"valid": True, "reason": "Higher quantity"}
    if quantity == cur_qty and face_value > cur_face:
        return {"valid": True, "reason": "Same quantity, higher face value"}

    return {"valid": False, "reason": f"Bid must be higher than {cur_qty}x {cur_face}s"}


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

    view_parser = subparsers.add_parser("player_view")
    view_parser.add_argument("player_id", type=int)

    subparsers.add_parser("status")

    apply_parser = subparsers.add_parser("apply_bid")
    apply_parser.add_argument("player_id", type=int)
    apply_parser.add_argument("quantity", type=int)
    apply_parser.add_argument("face_value", type=int)

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
    elif args.command == "apply_bid":
        state = read_state_from_stdin()
        result = apply_bid(state, args.player_id, args.quantity, args.face_value)
        json.dump(result, sys.stdout, indent=2)
        sys.stdout.write("\n")


if __name__ == "__main__":
    main()
