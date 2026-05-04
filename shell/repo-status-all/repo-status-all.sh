#!/usr/bin/env bash

set -u

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

TARGET_PATH="."
FETCH=false
SHOW_SKIPPED=false
NO_COLOR=false

print_usage() {
    cat << EOF
Usage:
  $(basename "$0") [options]

Options:
  -p, --path <path>   Path containing Git repositories. Default: current directory.
  --fetch             Run git fetch --prune before checking each repository.
  --show-skipped      Show directories that are not Git repositories.
  --no-color          Disable colored output.
  -h, --help          Show this help message.

Examples:
  $(basename "$0")
  $(basename "$0") -p ~/workspace
  $(basename "$0") -p ~/workspace --fetch
  $(basename "$0") -p ~/workspace --fetch --show-skipped
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

parse_args() {
    while [[ $# -gt 0 ]]; do
        case "$1" in
            -p|--path)
                if [[ -z "${2:-}" ]]; then
                    log_error "Error: Option $1 requires a path."
                    echo
                    print_usage
                    exit 1
                fi
                TARGET_PATH="$2"
                shift 2
                ;;
            --fetch)
                FETCH=true
                shift
                ;;
            --show-skipped)
                SHOW_SKIPPED=true
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

is_git_repo() {
    local dir="$1"
    git -C "$dir" rev-parse --is-inside-work-tree >/dev/null 2>&1
}

get_current_branch() {
    local dir="$1"
    git -C "$dir" rev-parse --abbrev-ref HEAD 2>/dev/null
}

get_upstream() {
    local dir="$1"
    git -C "$dir" rev-parse --abbrev-ref --symbolic-full-name '@{u}' 2>/dev/null || true
}

get_worktree_status() {
    local dir="$1"

    if [[ -n $(git -C "$dir" status --porcelain) ]]; then
        echo "dirty"
    else
        echo "clean"
    fi
}

get_ahead_behind() {
    local dir="$1"
    local upstream="$2"

    if [[ -z "$upstream" ]]; then
        echo "- -"
        return
    fi

    git -C "$dir" rev-list --left-right --count "HEAD...$upstream" 2>/dev/null || echo "- -"
}

format_changes() {
    local changes="$1"

    if [[ "$changes" == "clean" ]]; then
        color "$GREEN" "$changes"
    else
        color "$YELLOW" "$changes"
    fi
}

format_sync() {
    local sync_status="$1"

    case "$sync_status" in
        "up-to-date")
            color "$GREEN" "$sync_status"
            ;;
        "no upstream")
            color "$YELLOW" "$sync_status"
            ;;
        "fetch failed"|"detached HEAD"|diverged*)
            color "$RED" "$sync_status"
            ;;
        ahead*|behind*)
            color "$YELLOW" "$sync_status"
            ;;
        *)
            color "$RED" "$sync_status"
            ;;
    esac
}

print_table_header() {
    printf "%-35s %-25s %-12s %-18s %-30s\n" "Repository" "Branch" "Changes" "Sync" "Upstream"
    printf "%-35s %-25s %-12s %-18s %-30s\n" "----------" "------" "-------" "----" "--------"
}

main() {
    parse_args "$@"

    if [[ ! -d "$TARGET_PATH" ]]; then
        log_error "Error: Path '$TARGET_PATH' does not exist or is not a directory."
        exit 1
    fi

    TARGET_PATH="$(cd "$TARGET_PATH" && pwd)"

    log_warn "Checking repositories status..."
    log_info "Target path: $TARGET_PATH"
    echo

    local total_repos=0
    local clean_repos=0
    local dirty_repos=0
    local no_upstream_repos=0
    local behind_repos=0
    local ahead_repos=0
    local diverged_repos=0
    local fetch_failed_repos=0
    local detached_head_repos=0
    local skipped_dirs=0

    print_table_header

    for dir in "$TARGET_PATH"/*/; do
        [[ -d "$dir" ]] || continue

        local repo_name
        repo_name=$(basename "$dir")

        if ! is_git_repo "$dir"; then
            skipped_dirs=$((skipped_dirs + 1))

            if [[ "$SHOW_SKIPPED" == true ]]; then
                printf "%-35s %-25s %-12s %-18s %-30s\n" "$repo_name" "-" "skipped" "not git repo" "-"
            fi

            continue
        fi

        total_repos=$((total_repos + 1))

        local fetch_failed=false

        if [[ "$FETCH" == true ]]; then
            if ! git -C "$dir" fetch --prune --quiet; then
                fetch_failed=true
            fi
        fi

        local branch
        local upstream
        local changes
        local ahead
        local behind
        local sync_status

        branch=$(get_current_branch "$dir")
        upstream=$(get_upstream "$dir")
        changes=$(get_worktree_status "$dir")

        read -r ahead behind <<< "$(get_ahead_behind "$dir" "$upstream")"

        if [[ "$fetch_failed" == true ]]; then
            sync_status="fetch failed"
            fetch_failed_repos=$((fetch_failed_repos + 1))
        elif [[ "$branch" == "HEAD" ]]; then
            sync_status="detached HEAD"
            detached_head_repos=$((detached_head_repos + 1))
        elif [[ -z "$upstream" ]]; then
            sync_status="no upstream"
            no_upstream_repos=$((no_upstream_repos + 1))
        elif [[ "$ahead" == "-" || "$behind" == "-" ]]; then
            sync_status="unknown"
        elif [[ "$ahead" -eq 0 && "$behind" -eq 0 ]]; then
            sync_status="up-to-date"
        elif [[ "$ahead" -gt 0 && "$behind" -eq 0 ]]; then
            sync_status="ahead $ahead"
            ahead_repos=$((ahead_repos + 1))
        elif [[ "$ahead" -eq 0 && "$behind" -gt 0 ]]; then
            sync_status="behind $behind"
            behind_repos=$((behind_repos + 1))
        else
            sync_status="diverged +$ahead/-$behind"
            diverged_repos=$((diverged_repos + 1))
        fi

        if [[ "$changes" == "clean" ]]; then
            clean_repos=$((clean_repos + 1))
        else
            dirty_repos=$((dirty_repos + 1))
        fi

        local changes_display
        local sync_display

        changes_display=$(format_changes "$changes")
        sync_display=$(format_sync "$sync_status")

        printf "%-35s %-25s %-21s %-27s %-30s\n" "$repo_name" "$branch" "$changes_display" "$sync_display" "${upstream:-"-"}"
    done

    echo
    log_warn "Summary:"
    echo

    log_info "Repositories checked: $total_repos"
    log_success "Clean repositories: $clean_repos"

    if [[ "$dirty_repos" -gt 0 ]]; then
        log_warn "Dirty repositories: $dirty_repos"
    else
        log_success "Dirty repositories: 0"
    fi

    if [[ "$ahead_repos" -gt 0 ]]; then
        log_warn "Repositories ahead: $ahead_repos"
    fi

    if [[ "$behind_repos" -gt 0 ]]; then
        log_warn "Repositories behind: $behind_repos"
    fi

    if [[ "$diverged_repos" -gt 0 ]]; then
        log_error "Diverged repositories: $diverged_repos"
    fi

    if [[ "$detached_head_repos" -gt 0 ]]; then
        log_error "Detached HEAD repositories: $detached_head_repos"
    fi

    if [[ "$no_upstream_repos" -gt 0 ]]; then
        log_warn "Repositories without upstream: $no_upstream_repos"
    fi

    if [[ "$fetch_failed_repos" -gt 0 ]]; then
        log_error "Repositories with fetch errors: $fetch_failed_repos"
    fi

    if [[ "$SHOW_SKIPPED" == true ]]; then
        log_info "Skipped directories: $skipped_dirs"
    fi

    if [[ "$dirty_repos" -gt 0 || "$behind_repos" -gt 0 || "$diverged_repos" -gt 0 || "$detached_head_repos" -gt 0 || "$fetch_failed_repos" -gt 0 ]]; then
        exit 1
    fi

    exit 0
}

main "$@"