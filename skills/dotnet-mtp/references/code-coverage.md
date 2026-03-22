# Code Coverage

MTP uses `Microsoft.Testing.Extensions.CodeCoverage` — NOT the VSTest `--collect` mechanism. TUnit and MSTest 3.x+ include this as a transitive dependency, so `--coverage` typically works out of the box.

If the `--coverage` flag doesn't appear in `dotnet test --help` output, add the package explicitly:

```xml
<PackageReference Include="Microsoft.Testing.Extensions.CodeCoverage" />
```

## Collecting Coverage

```bash
dotnet test --project tests/MyTests.csproj \
  --coverage \
  --coverage-output-format cobertura \
  --coverage-output coverage.cobertura.xml
```

| Flag | Purpose |
|---|---|
| `--coverage` | Enable collection (required) |
| `--coverage-output-format` | `coverage` (default binary), `xml`, or `cobertura` |
| `--coverage-output` | Output filename. Relative to `--results-directory` if just a filename |
| `--coverage-settings` | Path to XML settings file for exclusions |

**Output location:** By default, the coverage file lands in `<test-project>/bin/Debug/<tfm>/TestResults/`. Use `--results-directory` to override.

For solution-level collection:

```bash
dotnet test --solution MySolution.sln \
  --coverage \
  --coverage-output-format cobertura \
  --coverage-output coverage.cobertura.xml
```

## Generating Reports

Use ReportGenerator via `dnx` (.NET 10+, no global install needed):

```bash
# Quick summary — coverage rates per assembly and class
dnx -y dotnet-reportgenerator-globaltool -- \
  -reports:coverage.cobertura.xml \
  -targetdir:CoverageReport \
  -reporttypes:TextSummary
cat CoverageReport/Summary.txt

# HTML report — per-file line highlighting showing covered/uncovered code
dnx -y dotnet-reportgenerator-globaltool -- \
  -reports:coverage.cobertura.xml \
  -targetdir:CoverageReport \
  -reporttypes:Html
# Open CoverageReport/index.html in browser
```

The `--` separator is required to forward `-` prefixed arguments to ReportGenerator. `-y` auto-accepts the NuGet download prompt.

### Reading the Summary

The TextSummary shows:
- **Line coverage** — percentage of executable lines hit
- **Branch coverage** — percentage of conditional branches taken
- **Method coverage** — percentage of methods entered
- Per-class breakdown with individual percentages

### Finding Uncovered Code

Use the HTML report (`-reporttypes:Html`). It highlights each source file:
- **Green lines** — covered by tests
- **Red lines** — not covered
- **Yellow lines** — partially covered (some branches not taken)

Navigate to low-coverage classes in the summary table, then click through to see exact uncovered lines.

## Excluding from Coverage

MTP excludes test assemblies by default (unlike VSTest where `IncludeTestAssembly` was `true`).

### Via Settings File

Create a coverage settings XML file and pass it with `--coverage-settings`:

```xml
<!-- coverage.settings.xml -->
<Configuration>
  <CodeCoverage>
    <ModulePathsExclude>
      <ModulePath>.*\.Tests\.dll$</ModulePath>
    </ModulePathsExclude>
    <FunctionsExclude>
      <Function>.*GeneratedCode.*</Function>
    </FunctionsExclude>
  </CodeCoverage>
</Configuration>
```

```bash
dotnet test --project tests/MyTests.csproj \
  --coverage \
  --coverage-output-format cobertura \
  --coverage-settings coverage.settings.xml
```

### Via Attribute

Mark classes or methods to exclude:

```csharp
[System.Diagnostics.CodeAnalysis.ExcludeFromCodeCoverage]
public class GeneratedBoilerplate { }
```

## Common Mistakes

| Wrong | Correct | Why |
|---|---|---|
| `--collect "XPlat Code Coverage"` | `--coverage` | VSTest syntax, not MTP |
| `coverlet.collector` package | `Microsoft.Testing.Extensions.CodeCoverage` | `coverlet.collector` uses VSTest data collector, not MTP |
| No `--coverage-output-format` | `--coverage-output-format cobertura` | Default is `.coverage` binary, not human-readable |
| `dnx -y pkg -reports:...` | `dnx -y pkg -- -reports:...` | `--` separator needed to forward `-` args to the tool |
