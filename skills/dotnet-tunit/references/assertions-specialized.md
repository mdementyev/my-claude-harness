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

### Eventually — Retry Assertion Until Timeout

Repeatedly re-evaluates a `Func<T>` and retries the assertion until it passes or times out. Use instead of manual polling loops:

```csharp
// Re-evaluates GetStatus() until it returns "ready" or 5s elapses
await Assert.That(() => GetStatus())
    .Eventually(s => s.IsEqualTo("ready"), TimeSpan.FromSeconds(5));

// With custom poll interval (default is 500ms)
await Assert.That(() => GetCount())
    .Eventually(c => c.IsGreaterThan(0), TimeSpan.FromSeconds(10), TimeSpan.FromMilliseconds(100));
```

### WaitsFor — Same Purpose, Extension Method Syntax

```csharp
await Assert.That(() => condition)
    .WaitsFor(c => c.IsTrue(), timeout: TimeSpan.FromSeconds(2));
```

Both `Eventually` and `WaitsFor` **re-evaluate the lambda on each poll** — it's not captured once.

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

## Satisfies with Mapping

Extract a property or transform a value, then assert on the result — all in one chain:

```csharp
// Map then assert with predicate
await Assert.That(response).Satisfies(r => r.StatusCode == 200);

// Map to a new value, then chain assertions on it
await Assert.That(user)
    .Satisfies(u => u.Email, email => email.Contains("@"));
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
