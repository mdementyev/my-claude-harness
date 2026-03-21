# Assertions — Exceptions

## Throws vs ThrowsExactly

```csharp
// Allows derived exception types
await Assert.That(() => DoSomething()).Throws<InvalidOperationException>();

// Exact type match only — derived types fail
await Assert.That(() => DoSomething()).ThrowsExactly<InvalidOperationException>();
```

## ThrowsNothing

Safety assertion — verify no exception is thrown:

```csharp
await Assert.That(() => SafeOperation()).ThrowsNothing();
```

## Message Assertions

```csharp
// Exact match
await Assert.That(() => Act()).Throws<Exception>().WithMessage("exact message");

// Partial match
await Assert.That(() => Act()).Throws<Exception>().WithMessageContaining("partial");

// Wildcard match — * is the ONLY wildcard, full-string match, NOT regex
await Assert.That(() => Act())
    .Throws<InvalidOperationException>()
    .WithMessageMatching("*not allowed*");
```

## Inner Exception

```csharp
await Assert.That(() => Act()).Throws<Exception>().WithInnerException();
```

## Parameter Name

For `ArgumentException` and derived types:

```csharp
await Assert.That(() => Act()).Throws<ArgumentNullException>().WithParameterName("config");
```

## Async Exceptions

Use `async` lambda:

```csharp
await Assert.That(async () => await service.ProcessAsync())
    .Throws<TimeoutException>()
    .WithMessageMatching("*timed out*");
```

## Try/Catch Fallback

When TUnit's fluent API can't express complex exception validation:

```csharp
try
{
    await sink.ProduceAsync(envelope, _ => { }, CancellationToken.None);
    throw new InvalidOperationException("Expected exception not thrown");
}
catch (MessageSerializationException ex)
{
    await Assert.That(ex.Message).Contains("expected text");
    await Assert.That(ex.InnerException).IsTypeOf<JsonException>();
}
```

## Common Mistakes

| Wrong | Correct |
|---|---|
| `Assert.Throws<T>(() => ...)` (xUnit, sync, no await) | `await Assert.That(() => ...).Throws<T>()` |
| `.ThrowsException().With.Message.Containing(...)` | Does NOT exist — use `Throws<T>().WithMessageContaining(...)` |
| `WithMessageMatching(".*regex.*")` | `*` is the only wildcard, NOT regex |
| Forgetting `async` in lambda for async code | `async () => await SomethingAsync()` |
| `Throws<Exception>()` when you want exact type | `ThrowsExactly<Exception>()` for exact match |
