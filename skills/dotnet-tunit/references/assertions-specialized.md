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
// Named groups — chain through .And
await Assert.That("John-42").Matches(@"(?<name>\w+)-(?<age>\d+)")
    .And.Group("name", g => g.IsEqualTo("John"))
    .And.Group("age", g => g.IsEqualTo("42"));

// Indexed groups (0 = full match, 1+ = captures)
await Assert.That("2024-03-21").Matches(@"(\d{4})-(\d{2})-(\d{2})")
    .And.Group(1, g => g.IsEqualTo("2024"));

// Multiple matches — Match() lambda receives RegexMatch, not string
await Assert.That("aaa bbb ccc").Matches(@"\w+")
    .And.Match(0, m => m.Member(r => r.Value, v => v.IsEqualTo("aaa")))
    .And.Match(2, m => m.Member(r => r.Value, v => v.IsEqualTo("ccc")));
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

### WaitsFor — Retry Assertion Until Timeout

Repeatedly re-evaluates a `Func<T>` and retries the assertion until it passes or times out. Use instead of manual polling loops:

```csharp
// Re-evaluates GetStatus() until it returns "ready" or 5s elapses
await Assert.That(() => GetStatus())
    .WaitsFor(s => s.IsEqualTo("ready"), TimeSpan.FromSeconds(5));

// With custom poll interval (default is 500ms)
await Assert.That(() => GetCount())
    .WaitsFor(c => c.IsGreaterThan(0), TimeSpan.FromSeconds(10), TimeSpan.FromMilliseconds(100));
```

`WaitsFor` **re-evaluate the lambda on each poll** — it's not captured once.

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

Assert on object properties with `.Member(selector, assertion)` — two arguments, no `.Satisfies()`:

```csharp
await Assert.That(user)
    .Member(x => x.Name, val => val.IsEqualTo("Alice"))
    .And.Member(x => x.Age, val => val.IsGreaterThan(0));
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

If using a derived stream type (e.g. `MemoryStream`), cast to `Stream` first — the extension methods are defined on `IAssertionSource<Stream>`:

```csharp
await Assert.That((Stream)stream).CanRead();
await Assert.That((Stream)stream).CanWrite();
await Assert.That((Stream)stream).CanSeek();
```
