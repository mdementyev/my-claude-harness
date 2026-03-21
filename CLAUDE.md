# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Purpose

This repo manages Claude Code skills, hooks, and agents. Skills are developed here and installed into `~/.claude/skills/` via symlinks.

## Installation

```bash
./install.sh
```

This symlinks each directory under `skills/` into `~/.claude/skills/`, cleaning up stale symlinks and skipping non-symlink conflicts.

## Architecture

- **`skills/<name>/SKILL.md`** — Each skill is a directory containing a `SKILL.md` with YAML frontmatter (`name`, `description`, optional `allowed-tools`) followed by markdown content. Some skills also have a `references/` subdirectory with supplementary docs.
- **`install.sh`** — Idempotent installer that manages symlinks from this repo into `~/.claude/skills/`.

## Skill Format

Every skill must have a `SKILL.md` with this structure:

```markdown
---
name: skill-name
description: When and why to use this skill
allowed-tools: Tool(pattern:*) # optional
---

# Skill content here
```

The `description` field is critical — it determines when Claude Code activates the skill.
