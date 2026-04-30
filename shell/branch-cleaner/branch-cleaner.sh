#!/usr/bin/env bash

set -u

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

BASE_BRANCH=""
DELETE=false
FORCE=false
YES=false
FETCH=true
NO_COLOR=false
MODE="all"

PROTECTED_BRANCHES=("main" "master" "develop" "development" "staging" "release" "production")

print_usage() {
    cat << EOF
Usage:
  $(basename "$0") [options]

Options:
  -b, --base <branch>     Base branch used to detect merged branches.
                          Default: current branch.
  --delete                Delete detected branches.
  --force                 Force delete branches using git branch -D.
                          By default, git branch -d is used.
  --yes                   Do not ask for confirmation when deleting.
  --gone-only             Only show/delete branches whose remote tracking branch is gone.
  --merged-only           Only show/delete branches already merged into the base branch.
  --no-fetch              Do not run git fetch --prune before checking branches.
  --no-color              Disable colored output.
  -h, --help              Show this help message.

Examples:
  $(basename "$0")
  $(basename "$0") -b develop
  $(basename "$0") --gone-only
  $(basename "$0") --merged-only -b main
  $(basename "$0") --delete -b develop
  $(basename "$0") --delete --force --gone-only
EOF
}

color() {
    local color_code="$1"
    local message="$2"

    if [[ "$NO_COLOR" == true ]]; then
        echo -e "$message"
    else
        echo -e "${color_code}${message}${NC}"
    fi
}

log_info() {
    color "$BLUE" "$1"
}

log_success() {
    color "$GREEN" "$1"
}

log_warn() {
    color "$YELLOW" "$1"
}

log_error() {
    color "$RED" "$1"
}

is_git_repo() {
    git rev-parse --is-inside-work-tree >/dev/null 2>&1
}

current_branch() {
    git rev-parse --abbrev-ref HEAD 2>/dev/null
}

branch_exists() {
    git show-ref --verify --quiet "refs/heads/$1"
}

is_protected_branch() {
    local branch="$1"

    for protected in "${PROTECTED_BRANCHES[@]}"; do
        if [[ "$branch" == "$protected" ]]; then
            return 0
        fi
    done

    return 1
}

is_current_branch() {
    local branch="$1"
    local current="$2"

    [[ "$branch" == "$current" ]]
}

is_remote_tracking_gone() {
    local branch="$1"
    local upstream

    upstream=$(git for-each-ref --format='%(upstream:short)' "refs/heads/$branch")

    if [[ -z "$upstream" ]]; then
        return 1
    fi

    if git show-ref --verify --quiet "refs/remotes/$upstream"; then
        return 1
    fi

    return 0
}

is_merged_into_base() {
    local branch="$1"
    local base="$2"

    git merge-base --is-ancestor "$branch" "$base" >/dev/null 2>&1
}

add_candidate() {
    local branch="$1"
    local reason="$2"

    for i in "${!CANDIDATE_BRANCHES[@]}"; do
        if [[ "${CANDIDATE_BRANCHES[$i]}" == "$branch" ]]; then
            CANDIDATE_REASONS[$i]="${CANDIDATE_REASONS[$i]}, $reason"
            return
        fi
    done

    CANDIDATE_BRANCHES+=("$branch")
    CANDIDATE_REASONS+=("$reason")
}

parse_args() {
    while [[ $# -gt 0 ]]; do
        case "$1" in
            -b|--base)
                if [[ -z "${2:-}" ]]; then
                    log_error "Error: Option $1 requires a branch name."
                    echo
                    print_usage
                    exit 1
                fi
                BASE_BRANCH="$2"
                shift 2
                ;;
            --delete)
                DELETE=true
                shift
                ;;
            --force)
                FORCE=true
                shift
                ;;
            --yes)
                YES=true
                shift
                ;;
            --gone-only)
                MODE="gone"
                shift
                ;;
            --merged-only)
                MODE="merged"
                shift
                ;;
            --no-fetch)
                FETCH=false
                shift
                ;;
            --no-color)
                NO_COLOR=true
                shift
                ;;
            -h|--help)
                print_usage
                exit 0
                ;;
            *)
                log_error "Error: Unknown option '$1'."
                echo
                print_usage
                exit 1
                ;;
        esac
    done
}

confirm_delete() {
    if [[ "$YES" == true ]]; then
        return 0
    fi

    echo
    log_warn "You are about to delete ${#CANDIDATE_BRANCHES[@]} local branch(es)."
    read -r -p "Continue? [y/N]: " response

    case "$response" in
        y|Y|yes|YES)
            return 0
            ;;
        *)
            log_warn "Delete cancelled."
            return 1
            ;;
    esac
}

delete_candidates() {
    local delete_cmd="-d"

    if [[ "$FORCE" == true ]]; then
        delete_cmd="-D"
    fi

    echo
    log_warn "Deleting branches using: git branch $delete_cmd"
    echo

    local deleted=0
    local failed=0

    for branch in "${CANDIDATE_BRANCHES[@]}"; do
        if git branch "$delete_cmd" "$branch"; then
            deleted=$((deleted + 1))
        else
            log_error "Failed to delete branch: $branch"
            failed=$((failed + 1))
        fi
    done

    echo
    log_success "Deleted branches: $deleted"

    if [[ "$failed" -gt 0 ]]; then
        log_error "Failed deletions: $failed"
        exit 1
    fi
}

main() {
    parse_args "$@"

    if ! is_git_repo; then
        log_error "Error: This directory is not inside a Git repository."
        exit 1
    fi

    local current
    current=$(current_branch)

    if [[ "$current" == "HEAD" ]]; then
        log_error "Error: Detached HEAD state detected. Cannot continue safely."
        exit 1
    fi

    if [[ -z "$BASE_BRANCH" ]]; then
        BASE_BRANCH="$current"
    fi

    if ! branch_exists "$BASE_BRANCH"; then
        log_error "Error: Base branch '$BASE_BRANCH' does not exist locally."
        exit 1
    fi

    log_warn "Starting branch cleanup analysis..."
    log_info "Current branch: $current"
    log_info "Base branch: $BASE_BRANCH"

    if [[ "$FETCH" == true ]]; then
        log_info "Fetching remote changes and pruning deleted remote branches..."
        if ! git fetch --prune; then
            log_error "Error: git fetch --prune failed."
            exit 1
        fi
    fi

    declare -a CANDIDATE_BRANCHES
    declare -a CANDIDATE_REASONS

    while IFS= read -r branch; do
        [[ -z "$branch" ]] && continue

        if is_current_branch "$branch" "$current"; then
            continue
        fi

        if is_protected_branch "$branch"; then
            continue
        fi

        if [[ "$MODE" == "all" || "$MODE" == "gone" ]]; then
            if is_remote_tracking_gone "$branch"; then
                add_candidate "$branch" "remote tracking branch is gone"
            fi
        fi

        if [[ "$MODE" == "all" || "$MODE" == "merged" ]]; then
            if is_merged_into_base "$branch" "$BASE_BRANCH"; then
                add_candidate "$branch" "merged into $BASE_BRANCH"
            fi
        fi

    done < <(git for-each-ref --format='%(refname:short)' refs/heads)

    echo

    if [[ ${#CANDIDATE_BRANCHES[@]} -eq 0 ]]; then
        log_success "No local branches found for cleanup."
        exit 0
    fi

    log_warn "Branches detected for cleanup:"
    echo

    for i in "${!CANDIDATE_BRANCHES[@]}"; do
        branch="${CANDIDATE_BRANCHES[$i]}"
        reason="${CANDIDATE_REASONS[$i]}"
        echo -e "  ${RED}${branch}${NC} - ${reason}"
    done

    echo

    if [[ "$DELETE" == false ]]; then
        log_info "Dry-run mode. No branches were deleted."
        log_info "Run with --delete to delete these branches."
        exit 0
    fi

    if confirm_delete; then
        delete_candidates
    fi
}

main "$@"