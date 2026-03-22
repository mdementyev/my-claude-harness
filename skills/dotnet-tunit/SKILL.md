---
name: dotnet-tunit
description: Use when writing, modifying, or reviewing TUnit tests in .NET projects. Covers test structure, assertions, data-driven testing, and TestContainers integration.
user-invocable: false
---

# TUnit Testing Reference

> **MANDATORY:** You MUST invoke the `dotnet-mtp` skill before running any `dotnet test` command. TUnit uses Microsoft Testing Platform (MTP), not VSTest.

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
| `Assert.InRange(v, lo, hi)` | `await Assert.That(v).IsBetween(lo, hi)` |
| `response.EnsureSuccessStatusCode()` | `await Assert.That(response).IsOk()` |
| `IAsyncLifetime` | `IAsyncInitializer` + `IAsyncDisposable` |

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
| `references/testcontainers.md` | TestContainers fixtures, `SharedType`, isolation patterns |
| `references/assertions-core.md` | `.And`/`.Or` chaining, `Assert.Multiple`, return values |
| `references/assertions-values.md` | Equality, comparison, null, boolean, numeric, type checking |
| `references/assertions-strings.md` | Contains, StartsWith, case/whitespace modifiers, regex, parsing |
| `references/assertions-collections.md` | `.Count()`, Contains, All/Any, Equivalency, ordering |
| `references/assertions-exceptions.md` | `Throws`/`ThrowsExactly`, message wildcards, async, try/catch |
| `references/assertions-specialized.md` | DateTime, Task, GUID, CancellationToken, Member, `Eventually`/`WaitsFor`, `Satisfies` |
| `references/assertions-json.md` | `JsonElement`, `JsonNode`, JSON string validity |
| `references/assertions-http.md` | `HttpResponseMessage` status, headers, content; `HttpStatusCode` |
