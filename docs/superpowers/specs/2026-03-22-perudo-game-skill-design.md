# Perudo Game Skill Design

## Overview

A Claude Code skill that runs a full game of Perudo (Liar's Dice) with AI agents as players. The main Claude session acts as an oracle/game master, while separate persistent Agent subprocesses act as players. The human watches an AI-vs-AI game with dramatic narration.

### Goals

- **Entertainment/demo**: showcase Claude's multi-agent capabilities through a bluffing dice game
- **AI research**: study how LLM agents handle imperfect information, bluffing, and probabilistic reasoning

### Non-goals

- Human participation as a player (AI-only, human watches)
- Exact call ("Calza") rule — not used in the user's house rules

## Architecture

Three components:

### 1. `skills/perudo/SKILL.md` — Oracle Skill

The orchestration brain. Contains:
- Complete Perudo rules
- Oracle turn loop protocol
- Agent base prompt template
- Narration guidelines
- Agent response format spec
- Error handling (invalid bids, retries)

### 2. `skills/perudo/scripts/perudo.py` — Game Engine

Deterministic script called via Bash. Handles all game mechanics so the LLM never does arithmetic or rule validation. No AI logic — purely deterministic. Python 3, stdlib only — no third-party dependencies.

**CLI interface (all state passed via stdin, results via stdout):**

- `echo '<state>' | python3 perudo.py validate_bid <quantity> <face_value>` — check if bid is legal
- `echo '<state>' | python3 perudo.py apply_bid <player_id> <quantity> <face_value>` — validate and apply a bid: updates current_bid, bid_history, advances current_player, handles Palifico face lock/unlock. Returns validation result and new state.
- `echo '<state>' | python3 perudo.py resolve_call <calling_player_id>` — count dice, determine winner/loser, remove die, re-roll, advance round
- `echo '<state>' | python3 perudo.py player_view <player_id>` — return state from one player's perspective (own dice visible, others hidden)
- `echo '<state>' | python3 perudo.py status` — return active players, dice counts, whose turn

Only `init` takes no stdin (it creates fresh state):
- `python3 perudo.py init <player_count> [--seed N]` — create game state, roll dice for all players. Optional seed for reproducibility.

All output is JSON to stdout. Errors are JSON to stderr with non-zero exit code.

### 3. Persistent Agent Subprocesses — Players

One Claude Code Agent subprocess per player, spawned at game start and communicated with via `SendMessage` throughout the game. These are Claude Code's built-in Agent tool and SendMessage capability.

## Game Rules (Standard Perudo, no Calza)

- Each player starts with 5 dice
- All players roll secretly at the start of each round
- Players bid on total quantity of a face value across ALL players' dice
- Ones (aces) are wild — they count as any face value
- A bid must be higher than the previous: higher quantity, or same quantity with higher face value
- Players take turns in strict sequential order (by player ID, skipping eliminated players). On their turn, a player either raises the bid or calls "Dudo" (liar) on the previous bidder
- The first bid of a round has no minimum — any valid quantity (≥1) and face value (2-6) is legal. Cannot open a regular round with ones.
- On a call: all dice are revealed. If the bid is met or exceeded, the caller loses a die. If not met, the bidder loses a die
- A player is eliminated when they lose all dice
- Last player standing wins

### Round Start

- **First round**: Player 1 starts
- **Subsequent rounds**: the loser of the previous challenge starts. If eliminated, the next active player in order starts
- At round start, `current_bid` is null — the starting player makes the first bid

### Palifico

- When a player is reduced to exactly 1 die, the next round is a Palifico round
- Palifico triggers only once per player (tracked per-player in game state). Since a player at 1 die either stays at 1 or is eliminated, re-triggering is impossible by game mechanics, but the engine tracks it explicitly for correctness
- During Palifico: ones are NOT wild
- The Palifico player starts the round and picks any face value with their first bid
- Subsequent players can only raise the quantity; the face value is locked
- After the bid goes all the way around past the Palifico starter, the face value lock lifts and normal bidding rules resume (but ones remain non-wild for the rest of the round)
- **Two-player Palifico**: Palifico is skipped when only 2 players remain (follows standard tournament rules)

### Bid Ordering

- A bid is higher if quantity is greater
- If quantity is equal, face value must be greater
- **Ones transition:** since ones are wild, they follow special conversion:
  - Moving TO ones from a normal face (2-6): minimum ones quantity is ceil(current_quantity / 2)
  - Moving FROM ones to a normal face (2-6): minimum quantity is current_ones_quantity * 2 + 1
  - These transitions don't apply during Palifico rounds (ones aren't wild in Palifico)
- During Palifico (while face value is locked): only quantity can increase

## Game State

Managed entirely by `perudo.py` as JSON. The oracle never modifies state directly.

```json
{
  "players": [
    {
      "id": 1,
      "name": "Agent-1",
      "dice_count": 5,
      "dice": [2, 3, 5, 1, 4],
      "eliminated": false,
      "palifico_used": false
    }
  ],
  "current_player_id": 1,
  "round": 3,
  "current_bid": {"quantity": 4, "face_value": 3, "bidder_id": 2},
  "bid_history": [
    {"player_id": 1, "action": "bid", "quantity": 3, "face_value": 2},
    {"player_id": 2, "action": "bid", "quantity": 4, "face_value": 3}
  ],
  "palifico": false,
  "palifico_starter_id": null,
  "palifico_locked_face": null,
  "palifico_face_unlocked": false,
  "phase": "awaiting_action",
  "total_dice": 10,
  "seed": null
}
```

Key fields:
- `current_bid.bidder_id` — tracks who made the last bid (used by `resolve_call` to determine who loses a die)
- `palifico_starter_id` — who triggered the Palifico round
- `palifico_locked_face` — the face value locked during Palifico
- `palifico_face_unlocked` — becomes true after bidding passes the Palifico starter, lifting the face lock
- `palifico_used` (per player) — prevents a player from triggering Palifico twice
- `total_dice` — convenience field, sum of all active players' dice counts

## Agent Design

### Prompt

Each agent receives an identical base prompt. No personality is assigned by the oracle. The prompt includes:
- Perudo rules (bidding, calling, wilds, Palifico)
- Instruction to secretly choose a playstyle at game start and never reveal it
- Instruction to build mental models of opponents based on observed behavior
- Response format requirements
- The agent's player ID and name

### Information Visibility

Agents see (via `player_view`) only when it is their turn:
- Their own dice values
- Number of dice each opponent has (not values)
- Full bid history for the current round
- Whether this is a Palifico round
- After each round: revealed dice from the resolution (all players' dice shown), included in the next turn message

Agents never see:
- Other players' dice during a round
- Other players' reasoning
- Other players' chosen playstyles

Agents do NOT receive bid-by-bid broadcasts between turns. They see the full bid history when it becomes their turn, which is simpler and sufficient.

### Response Format

```json
{"action": "bid", "quantity": 5, "face_value": 3, "reasoning": "..."}
```
or
```json
{"action": "call", "reasoning": "..."}
```

The `reasoning` field is paraphrased by the oracle in narration. Agents don't see each other's reasoning.

### Invalid Action Handling

If an agent returns an invalid bid (not higher than current, bad format), the oracle tells the agent why it's invalid and asks for a new action. Max 3 retries before the agent is forced to call.

### Mental Model Building

After each round resolution, all agents see the revealed dice (delivered in their next turn message). Over multiple rounds, agents accumulate evidence about who bluffs, who plays tight, who targets specific players. This happens naturally through the persistent conversation context — no explicit memory mechanism needed.

## Oracle Orchestration

### Game Startup

1. User triggers skill (e.g., "let's play perudo")
2. Oracle asks how many players (2-6)
3. Oracle calls `python3 perudo.py init <count>`
4. Oracle spawns N persistent agents with the base prompt
5. Oracle sends each agent their initial `player_view` (so they see their first dice)
6. Oracle narrates: introduces the players, sets the scene

### Turn Loop

1. Determine whose turn from game state (`current_player_id`)
2. Call `player_view` for active player, send via `SendMessage` to that agent
3. Agent responds with action
4. Oracle calls `validate_bid` or `resolve_call` on `perudo.py` via stdin
5. If invalid → tell agent why, retry (max 3 retries then forced call)
6. If valid bid → narrate the bid, advance to next player
7. If call → narrate dramatic reveal, show all dice, announce who loses a die, check elimination
8. At round end → engine re-rolls for new round, oracle sends fresh `player_view` to next active player (plus round resolution summary)
9. Repeat until one player remains

### Narration Style

- Dramatic, engaging commentary — like a poker broadcast
- Include agent reasoning in narration (paraphrased, not raw JSON)
- Call out interesting moments: bold bluffs, narrow escapes, Palifico tension
- Brief summary after each round: who's in, dice counts, momentum
- At game end: crown the winner, recap memorable moments

### Pacing

The game runs autonomously — no human input during play. The human watches narration scroll by.

### Context Window Management

With many players and long games, the oracle's context will grow. For v1, this is accepted as a known limitation — games with 6 players may hit context limits in very long games. The oracle should keep narration concise enough to avoid premature exhaustion. Claude Code's automatic context compression will help.

## File Structure

```
skills/perudo/
├── SKILL.md
├── scripts/
│   └── perudo.py
└── tests/
    └── test_perudo.py
```

Installed to `~/.claude/skills/perudo/` via the existing `install.sh` symlink mechanism.

## Configuration

- Number of players: 2-6, chosen by user at game start
- Optional random seed: for reproducible games (useful for research/debugging)
- Agent model: inherits from parent session (no override needed)
- No other configuration — playstyles are agent-chosen, rules are fixed

## Testing

`tests/test_perudo.py` — comprehensive unit tests for `perudo.py` covering:
- Dice rolling (correct count, valid face values 1-6, seeded reproducibility)
- Bid validation (ordering, first-bid-of-round with null current_bid, Palifico face lock, Palifico unlock after going around)
- Round resolution (wild ones counting, Palifico no-wilds, correct loser determination)
- Round start player selection (loser starts, eliminated player skipped)
- Player elimination (zero dice = eliminated, last player wins)
- Palifico triggering (once per player, skipped with 2 players)
- `player_view` information hiding (own dice visible, others hidden)
- State serialization round-trip (JSON in/out via stdin/stdout)
- Edge cases: last two players, all ones rolled, maximum bid, minimum bid
