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

# Detailed report — per-file line coverage with source code
dnx -y dotnet-reportgenerator-globaltool -- \
  -reports:coverage.cobertura.xml \
  -targetdir:CoverageReport \
  -reporttypes:Markdown
cat CoverageReport/Summary.md
```

The `--` separator is required to forward `-` prefixed arguments to ReportGenerator. `-y` auto-accepts the NuGet download prompt.

### Reading the Summary

The TextSummary shows:
- **Line coverage** — percentage of executable lines hit
- **Branch coverage** — percentage of conditional branches taken
- **Method coverage** — percentage of methods entered
- Per-class breakdown with individual percentages

### Finding Uncovered Code

Use the Markdown report (`-reporttypes:Markdown`). It produces a single file with inline source code and coverage markers:
- **`✔` with visit count** — line is covered (e.g. `✔  3` means 3 test visits)
- **`❌ 0`** — line is not covered
- **No marker** — line is not coverable (declarations, comments, braces)

The report also includes a **Risk Hotspots** table ranking methods by CRAP score (high complexity + low coverage), and per-class method metrics with branch/line coverage percentages.

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
| `-reporttypes:Html` | `-reporttypes:Markdown` | Html produces ~7x more data across many files; Markdown is a single file with the same line-level detail |
