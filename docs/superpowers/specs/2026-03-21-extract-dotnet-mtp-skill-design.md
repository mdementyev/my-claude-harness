# Extract dotnet-mtp Skill from dotnet-tunit

## Problem

The `dotnet-tunit` skill contains Microsoft Testing Platform (MTP) content that is not TUnit-specific. MTP is the platform layer used by TUnit, MSTest 3.x+, and other frameworks. Test filtering and CLI syntax belong to MTP, not TUnit. Extracting this content into a standalone `dotnet-mtp` skill makes it reusable across any MTP-based test framework.

## Decision

Extract all MTP-specific content from `dotnet-tunit` into a new `dotnet-mtp` skill. The new skill is a single `SKILL.md` file (no `references/` subdirectory) containing CLI syntax and the full `--treenode-filter` query language.

## New skill: `skills/dotnet-mtp/SKILL.md`

A single file with:

1. **Frontmatter** — name `dotnet-mtp`. Description states it is MANDATORY before ANY `dotnet test` command in MTP-based projects (including TUnit). Warns not to construct `--treenode-filter` arguments from memory.
2. **CLI syntax section** — `--project`/`--solution` flags, positional argument prohibition, VSTest-to-MTP migration table for CLI commands.
3. **Filtering section** — full `--treenode-filter` graph query syntax folded in from `references/filtering.md`: path syntax (`/Assembly/Namespace/Class/Method`), wildcards, logical operators, property filtering, combined path+property filters, common recipes, common mistakes table.

All content comes from existing `dotnet-tunit` files. No new content.

## Changes to `skills/dotnet-tunit/SKILL.md`

1. **Frontmatter description** — remove the "ALSO MANDATORY before ANY `dotnet test`" clause. That responsibility belongs to `dotnet-mtp`.
2. **Add mandatory skill reference** — prominent note near the top: "You MUST invoke the `dotnet-mtp` skill before running any `dotnet test` command."
3. **Remove "Running Tests (MTP CLI)" section** — `--project`/`--solution` syntax moves to `dotnet-mtp`.
4. **Remove VSTest-to-MTP rows from mapping table** — the `--filter` to `--treenode-filter` and positional argument rows move out. TUnit-specific rows (attributes, assertions, `IAsyncLifetime`) stay.
5. **Delete `references/filtering.md`** — content is now in `dotnet-mtp/SKILL.md`.

## What stays in dotnet-tunit

- All assertion references (`references/assertions-*.md`)
- Test structure, lifecycle hooks, parallelism (`references/test-structure.md`)
- Data-driven testing (`references/data-driven.md`)
- TestContainers integration (`references/testcontainers.md`)
- TUnit-specific mapping table (xUnit/NUnit attributes to TUnit equivalents)
- The "One Rule" (every assertion must be awaited)
- Namespace imports table
- Reference files table (updated to remove filtering.md)
