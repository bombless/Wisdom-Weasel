#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SNIPPET_FILE="${SCRIPT_DIR}/rime/wisdom_predictor.lua.snippet"

RIME_DIR="${HOME}/.local/share/fcitx5/rime"
SCHEMA_ID="luna_pinyin_simp"
ENDPOINT="http://127.0.0.1:8000/v1/generate/completions"
TIMEOUT_MS=800
MIN_INPUT_LENGTH=2
SKIP_BUILD=0

usage() {
  cat <<'EOF'
Usage:
  ./fcitx5/install_fcitx5_adapter.sh [options]

Options:
  --schema <schema_id>        Target schema id (default: luna_pinyin_simp)
  --rime-dir <path>           Rime user data dir (default: ~/.local/share/fcitx5/rime)
  --endpoint <url>            hf_backend API endpoint
  --timeout-ms <int>          Request timeout in milliseconds (default: 800)
  --min-input-length <int>    Trigger LLM when input length reaches this value (default: 2)
  --skip-build                Do not run rime_deployer --build
  -h, --help                  Show this help
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --schema)
      SCHEMA_ID="${2:-}"
      shift 2
      ;;
    --rime-dir)
      RIME_DIR="${2:-}"
      shift 2
      ;;
    --endpoint)
      ENDPOINT="${2:-}"
      shift 2
      ;;
    --timeout-ms)
      TIMEOUT_MS="${2:-}"
      shift 2
      ;;
    --min-input-length)
      MIN_INPUT_LENGTH="${2:-}"
      shift 2
      ;;
    --skip-build)
      SKIP_BUILD=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

if [[ ! -f "${SNIPPET_FILE}" ]]; then
  echo "Missing snippet file: ${SNIPPET_FILE}" >&2
  exit 1
fi

if ! command -v rime_deployer >/dev/null 2>&1; then
  echo "rime_deployer is required but not found." >&2
  exit 1
fi

if ! command -v curl >/dev/null 2>&1; then
  echo "curl is required but not found." >&2
  exit 1
fi

mkdir -p "${RIME_DIR}"

timestamp="$(date +%Y%m%d%H%M%S)"
rime_lua="${RIME_DIR}/rime.lua"
schema_custom="${RIME_DIR}/${SCHEMA_ID}.custom.yaml"

backup_if_exists() {
  local path="$1"
  if [[ -f "${path}" ]]; then
    cp -a "${path}" "${path}.bak.${timestamp}"
  fi
}

append_lua_snippet() {
  if [[ ! -f "${rime_lua}" ]]; then
    cp "${SNIPPET_FILE}" "${rime_lua}"
    return
  fi

  if grep -q "function wisdom_predictor" "${rime_lua}"; then
    return
  fi

  backup_if_exists "${rime_lua}"
  {
    printf '\n\n'
    cat "${SNIPPET_FILE}"
    printf '\n'
  } >> "${rime_lua}"
}

write_or_patch_custom_yaml() {
  local patch_block
  patch_block="$(cat <<EOF
  # Wisdom-Weasel fcitx5 adapter
  "engine/translators/+":
    - lua_translator@wisdom_predictor
  "wisdom_predictor/endpoint": "${ENDPOINT}"
  "wisdom_predictor/timeout_ms": ${TIMEOUT_MS}
  "wisdom_predictor/min_input_length": ${MIN_INPUT_LENGTH}
EOF
)"

  if [[ ! -f "${schema_custom}" ]]; then
    cat > "${schema_custom}" <<EOF
patch:
${patch_block}
EOF
    return
  fi

  if grep -q "lua_translator@wisdom_predictor" "${schema_custom}"; then
    return
  fi

  backup_if_exists "${schema_custom}"
  if grep -q '^patch:' "${schema_custom}"; then
    {
      printf '\n'
      printf '%s\n' "${patch_block}"
      printf '\n'
    } >> "${schema_custom}"
  else
    {
      printf '\npatch:\n'
      printf '%s\n' "${patch_block}"
      printf '\n'
    } >> "${schema_custom}"
  fi
}

append_lua_snippet
write_or_patch_custom_yaml

if [[ "${SKIP_BUILD}" -eq 0 ]]; then
  mkdir -p "${RIME_DIR}/build"
  rime_deployer --build "${RIME_DIR}" "/usr/share/rime-data" "${RIME_DIR}/build" >/dev/null
fi

echo "fcitx5 adapter installed."
echo "schema: ${SCHEMA_ID}"
echo "rime_dir: ${RIME_DIR}"
echo "endpoint: ${ENDPOINT}"
echo "next: restart fcitx5 (or run 'fcitx5-remote -r')."
