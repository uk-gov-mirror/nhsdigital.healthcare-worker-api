#!/usr/bin/env bash

set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(git -C "$script_dir" rev-parse --show-toplevel)"
cd "$repo_root"

status=0
version_comment_pattern='#[[:space:]]+[^[:space:]]'

while IFS= read -r file; do
  while IFS= read -r match; do
    line_number=${match%%:*}
    line=${match#*:}
    ref=$(printf '%s\n' "$line" | sed -E 's/^[[:space:]]*(-[[:space:]]+)?uses:[[:space:]]+([^[:space:]]+).*/\2/')

    if [[ "$ref" == ./* || "$ref" == docker://* ]]; then
      continue
    fi

    if [[ ! "$ref" =~ ^[A-Za-z0-9._-]+/[A-Za-z0-9._-]+(/[^@[:space:]]+)?@[A-Fa-f0-9]{40}$ ]]; then
      echo "$file:$line_number external action is not pinned to a full commit SHA: $line"
      status=1
      continue
    fi

    if [[ ! "$line" =~ $version_comment_pattern ]]; then
      echo "$file:$line_number pinned action is missing an inline version comment: $line"
      status=1
    fi
  done < <(grep -nE '^[[:space:]]*(-[[:space:]]+)?uses:[[:space:]]+' "$file" || true)
done < <(find .github/workflows .github/actions -type f \( -name '*.yml' -o -name '*.yaml' \) | sort)

exit "$status"
