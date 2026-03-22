# Assertions — HttpResponseMessage

TUnit provides built-in assertions for `HttpResponseMessage` and `HttpStatusCode`. No manual status code checking needed.

## Status Code — Named Assertions

```csharp
await Assert.That(response).IsOk();                    // 200
await Assert.That(response).IsCreated();               // 201
await Assert.That(response).IsNoContent();             // 204
await Assert.That(response).IsBadRequest();            // 400
await Assert.That(response).IsUnauthorized();          // 401
await Assert.That(response).IsForbidden();             // 403
await Assert.That(response).IsNotFound();              // 404
await Assert.That(response).IsConflict();              // 409
```

## Status Code — Category Assertions

```csharp
await Assert.That(response).IsSuccessStatusCode();        // 2xx
await Assert.That(response).IsNotSuccessStatusCode();     // NOT 2xx
await Assert.That(response).IsClientErrorStatusCode();    // 4xx
await Assert.That(response).IsServerErrorStatusCode();    // 5xx
await Assert.That(response).IsRedirectStatusCode();       // 3xx
```

## Status Code — Arbitrary

```csharp
await Assert.That(response).HasStatusCode(HttpStatusCode.Accepted);          // 202
await Assert.That(response).HasStatusCode(HttpStatusCode.TooManyRequests);   // 429
```

## Content and Headers

```csharp
await Assert.That(response).HasJsonContent();              // Content-Type is application/json
await Assert.That(response).HasContentType("text/plain");
await Assert.That(response).HasHeader("X-Request-Id");
```

## HttpStatusCode (Standalone)

When you have a status code value directly:

```csharp
await Assert.That(statusCode).IsSuccess();          // 2xx
await Assert.That(statusCode).IsClientError();      // 4xx
await Assert.That(statusCode).IsServerError();      // 5xx
await Assert.That(statusCode).IsRedirection();      // 3xx
await Assert.That(statusCode).IsInformational();    // 1xx
await Assert.That(statusCode).IsError();            // 4xx or 5xx
await Assert.That(statusCode).IsNotSuccess();       // NOT 2xx
```

## Common Mistakes

| Wrong | Correct |
|---|---|
| `Assert.That(response.StatusCode).IsEqualTo(HttpStatusCode.OK)` | `Assert.That(response).IsOk()` |
| `Assert.That(response.IsSuccessStatusCode).IsTrue()` | `Assert.That(response).IsSuccessStatusCode()` |
| `response.EnsureSuccessStatusCode()` in test | `await Assert.That(response).IsSuccessStatusCode()` — better failure messages |
| Manual Content-Type header check | `await Assert.That(response).HasJsonContent()` |
