# Assertions — Values

## Equality

```csharp
await Assert.That(actual).IsEqualTo(expected);
await Assert.That(actual).IsNotEqualTo(other);
await Assert.That(obj1).IsSameReferenceAs(obj2); // reference equality
```

## Comparison

```csharp
await Assert.That(count).IsGreaterThan(0);
await Assert.That(count).IsGreaterThanOrEqualTo(1);
await Assert.That(value).IsLessThan(100);
await Assert.That(value).IsLessThanOrEqualTo(99);
await Assert.That(value).IsBetween(1, 10);
```

## Null and Default

```csharp
await Assert.That(obj).IsNull();
await Assert.That(obj).IsNotNull();
await Assert.That(value).IsDefault();    // value types: default(T), reference types: null
await Assert.That(value).IsNotDefault();
```

## Boolean

```csharp
await Assert.That(flag).IsTrue();
await Assert.That(flag).IsFalse();
```

## Numeric

```csharp
await Assert.That(count).IsPositive();
await Assert.That(loss).IsNegative();
await Assert.That(balance).IsZero();
await Assert.That(count).IsNotZero();
```

### Floating-Point Tolerance

```csharp
await Assert.That(1.0 / 3.0).IsEqualTo(0.333).Within(0.001);    // double
await Assert.That(price).IsEqualTo(9.99m).Within(0.01m);          // decimal
await Assert.That(ratio).IsEqualTo(0.5f).Within(0.01f);           // float
```

## Type Checking

```csharp
// IsTypeOf returns the cast value for further assertions
var typed = await Assert.That(obj).IsTypeOf<MyClass>();
await Assert.That(typed.Name).IsEqualTo("expected");

await Assert.That(obj).IsAssignableTo<IMyInterface>();
```

## Custom Equality

Use `.Using()` with an `IEqualityComparer<T>` or a predicate:

```csharp
// With IEqualityComparer<T>
await Assert.That(people1)
    .IsEquivalentTo(people2)
    .Using(new PersonNameComparer());

// With predicate
await Assert.That(people1)
    .IsEquivalentTo(people2)
    .Using((p1, p2) => string.Equals(p1.Name, p2.Name,
                        StringComparison.OrdinalIgnoreCase));
```

## Common Mistakes

| Wrong (xUnit) | Correct (TUnit) |
|---|---|
| `Assert.Null(x)` | `await Assert.That(x).IsNull()` |
| `Assert.NotNull(x)` | `await Assert.That(x).IsNotNull()` |
| `Assert.True(x)` | `await Assert.That(x).IsTrue()` |
| `Assert.IsType<T>(x)` | `await Assert.That(x).IsTypeOf<T>()` |
| `Assert.IsAssignableFrom<T>(x)` | `await Assert.That(x).IsAssignableTo<T>()` |
| `Assert.Equal(expected, actual)` | `await Assert.That(actual).IsEqualTo(expected)` |
| `Assert.InRange(val, lo, hi)` | `await Assert.That(val).IsBetween(lo, hi)` |
