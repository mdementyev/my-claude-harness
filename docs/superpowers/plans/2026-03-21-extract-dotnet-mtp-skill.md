# Extract dotnet-mtp Skill Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extract MTP platform content from `dotnet-tunit` into a standalone `dotnet-mtp` skill reusable by any MTP-based test framework.

**Architecture:** Create `skills/dotnet-mtp/SKILL.md` containing CLI syntax and `--treenode-filter` query language. Update `skills/dotnet-tunit/SKILL.md` to remove MTP content and add a mandatory reference to the new skill. Delete `skills/dotnet-tunit/references/filtering.md`.

**Tech Stack:** Claude Code skills (Markdown with YAML frontmatter)

**Spec:** `docs/superpowers/specs/2026-03-21-extract-dotnet-mtp-skill-design.md`

---

### Task 1: Create `dotnet-mtp` skill

**Files:**
- Create: `skills/dotnet-mtp/SKILL.md`

- [ ] **Step 1: Create the skill file**

Create `skills/dotnet-mtp/SKILL.md` with this exact content:

````markdown
---
name: dotnet-mtp
description: MANDATORY before ANY `dotnet test` command in projects using Microsoft Testing Platform (MTP), including TUnit. Do not construct `--treenode-filter` arguments from memory — the syntax is non-obvious and you WILL get it wrong.
---

# Microsoft Testing Platform (MTP) Reference

MTP replaces VSTest as the test runner for modern .NET test frameworks (TUnit, MSTest 3.x+). This skill covers MTP-specific CLI syntax and test filtering.

## Running Tests (MTP CLI)

MTP does **not** accept positional project/solution arguments. Use explicit flags:

```bash
# Solution — must use --solution flag
dotnet test --solution MySolution.sln

# Project — must use --project flag
dotnet test --project MyProject.csproj
```

Passing them as positional arguments (the old VSTest way) does not work with MTP.

## Test Filtering (`--treenode-filter`)

### Path Syntax

The test tree has four levels: `/Assembly/Namespace/Class/Method`

```bash
dotnet test --treenode-filter "/*/*/MyClassName/*"
```

### Wildcards

| Pattern | Meaning |
|---|---|
| `*` | Matches any characters within one level |
| `**` | Matches any depth (recursive) |
| `A*` | Starts with A |
| `*A` | Ends with A |
| `*A*` | Contains A |

**Not supported:** `/A/**/B` — recursive wildcard cannot be followed by a specific node.

### Logical Operators

| Operator | Meaning |
|---|---|
| `&` | AND |
| `\|` | OR |
| `()` | Grouping (required when combining) |

```bash
# Nodes starting with "Integration" AND not ending with "Slow"
dotnet test --treenode-filter "/*/*/(Integration*)&(!*Slow)/*"
```

## Property Filtering

Filter by test properties using `[key=value]` syntax:

```bash
# Property equals value
dotnet test --treenode-filter "/**[Category=Integration]"

# Property not equal
dotnet test --treenode-filter "/**[Category!=Slow]"

# Wildcard in value
dotnet test --treenode-filter "/**[Category=Int*]"

# Boolean property (exists/not exists)
dotnet test --treenode-filter "/**[FunctionalTest=true]"

# Combined properties
dotnet test --treenode-filter "/**[(Category=Integration)|(Priority=High)]"
```

## Combined Path + Property

```bash
dotnet test --treenode-filter "/*/*/MyClass/*[OS=Linux]"
```

## Common Recipes

| Goal | Filter |
|---|---|
| All tests in a class | `/*/*/MyClassName/*` |
| Single test method | `/*/*/MyClassName/MyMethodName` |
| All tests in namespace subtree | `/*/MyNamespace*/**` |
| Tests by property | `/**[Category=Integration]` |
| Class + property | `/*/*/MyClass/*[OS=Linux]` |
| Tests starting with prefix | `/*/*/*/Test_*` |

## Common Mistakes

| Wrong (VSTest) | Correct (MTP) |
|---|---|
| `--filter "FullyQualifiedName~Foo"` | `--treenode-filter "/*/*/Foo/*"` |
| `--filter "Category=Integration"` | `--treenode-filter "/**[Category=Integration]"` |
| `dotnet test --filter` | `dotnet test --treenode-filter` |
| `dotnet test MySolution.sln` | `dotnet test --solution MySolution.sln` |
| `dotnet test MyProject.csproj` | `dotnet test --project MyProject.csproj` |
````

- [ ] **Step 2: Verify the file**

Read back the file and confirm it matches the content above.

- [ ] **Step 3: Commit**

```bash
git add skills/dotnet-mtp/SKILL.md
git commit -m "feat: add dotnet-mtp skill with MTP CLI and filtering reference"
```

---

### Task 2: Update `dotnet-tunit` SKILL.md

**Files:**
- Modify: `skills/dotnet-tunit/SKILL.md`

- [ ] **Step 1: Update the frontmatter description**

Change line 3 from:
```
description: Use when writing, modifying, or reviewing TUnit tests in .NET projects. Covers test structure, assertions, data-driven testing, filtering, and TestContainers integration. ALSO MANDATORY before ANY `dotnet test` command in TUnit/MTP projects — do not construct `--treenode-filter` arguments from memory, the syntax is non-obvious and you WILL get it wrong.
```
To:
```
description: Use when writing, modifying, or reviewing TUnit tests in .NET projects. Covers test structure, assertions, data-driven testing, and TestContainers integration.
```

- [ ] **Step 2: Replace the MTP intro and "Running Tests" section with a mandatory skill reference**

Replace lines 6-26 (from `# TUnit Testing Reference` through the blank line after `**Wrong (VSTest habit):**`) with:

```markdown
# TUnit Testing Reference

> **MANDATORY:** You MUST invoke the `dotnet-mtp` skill before running any `dotnet test` command. TUnit uses Microsoft Testing Platform (MTP), not VSTest.
```

- [ ] **Step 3: Remove the `--filter` to `--treenode-filter` row from the mapping table**

Delete this row (line 56):
```
| `--filter "FullyQualifiedName~X"` | `--treenode-filter "/*/*/X/*"` |
```

- [ ] **Step 4: Remove the filtering.md row from the Reference Files table**

Delete this row (line 71):
```
| `references/filtering.md` | MTP `--treenode-filter` graph query syntax |
```

- [ ] **Step 5: Verify the file**

Read back the full file and confirm:
- Frontmatter has no MTP/filtering references
- Mandatory skill reference note is present
- No "Running Tests (MTP CLI)" section
- Mapping table has no `--filter` row
- Reference Files table has no filtering.md row
- All TUnit-specific content is intact

- [ ] **Step 6: Commit**

```bash
git add skills/dotnet-tunit/SKILL.md
git commit -m "refactor: remove MTP content from dotnet-tunit, reference dotnet-mtp skill"
```

---

### Task 3: Delete `references/filtering.md`

**Files:**
- Delete: `skills/dotnet-tunit/references/filtering.md`

- [ ] **Step 1: Delete the file**

```bash
git rm skills/dotnet-tunit/references/filtering.md
```

- [ ] **Step 2: Commit**

```bash
git commit -m "chore: remove filtering.md, content moved to dotnet-mtp skill"
```

---

### Task 4: Run install script and verify

- [ ] **Step 1: Run install.sh**

```bash
./install.sh
```

Expected: should show `linking: dotnet-mtp` and `ok: dotnet-tunit` (or similar).

- [ ] **Step 2: Verify symlink exists**

```bash
ls -la ~/.claude/skills/dotnet-mtp
```

Expected: symlink pointing to `skills/dotnet-mtp` in this repo.

- [ ] **Step 3: Verify dotnet-mtp SKILL.md is readable through symlink**

Read `~/.claude/skills/dotnet-mtp/SKILL.md` and confirm it matches what was written.

- [ ] **Step 4: Commit (if any changes)**

No changes expected from this task — verification only.
