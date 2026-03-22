# Assertions — Strings

## Substring Checks

```csharp
await Assert.That(str).Contains("world");
await Assert.That(str).DoesNotContain("forbidden");
await Assert.That(str).StartsWith("Hello");
await Assert.That(str).DoesNotStartWith("Bad");
await Assert.That(str).EndsWith("!");
await Assert.That(str).DoesNotEndWith("?");
await Assert.That(str).Matches(@"\d+");
await Assert.That(str).DoesNotMatch(@"\d+");
```

## Case Insensitivity

`.IgnoringCase()` works on Contains, StartsWith, EndsWith, Matches, and IsEqualTo:

```csharp
await Assert.That(name).Contains("alice").IgnoringCase();
await Assert.That(name).IsEqualTo("ALICE").IgnoringCase();
```

For explicit control:

```csharp
await Assert.That(name).IsEqualTo("alice").WithComparison(StringComparison.OrdinalIgnoreCase);
```

## Whitespace Handling

`.WithTrimming()` and `.IgnoringWhitespace()` work on Contains and IsEqualTo:

```csharp
await Assert.That(input).IsEqualTo("hello").WithTrimming();           // trims before comparing
await Assert.That(input).IsEqualTo("hello world").IgnoringWhitespace(); // normalizes internal whitespace
```

## Length

```csharp
await Assert.That(str).Length().IsEqualTo(5);
await Assert.That(str).Length().IsGreaterThan(0);
```

## Regex Matching

Basic pattern matching. For advanced regex features (groups, match indexing), see `assertions-specialized.md`:

```csharp
await Assert.That(email).Matches(@"^[\w.]+@[\w.]+\.\w+$");
await Assert.That(code).Matches("[A-Z]{3}-\\d{4}").IgnoringCase();
```

## String Parsing

Test string-to-type conversions. Target type must support `IParsable<T>`:

```csharp
await Assert.That("123").WhenParsedInto<int>().IsEqualTo(123);
await Assert.That("3.14").WhenParsedInto<double>().IsPositive();
await Assert.That("true").WhenParsedInto<bool>().IsTrue();
```

Optional `IFormatProvider` parameter for culture-specific parsing.

## Empty and Null Checks

```csharp
await Assert.That(str).IsEmpty();
await Assert.That(str).IsNotEmpty();
await Assert.That(str).IsNullOrEmpty();
await Assert.That(str).IsNotNullOrEmpty();
await Assert.That(str).IsNullOrWhiteSpace();    // note capital S
await Assert.That(str).IsNotNullOrWhiteSpace();
```

## Common Mistakes

| Wrong (xUnit) | Correct (TUnit) |
|---|---|
| `Assert.Contains("x", str)` (note arg order) | `await Assert.That(str).Contains("x")` |
| `Assert.StartsWith("prefix", str)` | `await Assert.That(str).StartsWith("prefix")` |
| `Assert.Empty(str)` | `await Assert.That(str).IsEmpty()` |
| `Assert.Matches(pattern, str)` | `await Assert.That(str).Matches(pattern)` |
| `IsNullOrWhitespace` (lowercase s) | `IsNullOrWhiteSpace` (capital S) |
| `.NotStartsWith()` / `.NotContain()` | `.DoesNotStartWith()` / `.DoesNotContain()` — always `DoesNot` prefix |
