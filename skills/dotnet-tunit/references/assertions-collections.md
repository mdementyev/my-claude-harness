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

**`All()` and `Any()` take `Func<T, bool>` predicates** (not assertion lambdas):

```csharp
await Assert.That(scores).All(x => x > 0);    // every element
await Assert.That(scores).Any(x => x > 90);   // at least one
await Assert.That(items).ContainsOnly(x => x > 0);
```

**Note:** `Count(predicate)` is different — it takes an assertion lambda `Func<IAssertionSource<T>, Assertion<T>?>`. Don't confuse the two.

### All().Satisfy — Assert on Each Item

Two-step pattern for complex per-item assertions (not just predicates):

```csharp
// Assert each user's email contains "@"
await Assert.That(users).All().Satisfy(user => user.Contains("@"));

// With mapping — extract a property, then assert on it
await Assert.That(users).All().Satisfy(
    u => u.Email,                              // map
    email => email.Contains("@")               // assert
);
```

## Count Bounds

```csharp
await Assert.That(items).HasAtLeast(3);
await Assert.That(items).HasAtMost(10);
await Assert.That(items).HasCountBetween(3, 10);
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
using TUnit.Assertions.Enums;

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

## List Index Access

Requires `IList<T>` or `IReadOnlyList<T>` (not just `IEnumerable`):

```csharp
await Assert.That(list).ItemAt(0).IsEqualTo("first");
await Assert.That(list).FirstItem().IsEqualTo("first");
await Assert.That(list).LastItem().IsEqualTo("last");
await Assert.That(list).ItemAt(2).IsNull();
await Assert.That(list).ItemAt(1).Satisfies(x => x.IsGreaterThan(5));

// HasItemAt — assert index exists with specific value in one call
await Assert.That(list).HasItemAt(0, "expected");
```

## Sets

Requires `ISet<T>`, `IReadOnlySet<T>`, or `HashSet<T>`:

```csharp
await Assert.That(subset).IsSubsetOf(superset);
await Assert.That(superset).IsSupersetOf(subset);
await Assert.That(subset).IsProperSubsetOf(superset);    // strict subset (not equal)
await Assert.That(superset).IsProperSupersetOf(subset);

await Assert.That(set1).Overlaps(set2);
await Assert.That(set1).DoesNotOverlap(set2);
await Assert.That(set1).SetEquals(set2);                  // same elements regardless of order
```

## Dictionaries

```csharp
await Assert.That(dict).ContainsKey("myKey");
await Assert.That(dict).DoesNotContainKey("badKey");
await Assert.That(dict).ContainsValue("myValue");
await Assert.That(dict).DoesNotContainValue("badValue");

// Key-value pair — single assertion, NOT a chain
await Assert.That(dict).ContainsKeyWithValue("myKey", "myValue");

// Quantifiers over keys/values
await Assert.That(dict).AllKeys(k => k.StartsWith("prefix"));
await Assert.That(dict).AnyKey(k => k == "special");
await Assert.That(dict).AllValues(v => v > 0);
await Assert.That(dict).AnyValue(v => v > 100);
```

## Common Mistakes

| Wrong | Correct |
|---|---|
| `HasCount().EqualTo(n)` (obsolete) | `.Count().IsEqualTo(n)` |
| `Assert.That(c.Count).IsEqualTo(n)` (works but not idiomatic) | `Assert.That(c).Count().IsEqualTo(n)` |
| `Assert.Single(c)` (xUnit) | `await Assert.That(c).HasSingleItem()` |
| `Assert.Empty(c)` (xUnit) | `await Assert.That(c).IsEmpty()` |
| `Assert.Contains(item, c)` (xUnit, note arg order) | `await Assert.That(c).Contains(item)` |
| `Assert.All(c, x => ...)` (xUnit) | `await Assert.That(c).All(x => ...)` — predicate returns `bool` |
| `.ContainsKey("k").WithValue("v")` (doesn't exist) | `.ContainsKeyWithValue("k", "v")` — single method |
| `Assert.That(list[0]).IsEqualTo("x")` (manual index) | `Assert.That(list).ItemAt(0).IsEqualTo("x")` |
| `.First()` or `.ElementAt(0)` (doesn't exist) | `.FirstItem()` / `.ItemAt(0)` |
| `.HasMinCount(n)` / `.HasMaxCount(n)` (doesn't exist) | `.HasAtLeast(n)` / `.HasAtMost(n)` |
| `.Count().IsGreaterThanOrEqualTo(3)` (verbose) | `.HasAtLeast(3)` |
| `.BeSubsetOf()` (FluentAssertions) | `.IsSubsetOf()` — requires `ISet<T>` or `IReadOnlySet<T>` |
| `.OnlyContain(pred)` (FluentAssertions) | `.ContainsOnly(pred)` or `.All(pred)` |
