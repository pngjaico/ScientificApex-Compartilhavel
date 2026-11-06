#!/usr/bin/env sh
# ScientificApex local source installation. No provider/account setup.
set -eu

clone_root=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
cd "$clone_root"
development=false
verify_only=false
for argument in "$@"; do
    case "$argument" in
        --development) development=true ;;
        --verify-only) verify_only=true ;;
        *) printf 'Unknown option: %s\n' "$argument" >&2; exit 2 ;;
    esac
done

if [ "$verify_only" = false ]; then
    command -v uv >/dev/null 2>&1 || {
        printf '%s\n' 'Install uv: https://docs.astral.sh/uv/getting-started/installation/' >&2
        exit 1
    }
    if [ "$development" = true ]; then
        uv sync --locked --python 3.13
    else
        uv sync --locked --python 3.13 --no-dev
    fi
fi

python_executable="$clone_root/.venv/bin/python"
[ -x "$python_executable" ] || {
    printf '%s\n' 'Missing .venv/bin/python. Run bash instalar.sh first.' >&2
    exit 1
}
mkdir -p .machine/verification
"$python_executable" -m article_machine --help > .machine/verification/cli.txt
"$python_executable" -m article_machine machine audit --workspace-root . --strict > .machine/verification/auditoria.json
printf '%s\n' 'PASS: core CLI and strict operational audit.' 'Read AGENTS.md and the usage guide; use the CLI or your preferred agent.'
