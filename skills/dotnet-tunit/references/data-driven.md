# Data-Driven Testing

## [Arguments] — Inline Test Data

Replaces xUnit's `[InlineData]`. Apply multiple `[Arguments]` to one `[Test]` method:

```csharp
[Test]
[Arguments(1, 2, 3)]
[Arguments(0, 0, 0)]
[Arguments(-1, 1, 0)]
public async Task Add_Returns_Sum(int a, int b, int expected)
{
    await Assert.That(a + b).IsEqualTo(expected);
}
```

Optional properties: `DisplayName` (supports `$paramName` substitution), `Categories`, `Skip`.

## [MethodDataSource] — External Data

Replaces xUnit's `[MemberData]`. Three forms:

```csharp
// Same class — nameof
[Test]
[MethodDataSource(nameof(GetCases))]
public async Task My_Test(int input, string expected) { }

public static IEnumerable<(int, string)> GetCases() => [(1, "one"), (2, "two")];

// External class — typeof + nameof (works with static classes)
[Test]
[MethodDataSource(typeof(SharedData), nameof(SharedData.GetCases))]
public async Task My_Test(string value) { }

// External class — generic form (class must NOT be static)
[Test]
[MethodDataSource<SharedData>(nameof(SharedData.GetCases))]
public async Task My_Test(string value) { }
```

Data source can return `IEnumerable<T>`, `IAsyncEnumerable<T>`, `Task<T>`, tuples, or arrays.

## [ClassDataSource<T>] — Fixture Injection

Injects shared fixtures into test classes. Property must use `required` + `init`:

```csharp
[ClassDataSource<KafkaFixture>(Shared = SharedType.PerTestSession)]
public required KafkaFixture Kafka { get; init; }
```

### SharedType Options

| SharedType | Scope | Use Case |
|---|---|---|
| `None` | New instance per test | Isolated per-test state (rare for fixtures) |
| `PerClass` | One per test class | Class-specific state |
| `PerTestSession` | One for entire test run | Expensive resources (containers, databases) |

## [MatrixDataSource] — Combinatorial

Generates all combinations of parameter values:

```csharp
[Test]
[MatrixDataSource]
public async Task Matrix_Test(
    [Matrix(1, 2, 3)] int x,
    [Matrix("a", "b")] string y)
{
    // Generates 6 test cases: (1,"a"), (1,"b"), (2,"a"), (2,"b"), (3,"a"), (3,"b")
}
```

Booleans and enums auto-expand all values without `[Matrix]`:

```csharp
[Test]
[MatrixDataSource]
public async Task Bool_Test(bool flag, MyEnum mode)
{
    // Generates cases for all bool × enum combinations
}
```

## Common Mistakes

| Wrong (xUnit/NUnit) | Correct (TUnit) |
|---|---|
| `[InlineData(1, 2)]` | `[Arguments(1, 2)]` |
| `[MemberData(nameof(X))]` | `[MethodDataSource(nameof(X))]` |
| `[ClassData(typeof(X))]` | `[ClassDataSource<X>]` |
| `public KafkaFixture Kafka { get; set; }` | `public required KafkaFixture Kafka { get; init; }` |
| `SharedType.Globally` | `SharedType.PerTestSession` |
