---
name: dotnet-mtp
description: MANDATORY before ANY `dotnet test` command in projects using Microsoft Testing Platform (MTP), including TUnit. Do not construct `--treenode-filter` arguments from memory — the syntax is non-obvious and you WILL get it wrong. Also covers MTP-specific code coverage collection (--coverage flag) — do NOT use VSTest's --collect mechanism. ALSO TRIGGER when the user asks about test coverage gaps, uncovered code, or "what isn't tested" in a .NET/TUnit project — collect real code coverage data instead of guessing by reading source.
user-invocable: false
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

- **Assembly** — assembly name without `.dll` extension
- **Namespace** — full dotted namespace as a flat string (NOT hierarchical segments). Each distinct namespace is a separate node (e.g., `MyApp.Tests` and `MyApp.Tests.Integration` are two separate level-2 nodes)
- **Class** — class name
- **Method** — method name

```bash
dotnet test --treenode-filter "/*/*/MyClassName/*"
```

### Wildcards

`*` matches any characters within one path level:

| Pattern | Meaning |
|---|---|
| `*` | Matches anything at this level |
| `A*` | Starts with A |
| `*A` | Ends with A |
| `*A*` | Contains A |

`**` matches any remaining depth but **only as a terminal segment** — it cannot be followed by more path segments:

| Pattern | Works? |
|---|---|
| `/**` | Yes — matches all tests |
| `/*/**` | Yes — matches all tests under any assembly |
| `/**/*` | No — zero matches |
| `/**/ClassName/*` | No — zero matches |

### Logical Operators

**Each operand MUST be individually parenthesized.** A single set of parens around the whole expression does NOT work.

| Operator | Meaning |
|---|---|
| `&` | AND |
| `\|` | OR |
| `!` | Negation (see rules below) |

```bash
# OR — each operand in its own parens
dotnet test --treenode-filter "/*/*/(ClassA)|(ClassB)/*"

# AND with negation
dotnet test --treenode-filter "/*/*/(Integration*)&(!*Slow)/*"
```

### Negation Rules

Negation (`!`) has two forms with different behavior:

| Form | Exact names | Wildcard patterns |
|---|---|---|
| Standalone `(!pattern)` | Does NOT work — returns zero | Works |
| With AND `(*)&(!pattern)` | Works | Works |

```bash
# WRONG — standalone negation with exact name returns zero
dotnet test --treenode-filter "/*/*/(!KafkaIntegrationTests)/*"

# CORRECT — use AND form for exact names
dotnet test --treenode-filter "/*/*/(*)&(!KafkaIntegrationTests)/*"

# OK — standalone negation with wildcard works
dotnet test --treenode-filter "/*/*/(!*Integration*)/*"
```

**Safe rule: always use `(*)&(!pattern)` for negation.** It works in all cases.

### `--list-tests` Does NOT Respect Filters

`--list-tests` ignores `--treenode-filter` and always shows all discovered tests. To verify a filter matches the expected tests, run the tests (use `--no-build` to skip rebuild).

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
| All tests in a namespace | `/*/My.Full.Namespace/*/*` |
| Exclude a class by name | `/*/*/(*)&(!MyClassName)/*` |
| Exclude a namespace | `/*/(*)&(!My.Full.Namespace)/*/*` |
| Two specific classes | `/*/*/(ClassA)|(ClassB)/*` |
| Tests matching a prefix | `/*/*/*/Test_*` |
| All tests (any depth) | `/**` |
| Tests by property | `/**[Category=Integration]` |

## Common Mistakes

| Wrong | Correct | Why |
|---|---|---|
| `--filter "FullyQualifiedName~Foo"` | `--treenode-filter "/*/*/Foo/*"` | VSTest syntax, not MTP |
| `dotnet test --filter` | `dotnet test --treenode-filter` | VSTest flag |
| `dotnet test MySolution.sln` | `dotnet test --solution MySolution.sln` | MTP requires explicit flags |
| `dotnet test MyProject.csproj` | `dotnet test --project MyProject.csproj` | MTP requires explicit flags |
| `/**/MyClass/*` | `/*/*/MyClass/*` | `**` only works as terminal segment |
| `(ClassA\|ClassB)` | `(ClassA)\|(ClassB)` | Each OR operand needs its own parens |
| `(!ExactName)` | `(*)&(!ExactName)` | Standalone negation fails for exact names |
| `--list-tests --treenode-filter "..."` | Run tests with `--no-build` | `--list-tests` ignores filters |

## Finding Coverage Gaps

> **NEVER answer "what's not covered" by reading source and test files.**
> Run coverage collection. Source-reading produces guesses; coverage data produces facts.

### Step-by-step

1. Run tests with coverage:
   ```bash
   dotnet test --project <test-project> \
     --coverage \
     --coverage-output-format cobertura \
     --coverage-output coverage.cobertura.xml
   ```

2. Generate a quick summary to identify low-coverage areas:
   ```bash
   dnx -y dotnet-reportgenerator-globaltool -- \
     -reports:coverage.cobertura.xml \
     -targetdir:CoverageReport \
     -reporttypes:TextSummary
   cat CoverageReport/Summary.txt
   ```

3. For line-level detail on low-coverage classes, generate the Markdown report:
   ```bash
   dnx -y dotnet-reportgenerator-globaltool -- \
     -reports:coverage.cobertura.xml \
     -targetdir:CoverageReport \
     -reporttypes:Markdown
   cat CoverageReport/Summary.md
   ```

4. Present real coverage data to the user. Only THEN read source for context on what uncovered lines do.

See `references/code-coverage.md` for flag details, output format options, and exclusion configuration.

## Reference Files

| File | Covers |
|---|---|
| `references/code-coverage.md` | Coverage collection, Cobertura reports, ReportGenerator, exclusions |
