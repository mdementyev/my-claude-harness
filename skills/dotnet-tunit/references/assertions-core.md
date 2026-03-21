# Assertions — Core Mechanics

## The Async Rule

Every assertion MUST be awaited:

```csharp
// CORRECT
await Assert.That(value).IsEqualTo(expected);

// WRONG — compiles but silently skips the assertion
Assert.That(value).IsEqualTo(expected); // no await!
```

Missing `await` means the test passes without checking anything.

## Chaining with .And

Chain multiple conditions on the same value. Single `await`, all conditions evaluated:

```csharp
await Assert.That(name)
    .IsNotNull()
    .And.StartsWith("A")
    .And.Contains("li");
```

## Chaining with .Or

Pass if any condition holds:

```csharp
await Assert.That(status)
    .IsEqualTo("active")
    .Or.IsEqualTo("pending");
```

**Do NOT mix `.And` and `.Or` in the same chain** — TUnit's analyzer will warn. Use `Assert.Multiple` instead.

## Assert.Multiple

Groups independent assertions and reports all failures (not just the first):

```csharp
// Implicit scope — rest of method
using var _ = Assert.Multiple();
await Assert.That(user.Name).IsEqualTo("Alice");
await Assert.That(user.Age).IsPositive();
await Assert.That(user.Email).Contains("@");

// Explicit scope — block only
using (Assert.Multiple())
{
    await Assert.That(name).IsNotNull();
    await Assert.That(age).IsPositive();
}
```

## Assertion Return Values

Some assertions return typed values for further use:

```csharp
// HasSingleItem returns the single item
var item = await Assert.That(list).HasSingleItem();
await Assert.That(item.Name).IsEqualTo("expected");

// IsTypeOf<T> returns the cast value
var typed = await Assert.That(obj).IsTypeOf<MyClass>();
await Assert.That(typed.Name).IsEqualTo("expected");

// Contains(predicate) returns the matched item
var found = await Assert.That(users).Contains(u => u.Name == "Alice");
await Assert.That(found.Age).IsGreaterThan(0);
```

## Common Mistakes

| Wrong | Correct |
|---|---|
| `Assert.That(x).IsEqualTo(y);` (no await) | `await Assert.That(x).IsEqualTo(y);` |
| `Assert.Equal(expected, actual)` (xUnit) | `await Assert.That(actual).IsEqualTo(expected)` |
| `Assert.Throws<T>(() => ...)` (xUnit) | `await Assert.That(act).Throws<T>()` |
| Mixing `.And` and `.Or` in same chain | Use `Assert.Multiple` for independent assertions |
| `Assert.That(expected).IsEqualTo(actual)` (reversed) | `Assert.That(actual).IsEqualTo(expected)` |
