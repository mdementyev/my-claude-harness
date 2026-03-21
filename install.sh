#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILLS_SRC="$REPO_DIR/skills"
SKILLS_DST="$HOME/.claude/skills"

mkdir -p "$SKILLS_DST"

# Remove stale symlinks pointing into this repo
for link in "$SKILLS_DST"/*/; do
  link="${link%/}"
  [ -L "$link" ] || continue
  target="$(readlink "$link")"
  case "$target" in
    "$SKILLS_SRC"/*)
      if [ ! -e "$link" ]; then
        echo "removing stale symlink: $(basename "$link")"
        rm "$link"
      fi
      ;;
  esac
done

# Create/update symlinks for each skill
for skill_dir in "$SKILLS_SRC"/*/; do
  skill_dir="${skill_dir%/}"
  name="$(basename "$skill_dir")"
  dest="$SKILLS_DST/$name"

  if [ -L "$dest" ]; then
    existing="$(readlink "$dest")"
    if [ "$existing" = "$skill_dir" ]; then
      echo "ok: $name"
      continue
    fi
    echo "updating: $name"
    rm "$dest"
  elif [ -e "$dest" ]; then
    echo "skipping: $name (non-symlink already exists at $dest)"
    continue
  else
    echo "linking: $name"
  fi

  ln -s "$skill_dir" "$dest"
done
