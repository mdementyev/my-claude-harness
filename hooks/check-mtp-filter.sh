#!/usr/bin/env bash
# PreToolUse hook: block common VSTest habits that silently fail under MTP.
# 1. --filter (MTP uses --treenode-filter; --filter silently matches zero tests)
# 2. Positional .csproj/.sln/.slnx args (MTP requires --project / --solution flags)

set -euo pipefail

input=$(cat)
command=$(echo "$input" | jq -r '.tool_input.command // ""')

# Detect violations
violation=""

if echo "$command" | grep -qE 'dotnet\s+test\s.*--filter\s'; then
  violation="filter"
elif echo "$command" | grep -qE 'dotnet\s+test\s' && \
     echo "$command" | grep -qE '\S+\.(csproj|sln|slnx)(\s|$)' && \
     ! echo "$command" | grep -qE -- '--(project|solution)\s+\S+\.(csproj|sln|slnx)'; then
  violation="positional"
fi

if [ -z "$violation" ]; then
  exit 0
fi

# Walk up from cwd looking for global.json with MTP test runner
dir="$PWD"
while [ "$dir" != "/" ]; do
  if [ -f "$dir/global.json" ]; then
    if jq -e '.test.runner == "Microsoft.Testing.Platform"' "$dir/global.json" > /dev/null 2>&1; then
      if [ "$violation" = "filter" ]; then
        cat <<'EOF'
{
  "decision": "block",
  "reason": "--filter does not work with Microsoft Testing Platform (MTP). This project uses MTP (see global.json). Use --treenode-filter instead.\n\nThe test tree has four levels: /Assembly/Namespace/Class/Method\n\n  All tests in a class:  /*/*/MyClassName/*\n  Single test method:    /*/*/MyClassName/MyMethodName\n  Tests by property:     /**[Category=Integration]\n  Namespace subtree:     /*/MyNamespace*/**\n\nExample: dotnet test --treenode-filter \"/*/*/CircuitBreakerTests/*\"\n\nInvoke the dotnet-mtp skill for complete filtering reference."
}
EOF
      else
        cat <<'EOF'
{
  "decision": "block",
  "reason": "Positional project/solution arguments don't work with Microsoft Testing Platform (MTP). This project uses MTP (see global.json). Use --project or --solution flags instead.\n\n  WRONG:   dotnet test MyProject.csproj\n  CORRECT: dotnet test --project MyProject.csproj\n\n  WRONG:   dotnet test MySolution.sln\n  CORRECT: dotnet test --solution MySolution.sln\n\n  WRONG:   dotnet test MySolution.slnx\n  CORRECT: dotnet test --solution MySolution.slnx\n\nInvoke the dotnet-mtp skill for complete MTP CLI reference."
}
EOF
      fi
      exit 0
    fi
    break
  fi
  dir=$(dirname "$dir")
done
