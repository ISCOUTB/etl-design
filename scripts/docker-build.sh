#!/bin/bash
set -euo pipefail

usage() {
    cat <<EOF
Usage: $(basename "$0") -f <dockerfile> [OPTIONS] [-- extra docker args]

Required:
  -f, --file <path>         Path to the Dockerfile (relative to workspace root)

Optional:
  -t, --tag <image:tag>     Image tag (can be repeated for multiple tags)
  -c, --context <path>      Build context path (default: .)
  -p, --push                Push the image after building (multi-arch)
      --platform <list>     Comma-separated platforms
                            (default without --push: linux/amd64)
                            (default with    --push: linux/amd64,linux/arm64)
  -v, --verbose             Show buildx builder bootstrap output
  -h, --help                Show this help

Notes:
  - Without --push, the image is built with --load (single platform, available locally).
  - With --push,    the image is built with --push (multi-platform, sent to registry).
  - Pass extra docker buildx args after '--', e.g.: -- --no-cache
EOF
    exit 1
}

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# ── defaults ────────────────────────────────────────────────────────────────
DOCKERFILE=""
CONTEXT="."
TAGS=()
PUSH=false
PLATFORM=""   # resolved after parsing, depends on --push
VERBOSE=false
EXTRA_ARGS=()

# ── parse args ───────────────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
    case "$1" in
        -f|--file)
            DOCKERFILE="$2"; shift 2 ;;
        -t|--tag)
            TAGS+=("$2"); shift 2 ;;
        -c|--context)
            CONTEXT="$2"; shift 2 ;;
        -p|--push)
            PUSH=true; shift ;;
        --platform)
            PLATFORM="$2"; shift 2 ;;
        -v|--verbose)
            VERBOSE=true; shift ;;
        -h|--help)
            usage ;;
        --)
            shift; EXTRA_ARGS=("$@"); break ;;
        *)
            echo "Unknown argument: $1" >&2; usage ;;
    esac
done

# ── validate ─────────────────────────────────────────────────────────────────
if [[ -z "$DOCKERFILE" ]]; then
    echo "Error: --file is required." >&2
    usage
fi

if [[ ! -f "$DOCKERFILE" ]]; then
    echo "Error: Dockerfile not found at '$DOCKERFILE'." >&2
    exit 1
fi

if [[ ! -d "$CONTEXT" ]]; then
    echo "Error: build context directory not found at '$CONTEXT'" >&2
    exit 1
fi

# ── resolve default platform ────────────────────────────────────────────────
if [[ -z "$PLATFORM" ]]; then
    if [[ "$PUSH" == true ]]; then
        PLATFORM="linux/amd64,linux/arm64"
    else
        PLATFORM="linux/amd64"
    fi
fi

# ── setup buildx builder ─────────────────────────────────────────────────────
if ! docker buildx inspect multiarch >/dev/null 2>&1; then
    echo "▶ Creating multiarch buildx builder..."
    docker buildx create --name multiarch --driver docker-container --use
fi
docker buildx use multiarch
if [[ "$VERBOSE" == true ]]; then
    docker buildx inspect --bootstrap
else
    docker buildx inspect --bootstrap >/dev/null
fi

# ── build cmd ────────────────────────────────────────────────────────────────
BUILD_ARGS=(
    buildx build
    --platform "$PLATFORM"
    -f "$DOCKERFILE"
)

for tag in "${TAGS[@]}"; do
    BUILD_ARGS+=(-t "$tag")
done

if [[ "$PUSH" == true ]]; then
    BUILD_ARGS+=(--push)
else
    BUILD_ARGS+=(--load)
fi

BUILD_ARGS+=("${EXTRA_ARGS[@]}")
BUILD_ARGS+=("$CONTEXT")

echo "▶ docker ${BUILD_ARGS[*]}"
exec docker "${BUILD_ARGS[@]}"
