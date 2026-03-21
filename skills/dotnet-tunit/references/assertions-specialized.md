# Assertions — Specialized Types

## DateTime

```csharp
// Tolerance
await Assert.That(actual).IsEqualTo(expected).Within(TimeSpan.FromSeconds(1));

// Relative checks
await Assert.That(timestamp).IsAfter(cutoff);
await Assert.That(timestamp).IsBefore(deadline);
await Assert.That(timestamp).IsToday();
await Assert.That(timestamp).IsUtc();
await Assert.That(timestamp).IsInFuture();
await Assert.That(timestamp).IsInPast();
```

## Regex (Advanced)

Basic `.Matches("pattern")` is in `assertions-strings.md`. Advanced features:

```csharp
// Named groups
await Assert.That("John-42").Matches(@"(?<name>\w+)-(?<age>\d+)")
    .Group("name", g => g.IsEqualTo("John"))
    .Group("age", g => g.IsEqualTo("42"));

// Indexed groups (0 = full match, 1+ = captures)
await Assert.That("2024-03-21").Matches(@"(\d{4})-(\d{2})-(\d{2})")
    .Group(1, g => g.IsEqualTo("2024"));

// Multiple matches
await Assert.That("aaa bbb ccc").Matches(@"\w+")
    .Match(0, m => m.IsEqualTo("aaa"))
    .Match(2, m => m.IsEqualTo("ccc"));
```

## Task

```csharp
await Assert.That(task).IsCompleted();
await Assert.That(task).IsCanceled();              // note: one 'l'
await Assert.That(task).IsFaulted();
await Assert.That(task).IsCompletedSuccessfully();
```

Timeout assertion — called on a **delegate**, not a Task:

```csharp
await Assert.That(async () => await LongOperation())
    .CompletesWithin(TimeSpan.FromSeconds(5));
```

## Polling / Waiting

Repeatedly evaluates a lambda until a condition is met or timeout:

```csharp
await Assert.That(() => condition)
    .WaitsFor(c => c == true, timeout: TimeSpan.FromSeconds(2));
```

The lambda `() => condition` is **re-evaluated on each poll** — it's not captured once.

## GUID

```csharp
await Assert.That(id).IsNotEmptyGuid();
await Assert.That(Guid.Empty).IsEmptyGuid();
```

## CancellationToken

```csharp
await Assert.That(token).IsCancellationRequested();      // NOT .IsCancelled
await Assert.That(token).IsNotCancellationRequested();
await Assert.That(token).CanBeCanceled();
await Assert.That(token).IsNone();                        // CancellationToken.None
```

## Member Assertions

Assert on object properties with `.Member().Satisfies()`:

```csharp
await Assert.That(user)
    .Member(x => x.Name).Satisfies(val => val.IsEqualTo("Alice"))
    .And.Member(x => x.Age).Satisfies(val => val.IsGreaterThan(0));
```

## Character

```csharp
await Assert.That(ch).IsLetter();
await Assert.That(ch).IsDigit();
await Assert.That(ch).IsWhiteSpace();
await Assert.That(ch).IsUpper();
await Assert.That(ch).IsLower();
await Assert.That(ch).IsPunctuation();
```

## Stream

```csharp
await Assert.That(stream).CanRead();
await Assert.That(stream).CanWrite();
await Assert.That(stream).CanSeek();
```
