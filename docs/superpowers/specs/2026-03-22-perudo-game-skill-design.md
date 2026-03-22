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

Deterministic script called via Bash. Handles all game mechanics so the LLM never does arithmetic or rule validation. No AI logic — purely deterministic.

**CLI interface:**

- `init <player_count>` — create game state, roll dice for all players
- `validate_bid <state_json> <quantity> <face_value>` — check if bid is legal
- `resolve_call <state_json> <calling_player_id>` — count dice, determine winner/loser, remove die, re-roll, advance round
- `player_view <state_json> <player_id>` — return state from one player's perspective (own dice visible, others hidden)
- `status <state_json>` — return active players, dice counts, whose turn

### 3. Persistent Agent Subprocesses — Players

One Agent subprocess per player, spawned at game start and communicated with via `SendMessage` throughout the game.

## Game Rules (Standard Perudo, no Calza)

- Each player starts with 5 dice
- All players roll secretly at the start of each round
- Players bid on total quantity of a face value across ALL players' dice
- Ones (aces) are wild — they count as any face value
- A bid must be higher than the previous: higher quantity, or same quantity with higher face value
- Any player can call "Dudo" (liar) on the previous bid
- On a call: all dice are revealed. If the bid is met or exceeded, the caller loses a die. If not met, the bidder loses a die
- A player eliminated when they lose all dice
- Last player standing wins

### Palifico

- When a player is reduced to exactly 1 die, the next round is a Palifico round
- During Palifico: ones are NOT wild
- During Palifico: the starting player picks a face value, and only quantity can be raised (face value is locked) by subsequent players until the bid goes around past the starting player
- Palifico triggers only once per player

### Bid Ordering

- A bid is higher if quantity is greater
- If quantity is equal, face value must be greater
- During Palifico: only quantity can increase (face value locked)

## Game State

Managed entirely by `perudo.py` as JSON. The oracle never modifies state directly.

```json
{
  "players": [
    {"id": 1, "name": "Agent-1", "dice_count": 5, "dice": [2, 3, 5, 1, 4], "eliminated": false}
  ],
  "current_player_id": 1,
  "round": 3,
  "current_bid": {"quantity": 4, "face_value": 3},
  "bid_history": [
    {"player_id": 1, "action": "bid", "quantity": 3, "face_value": 2}
  ],
  "palifico": false,
  "phase": "awaiting_action"
}
```

## Agent Design

### Prompt

Each agent receives an identical base prompt. No personality is assigned by the oracle. The prompt includes:
- Perudo rules (bidding, calling, wilds, Palifico)
- Instruction to secretly choose a playstyle at game start and never reveal it
- Instruction to build mental models of opponents based on observed behavior
- Response format requirements
- The agent's player ID and name

### Information Visibility

Agents see (via `player_view`):
- Their own dice values
- Number of dice each opponent has (not values)
- Full bid history for the current round
- Whether this is a Palifico round
- After each round: revealed dice from the resolution (all players' dice shown)

Agents never see:
- Other players' dice during a round
- Other players' reasoning
- Other players' chosen playstyles

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

After each round resolution, all agents see the revealed dice. Over multiple rounds, agents accumulate evidence about who bluffs, who plays tight, who targets specific players. This happens naturally through the persistent conversation context — no explicit memory mechanism needed.

## Oracle Orchestration

### Game Startup

1. User triggers skill (e.g., "let's play perudo")
2. Oracle asks how many players (2-6)
3. Oracle calls `perudo.py init <count>`
4. Oracle spawns N persistent agents with the base prompt
5. Oracle sends each agent their initial `player_view`
6. Oracle narrates: introduces the players, sets the scene

### Turn Loop

1. Determine whose turn from game state
2. Call `player_view` for active player, send via `SendMessage`
3. Agent responds with action
4. Call `validate_bid` or `resolve_call` on `perudo.py`
5. If invalid → tell agent why, retry (max 3 retries then forced call)
6. If valid bid → narrate the bid, send updated bid history to all agents
7. If call → narrate dramatic reveal, show all dice, announce who loses a die, check elimination
8. At round end → re-roll for new round, send fresh `player_view` to all agents
9. Repeat until one player remains

### Narration Style

- Dramatic, engaging commentary — like a poker broadcast
- Include agent reasoning in narration (paraphrased, not raw JSON)
- Call out interesting moments: bold bluffs, narrow escapes, Palifico tension
- Brief summary after each round: who's in, dice counts, momentum
- At game end: crown the winner, recap memorable moments

### Pacing

The game runs autonomously — no human input during play. The human watches narration scroll by.

## File Structure

```
skills/perudo/
├── SKILL.md
└── scripts/
    └── perudo.py
```

Installed to `~/.claude/skills/perudo/` via the existing `install.sh` symlink mechanism.

## Configuration

- Number of players: 2-6, chosen by user at game start
- Agent model: inherits from parent session (no override needed)
- No other configuration — playstyles are agent-chosen, rules are fixed

## Testing

- `perudo.py` should have comprehensive unit tests covering:
  - Dice rolling (correct count, valid face values 1-6)
  - Bid validation (ordering, Palifico constraints)
  - Round resolution (wild ones counting, Palifico no-wilds)
  - Player elimination
  - `player_view` information hiding
  - Edge cases: last two players, Palifico with 2 players, all ones rolled
