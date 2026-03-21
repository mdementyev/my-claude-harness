# Test Structure

## Test Methods

Every test method uses `[Test]` and returns `async Task`:

```csharp
[Test]
public async Task Method_Name_Describes_Behavior()
{
    var result = sut.DoSomething();
    await Assert.That(result).IsEqualTo(expected);
}
```

## Lifecycle Hooks

### Per-Test Hooks (instance methods)

```csharp
[Before(Test)]
public async Task Setup() { }

[Before(Test)]
public async Task Setup(TestContext context, CancellationToken ct) { }

[After(Test)]
public async Task Cleanup() { }
```

`[Before(Test)]`/`[After(Test)]` must be **instance** methods. Return `void` or `Task`. Optional parameters: `TestContext`, `CancellationToken`.

### Per-Class Hooks (static methods)

```csharp
[Before(Class)]
public static async Task ClassSetup() { }

[After(Class)]
public static async Task ClassCleanup() { }
```

`[Before(Class)]`/`[After(Class)]` must be **static**.

### Assembly Hooks

```csharp
[Before(Assembly)]
public static async Task AssemblySetup() { }

[After(Assembly)]
public static async Task AssemblyCleanup() { }
```

## Parallelism

TUnit runs tests **in parallel by default**. To opt out for tests sharing mutable state:

```csharp
[NotInParallel("Kafka")]
public class KafkaIntegrationTests
{
    // Tests in this class run sequentially.
    // Other classes still run in parallel.
}
```

The string key groups classes — all classes with the same key serialize together.

## IAsyncInitializer

For async setup in fixtures/test classes. Requires explicit import:

```csharp
using TUnit.Core.Interfaces; // required — not auto-imported

public class MyFixture : IAsyncInitializer, IAsyncDisposable
{
    public async Task InitializeAsync() { }
    public async ValueTask DisposeAsync() { }
}
```

## Common Mistakes

| Wrong (xUnit/NUnit) | Correct (TUnit) |
|---|---|
| `[Fact]` or `[Test]` (NUnit) | `[Test]` |
| `public void Test()` | `public async Task Test()` |
| Constructor for setup | `[Before(Test)]` instance method |
| `IAsyncLifetime` | `IAsyncInitializer` + `IAsyncDisposable` |
| `Dispose()` for cleanup | `[After(Test)]` or `IAsyncDisposable` |
| Forgetting `using TUnit.Core.Interfaces` | Required for `IAsyncInitializer` |
| Static `[Before(Test)]` method | Must be instance method |
| Instance `[Before(Class)]` method | Must be static method |
