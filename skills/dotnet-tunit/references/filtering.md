# Test Filtering (MTP Graph Query)

TUnit uses **Microsoft Testing Platform (MTP)**, not VSTest. Use `--treenode-filter`, NOT `--filter`.

## Path Syntax

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

## Running Specific Projects or Solutions

MTP changes how `dotnet test` handles project/solution arguments:

```bash
# Solution — must use --solution flag
dotnet test --solution MySolution.sln

# Project — must use --project flag
dotnet test --project MyProject.csproj
```

Passing them as positional arguments (the old VSTest way) does not work with MTP.

## Common Mistakes

| Wrong (VSTest) | Correct (MTP) |
|---|---|
| `--filter "FullyQualifiedName~Foo"` | `--treenode-filter "/*/*/Foo/*"` |
| `--filter "Category=Integration"` | `--treenode-filter "/**[Category=Integration]"` |
| `dotnet test --filter` | `dotnet test --treenode-filter` |
| `dotnet test MySolution.sln` | `dotnet test --solution MySolution.sln` |
| `dotnet test MyProject.csproj` | `dotnet test --project MyProject.csproj` |
