# Assertions — JSON

TUnit provides built-in JSON assertions for `string`, `JsonElement`, and `JsonNode`. No manual deserialization needed.

## String — Validity Checks

```csharp
await Assert.That(jsonString).IsValidJson();
await Assert.That(jsonString).IsNotValidJson();
await Assert.That(jsonString).IsValidJsonObject();   // must be { ... }
await Assert.That(jsonString).IsValidJsonArray();    // must be [ ... ]
```

## JsonElement

```csharp
// Type checks
await Assert.That(element).IsObject();
await Assert.That(element).IsArray();
await Assert.That(element).IsString();
await Assert.That(element).IsNumber();
await Assert.That(element).IsBoolean();
await Assert.That(element).IsNull();
await Assert.That(element).IsNotNull();

// Property existence
await Assert.That(element).HasProperty("name");
await Assert.That(element).DoesNotHaveProperty("removed");

// Deep equality — compares entire JSON tree
await Assert.That(actual).IsDeepEqualTo(expected);
await Assert.That(actual).IsNotDeepEqualTo(other);
```

## JsonNode

```csharp
// Type checks
await Assert.That(node).IsJsonObject();
await Assert.That(node).IsJsonArray();
await Assert.That(node).IsJsonValue();

// Array assertions
await Assert.That(node).IsJsonArrayEmpty();
await Assert.That(node).IsJsonArrayNotEmpty();
await Assert.That(node).HasJsonArrayCount(3);

// Property existence
await Assert.That(node).HasJsonProperty("name");
await Assert.That(node).DoesNotHaveJsonProperty("removed");

// Deep equality
await Assert.That(actual).IsDeepEqualTo(expected);
await Assert.That(actual).IsNotDeepEqualTo(other);
```

## Common Mistakes

| Wrong | Correct |
|---|---|
| Manual `JsonSerializer.Deserialize` then assert fields | Use `JsonElement`/`JsonNode` assertions directly |
| `JsonElement` assertions on `JsonNode` (different API) | `HasProperty` (Element) vs `HasJsonProperty` (Node) |
| `IsArray` on a `JsonNode` | `IsJsonArray()` — Node methods have `Json` prefix |
| Checking `element.ValueKind == JsonValueKind.Object` | `await Assert.That(element).IsObject()` |
