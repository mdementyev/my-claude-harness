# Assertions — Collections

## Count

```csharp
await Assert.That(items).Count().IsEqualTo(3);
await Assert.That(items).Count().IsGreaterThan(0);
```

Count with inner assertions — count elements matching a condition:

```csharp
// Count of items where value > 5
await Assert.That(items).Count(x => x.IsGreaterThan(5)).IsEqualTo(3);
```

**Gotcha:** `HasCount().EqualTo(n)` is obsolete. `Assert.That(c.Count).IsEqualTo(n)` works but `.Count().IsEqualTo(n)` is the idiomatic TUnit way.

## Empty

```csharp
await Assert.That(list).IsEmpty();
await Assert.That(list).IsNotEmpty();
```

## Contains

```csharp
await Assert.That(list).Contains(42);
await Assert.That(list).DoesNotContain(99);
```

Predicate overload returns the matched item:

```csharp
var found = await Assert.That(users).Contains(u => u.Name == "Alice");
await Assert.That(found.Age).IsGreaterThan(0);
```

## All / Any

```csharp
await Assert.That(scores).All(x => x.IsGreaterThan(0));   // every element
await Assert.That(scores).Any(x => x.IsGreaterThan(90));   // at least one
```

## Single Item

Returns the single item for further assertions:

```csharp
var item = await Assert.That(list).HasSingleItem();
await Assert.That(item.Name).IsEqualTo("only-one");
```

## Ordering

```csharp
await Assert.That(numbers).IsInOrder();           // ascending
await Assert.That(numbers).IsInDescendingOrder();

// By property
await Assert.That(users).IsOrderedBy(u => u.Name);
await Assert.That(users).IsOrderedByDescending(u => u.Age);
```

## Equivalency

Order-agnostic by default:

```csharp
await Assert.That(actual).IsEquivalentTo(expected);
```

Require matching order:

```csharp
await Assert.That(actual).IsEquivalentTo(expected, CollectionOrdering.Matching);
```

With custom comparer:

```csharp
await Assert.That(actual).IsEquivalentTo(expected).Using(comparer);
await Assert.That(actual).IsEquivalentTo(expected)
    .Using((a, b) => string.Equals(a.Name, b.Name, StringComparison.OrdinalIgnoreCase));
```

## Distinctness

```csharp
await Assert.That(items).HasDistinctItems();
await Assert.That(items).HasDistinctItems(customComparer); // with IEqualityComparer<T>
```

## Dictionaries

```csharp
await Assert.That(dict).ContainsKey("myKey");
await Assert.That(dict).DoesNotContainKey("badKey");
await Assert.That(dict).ContainsValue("myValue");
await Assert.That(dict).DoesNotContainValue("badValue");
```

## Common Mistakes

| Wrong | Correct |
|---|---|
| `HasCount().EqualTo(n)` (obsolete) | `.Count().IsEqualTo(n)` |
| `Assert.That(c.Count).IsEqualTo(n)` (works but not idiomatic) | `Assert.That(c).Count().IsEqualTo(n)` |
| `Assert.Single(c)` (xUnit) | `await Assert.That(c).HasSingleItem()` |
| `Assert.Empty(c)` (xUnit) | `await Assert.That(c).IsEmpty()` |
| `Assert.Contains(item, c)` (xUnit, note arg order) | `await Assert.That(c).Contains(item)` |
| `Assert.All(c, x => ...)` (xUnit) | `await Assert.That(c).All(x => ...)` |
