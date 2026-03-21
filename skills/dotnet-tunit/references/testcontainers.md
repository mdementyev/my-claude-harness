# TestContainers Integration

## Fixture Structure

Fixtures implement `IAsyncInitializer` + `IAsyncDisposable` (NOT xUnit's `IAsyncLifetime`):

```csharp
using TUnit.Core.Interfaces; // required for IAsyncInitializer

public class KafkaFixture : IAsyncInitializer, IAsyncDisposable
{
    private KafkaContainer? _container;

    // Guard against premature access
    public string BootstrapServers =>
        _container?.GetBootstrapAddress()
        ?? throw new InvalidOperationException("Container not initialized");

    public async Task InitializeAsync()
    {
        _container = new KafkaBuilder("confluentinc/cp-kafka:7.6.0").Build();
        await _container.StartAsync();
    }

    public async ValueTask DisposeAsync()
    {
        if (_container is not null)
            await _container.DisposeAsync();
    }
}
```

Key signatures: `InitializeAsync()` returns `Task`, `DisposeAsync()` returns `ValueTask`.

## Fixture Injection

Use `[ClassDataSource<T>]` with `required` + `init`:

```csharp
[ClassDataSource<KafkaFixture>(Shared = SharedType.PerTestSession)]
public required KafkaFixture Kafka { get; init; }
```

Multiple fixtures can be injected independently on separate properties.

### SharedType Options

| SharedType | Scope | Use Case |
|---|---|---|
| `None` | New instance per test | Isolated state (rare for containers) |
| `PerClass` | One per test class | Class-specific container state |
| `PerTestSession` | One for entire test run | Expensive resources (containers, databases) |

## Parallel Test Isolation

Tests sharing mutable container state must not run in parallel:

```csharp
[NotInParallel("Kafka")]
public class KafkaIntegrationTests
{
    [ClassDataSource<KafkaFixture>(Shared = SharedType.PerTestSession)]
    public required KafkaFixture Kafka { get; init; }
}
```

## Schema Idempotency

Create schemas in `InitializeAsync()`, not in `[Before(Test)]`:

```csharp
public async Task InitializeAsync()
{
    _container = new PostgreSqlBuilder().Build();
    await _container.StartAsync();

    // Idempotent — safe when SharedType.PerTestSession runs once
    await ExecuteAsync("CREATE TABLE IF NOT EXISTS ...");
    await ExecuteAsync("CREATE INDEX IF NOT EXISTS ...");
}
```

## Test Data Isolation

Use unique keys per test to avoid interference when sharing containers:

```csharp
[Test]
public async Task Produces_Message_To_Topic()
{
    var topic = $"test-{Guid.NewGuid()}";
    // Each test gets its own topic — no cross-test pollution
}
```

## Common Mistakes

| Wrong | Correct |
|---|---|
| `IAsyncLifetime` (xUnit) | `IAsyncInitializer` + `IAsyncDisposable` |
| `[ClassData<T>]` | `[ClassDataSource<T>(...)]` |
| `public T Prop { get; set; }` | `public required T Prop { get; init; }` |
| `SharedType.Globally` | `SharedType.PerTestSession` |
| Schema in `[Before(Test)]` | Schema in fixture's `InitializeAsync()` |
| Shared topic/table names | Unique per test: `$"test-{Guid.NewGuid()}"` |
| Missing `using TUnit.Core.Interfaces` | Required for `IAsyncInitializer` |
