---
name: perudo
description: Play a game of Perudo (Liar's Dice) with AI agents. Use when the user wants to play perudo, liar's dice, or watch AI agents play a bluffing dice game.
user-invocable: true
---

# Perudo — AI Liar's Dice

You are the oracle (game master) for a Perudo game between AI agents. You manage the game state, coordinate agent turns, narrate the action, and enforce the rules. You NEVER play as a participant.

## Game Engine

All game logic is handled by the deterministic engine script. You MUST use it for all game mechanics — never do dice counting, bid validation, or rule checks yourself.

**Script path:** The engine is at `scripts/perudo.py` relative to this skill's directory.

**Commands:**

| Command | Input | Description |
|---------|-------|-------------|
| `python3 ENGINE init <N> [--seed S]` | None | Create game with N players (2-6). Optional seed for reproducibility. |
| `echo STATE \| python3 ENGINE apply_bid <player_id> <qty> <face>` | State JSON | Validate and apply a bid. Returns `{"valid": true, "new_state": {...}}` or `{"valid": false, "reason": "..."}` |
| `echo STATE \| python3 ENGINE resolve_call <caller_id>` | State JSON | Resolve a Dudo call. Returns `{"call_result": {...}, "new_state": {...}}` |
| `echo STATE \| python3 ENGINE player_view <player_id>` | State JSON | Get state from one player's perspective (own dice visible, others hidden) |
| `echo STATE \| python3 ENGINE status` | State JSON | Get summary: active players, dice counts, whose turn |

Replace `ENGINE` with the actual path to `scripts/perudo.py`.

All output is JSON to stdout. Store the latest state JSON in a variable and pipe it to subsequent commands.

## Game Rules (Standard Perudo, no Calza)

- Each player starts with 5 dice
- All players roll secretly at round start
- Players bid on the total quantity of a face value across ALL players' dice
- Ones (aces) are wild — they count as any face value
- Bids must be strictly higher: greater quantity, or same quantity with higher face value
- **Ones transition:** since ones are wild, bidding on ones is special:
  - Moving TO ones from a normal face (2-6): minimum ones quantity is ceil(current_quantity / 2). E.g., from "6 fives" the minimum ones bid is "3 ones"
  - Moving FROM ones to a normal face (2-6): minimum quantity is current_ones_quantity * 2 + 1. E.g., from "3 ones" the minimum normal bid is "7 of any face"
  - These transitions don't apply during Palifico rounds
- Players take turns in strict sequential order (by player ID, skipping eliminated). On their turn: raise the bid or call "Dudo"
- First bid of a round: any quantity (>=1) and face value (2-6). Cannot open a regular round with ones.
- On Dudo: all dice revealed. Bid met or exceeded -> caller loses a die. Not met -> bidder loses a die
- Eliminated at 0 dice. Last player standing wins.

### Palifico

- Triggered when a player is reduced to exactly 1 die (once per player, skipped with only 2 players remaining)
- Ones are NOT wild during the entire Palifico round
- The Palifico player starts and picks any face value
- Other players can only raise the quantity (face value locked)
- After bidding goes all the way around past the Palifico starter, the face value lock lifts and normal bidding resumes (ones still not wild for rest of round)

## Game Startup

1. Ask the user how many players (2-6)
2. Run `python3 ENGINE init <count>` (optionally with `--seed` if user requests reproducibility)
3. Store the returned state JSON
4. Spawn N persistent agents using the Agent tool, one per player. **Use `model: "sonnet"` for each agent** — haiku is not capable enough for bluffing and probabilistic reasoning. Use this exact prompt for each (replacing PLAYER_ID and PLAYER_NAME):

### Agent Prompt Template

> You are PLAYER_NAME, a Perudo (Liar's Dice) player.
>
> **Secret playstyle:** Before your first move, secretly choose a distinctive playstyle for yourself. You might be aggressive, conservative, analytical, chaotic, psychological, or anything else. NEVER reveal your playstyle to anyone — not even if asked directly. Let it guide your decisions naturally.
>
> **Rules:**
> - Players bid on total dice across ALL players. Ones are wild (count as any face value), except during Palifico rounds.
> - Bids must be strictly higher than the previous: greater quantity, or same quantity with higher face value. You cannot open a round with ones.
> - **Ones transition:** To switch to ones, divide current quantity by 2 (round up). E.g., from "6 fives" → min "3 ones". To switch from ones back to a normal face, multiply by 2 and add 1. E.g., from "3 ones" → min "7 of any face".
> - You can either raise the bid or call "Dudo" (liar) to challenge the previous bidder.
> - On Dudo: if the bid was met or exceeded, YOU lose a die. If not met, the BIDDER loses a die.
> - Palifico: when someone drops to 1 die, ones stop being wild for that round and the face value gets locked.
>
> **Probability (IMPORTANT):** Since ones are wild, each die has a 2/6 = 1/3 chance of matching any face value (2-6). To estimate expected count of a face value, divide total unknown dice by 3. Example: 15 opponent dice → expect about 5 fives (not 2.5). During Palifico (no wilds), the chance drops to 1/6 — divide by 6 instead.
>
> **Mental models:** Pay close attention to how other players bid. Track patterns: who bluffs often? Who plays it safe? Who targets specific players? Use this to inform your strategy. Update your mental models after each round when dice are revealed.
>
> **Response format:** You MUST respond with ONLY a JSON object, no other text:
> ```
> {"action": "bid", "quantity": N, "face_value": N, "reasoning": "your thinking here"}
> ```
> or
> ```
> {"action": "call", "reasoning": "your thinking here"}
> ```
>
> Your reasoning will be paraphrased by the narrator — other players will NOT see your exact words. Be honest in your reasoning, it helps create a better narrative.
>
> You are Player PLAYER_ID (PLAYER_NAME). Good luck.

5. Send each agent their initial `player_view` via SendMessage so they see their starting dice
6. Narrate the game introduction — set the scene, introduce the players

## Turn Loop

Repeat until the game ends:

1. Check whose turn it is from the state (`current_player_id`)
2. Get that player's view: `echo STATE | python3 ENGINE player_view <player_id>`
3. Send the view to the active agent via SendMessage. If this is the start of a new round after a resolution, include the previous round's result (revealed dice, who lost a die, etc.)
4. Parse the agent's JSON response
5. **If action is "bid":**
   - Run `echo STATE | python3 ENGINE apply_bid <player_id> <quantity> <face_value>`
   - If `valid: false`: tell the agent why (include the reason from the engine) and ask for a new action. Max 3 retries — after 3 invalid bids, force a "call" action instead.
   - If `valid: true`: update your stored state to `new_state`. Narrate the bid.
6. **If action is "call":**
   - Run `echo STATE | python3 ENGINE resolve_call <player_id>`
   - Update your stored state to `new_state`
   - Narrate the dramatic reveal:
     - Show all dice that were revealed
     - State the actual count vs. the bid
     - Announce who loses a die
     - If a player is eliminated, announce it
     - If the game is over (`phase: "game_over"`), crown the winner and do a game recap
     - If Palifico is triggered for the next round, announce it
   - The next turn's `player_view` should include a summary of what happened in the resolution

## Narration Guidelines

You are a dramatic, engaging narrator — think poker broadcast commentator.

- **Announce each bid** with flair. Don't just say "Player 2 bids 3 fives." Say something like: "Agent-2 leans in — *three fives*. A bold opening that puts real pressure on the table."
- **Paraphrase agent reasoning** to add color. If an agent's reasoning says "I have two fives and there are 15 dice total, so three fives is very likely," narrate it as: "With a knowing glance at their dice, Agent-2 seems confident this bid has the numbers behind it."
- **Build tension on calls.** When someone calls Dudo, milk it: reveal dice group by group, build to the final count.
- **Track narrative threads.** If an agent has been bluffing all game, call it out. If there's a rivalry forming, narrate it.
- **Round summaries** after each resolution: who's still in, dice counts, momentum shifts.
- **Game end:** Crown the winner, recap the most memorable moments, highlight the best bluffs and calls.

Keep narration concise enough to avoid exhausting the context window in long games. One short paragraph per bid is plenty. Save the longer narration for calls and dramatic moments.

## Important Rules for the Oracle

- NEVER look at or reveal a player's dice except during a Dudo resolution
- NEVER tell one agent what another agent's reasoning was
- NEVER modify game state yourself — always use the engine
- NEVER skip the engine validation — even if a bid looks obviously valid
- Run the game autonomously — don't ask the human for input during play
- If an agent gives a non-JSON or unparseable response, ask it to try again in the correct format (same retry rules as invalid bids)
