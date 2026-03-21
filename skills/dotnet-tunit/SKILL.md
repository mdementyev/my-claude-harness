---
name: dotnet-tunit
description: Use when writing, modifying, or reviewing TUnit tests in .NET projects. Covers test structure, assertions, data-driven testing, filtering, and TestContainers integration. ALSO MANDATORY before ANY `dotnet test` command in TUnit/MTP projects — do not construct `--treenode-filter` arguments from memory, the syntax is non-obvious and you WILL get it wrong.
---

# TUnit Testing Reference

TUnit is built on **Microsoft Testing Platform (MTP)**, not VSTest. This affects CLI syntax (see `references/filtering.md`).

## Running Tests (MTP CLI)

MTP does **not** accept positional project/solution arguments. Use explicit flags:

```bash
# Project — must use --project flag
dotnet test --project tests/MyProject

# Solution — must use --solution flag
dotnet test --solution MySolution.sln

# With filter
dotnet test --project tests/MyProject --treenode-filter "/*/*/MyClassName/*"
```

**Wrong (VSTest habit):** `dotnet test tests/MyProject` — this errors under MTP.

## The One Rule

Every assertion MUST be awaited. Every test method MUST be `async Task`.

```csharp
[Test]
public async Task My_Test()
{
    await Assert.That(value).IsEqualTo(expected);
}
```

Missing `await` compiles but **silently skips the assertion**. The test passes without checking anything.

## xUnit/NUnit → TUnit

| xUnit/NUnit | TUnit |
|---|---|
| `[Fact]` / `[Test]` (NUnit) | `[Test]` |
| `[Theory]` / `[TestCase]` | `[Test]` + `[Arguments]` |
| `[InlineData(1, 2)]` | `[Arguments(1, 2)]` |
| `[MemberData]` / `[TestCaseSource]` | `[MethodDataSource]` |
| `[ClassData]` | `[ClassDataSource<T>]` |
| `Assert.Equal(expected, actual)` | `await Assert.That(actual).IsEqualTo(expected)` |
| `Assert.Null(x)` | `await Assert.That(x).IsNull()` |
| `Assert.Throws<T>(() => ...)` | `await Assert.That(act).Throws<T>()` |
| `Assert.Contains("x", str)` | `await Assert.That(str).Contains("x")` |
| `Assert.Single(c)` | `await Assert.That(c).HasSingleItem()` |
| `IAsyncLifetime` | `IAsyncInitializer` + `IAsyncDisposable` |
| `--filter "FullyQualifiedName~X"` | `--treenode-filter "/*/*/X/*"` |

## Namespace Imports

| Import | When needed |
|---|---|
| _(implicit)_ | `Assert.That()` — available by default |
| `using TUnit.Core.Interfaces` | `IAsyncInitializer` for async fixture setup |

## Reference Files

| File | Covers |
|---|---|
| `references/test-structure.md` | `[Test]`, lifecycle hooks, parallelism, `IAsyncInitializer` |
| `references/data-driven.md` | `[Arguments]`, `[MethodDataSource]`, `[ClassDataSource]`, `[MatrixDataSource]` |
| `references/filtering.md` | MTP `--treenode-filter` graph query syntax |
| `references/testcontainers.md` | TestContainers fixtures, `SharedType`, isolation patterns |
| `references/assertions-core.md` | `.And`/`.Or` chaining, `Assert.Multiple`, return values |
| `references/assertions-values.md` | Equality, comparison, null, boolean, numeric, type checking |
| `references/assertions-strings.md` | Contains, StartsWith, case/whitespace modifiers, regex, parsing |
| `references/assertions-collections.md` | `.Count()`, Contains, All/Any, Equivalency, ordering |
| `references/assertions-exceptions.md` | `Throws`/`ThrowsExactly`, message wildcards, async, try/catch |
| `references/assertions-specialized.md` | DateTime, Task, GUID, CancellationToken, Member, `WaitsFor` |
