#!/usr/bin/env bash

# Color definitions
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Arrays to hold final summary
declare -a OK_REPOS
declare -a FAILED_REPOS
declare -a SKIPPED_REPOS

TARGET_BRANCH=""
TARGET_PATH="."

print_usage() {
    echo "Usage: $(basename "$0") -b <branch> [options]"
    echo
    echo "Options:"
    echo "  -b <branch>   Branch to update. Required."
    echo "  -p <path>     Path containing Git repositories. Default: current directory."
    echo "  -h            Show this help message"
    echo
    echo "Examples:"
    echo "  $(basename "$0") -b develop"
    echo "  $(basename "$0") -b develop -p ~/workspace/services"
}

while getopts ":b:p:h" opt; do
    case "$opt" in
        b)
            TARGET_BRANCH="$OPTARG"
            ;;
        p)
            TARGET_PATH="$OPTARG"
            ;;
        h)
            print_usage
            exit 0
            ;;
        :)
            echo -e "${RED}Error: Option -$OPTARG requires an argument.${NC}"
            echo
            print_usage
            exit 1
            ;;
        \?)
            echo -e "${RED}Error: Invalid option -$OPTARG.${NC}"
            echo
            print_usage
            exit 1
            ;;
    esac
done

if [[ -z "$TARGET_BRANCH" ]]; then
    echo -e "${RED}Error: Missing required parameter -b <branch>.${NC}"
    echo
    print_usage
    exit 1
fi

if [[ ! -d "$TARGET_PATH" ]]; then
    echo -e "${RED}Error: Path '$TARGET_PATH' does not exist or is not a directory.${NC}"
    exit 1
fi

TARGET_PATH="$(cd "$TARGET_PATH" && pwd)"

echo -e "${YELLOW}Starting repositories update...${NC}"
echo -e "${BLUE}Target branch: ${TARGET_BRANCH}${NC}"
echo -e "${BLUE}Target path: ${TARGET_PATH}${NC}"
echo

for dir in "$TARGET_PATH"/*/; do
    [[ -d "$dir" ]] || continue

    repo_name=$(basename "$dir")

    if [[ ! -d "$dir/.git" ]]; then
        echo -e "${YELLOW}⚠️  $repo_name is not a Git repository. Skipping...${NC}"
        SKIPPED_REPOS+=("${repo_name} - SKIPPED: Not a Git repository")
        continue
    fi

    echo -e "${GREEN}Processing repository: $repo_name${NC}"

    (
        cd "$dir" || exit 1

        current_branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null)

        if [[ "$current_branch" == "HEAD" ]]; then
            echo -e "${RED}❌ Detached HEAD in $repo_name. Skipping...${NC}"
            exit 10
        fi

        if [[ -n $(git status --porcelain) ]]; then
            echo -e "${RED}⚠️  Uncommitted changes in $repo_name (branch: $current_branch). Skipping...${NC}"
            exit 20
        fi

        echo -e "${BLUE}Fetching latest remote information...${NC}"
        if ! git fetch origin --prune; then
            echo -e "${RED}❌ Failed to fetch origin in $repo_name.${NC}"
            exit 30
        fi

        if ! git ls-remote --exit-code --heads origin "$TARGET_BRANCH" >/dev/null 2>&1; then
            echo -e "${RED}❌ Remote branch '$TARGET_BRANCH' does not exist in $repo_name. Skipping...${NC}"
            exit 40
        fi

        if [[ "$current_branch" == "$TARGET_BRANCH" ]]; then
            echo -e "${GREEN}→ Already on $TARGET_BRANCH. Pulling latest changes...${NC}"

            if git pull --ff-only origin "$TARGET_BRANCH"; then
                exit 0
            else
                echo -e "${RED}❌ Pull failed in $repo_name.${NC}"
                exit 50
            fi
        else
            echo -e "${YELLOW}↪ Switching from $current_branch to $TARGET_BRANCH...${NC}"

            if git show-ref --verify --quiet "refs/heads/$TARGET_BRANCH"; then
                if ! git switch "$TARGET_BRANCH"; then
                    echo -e "${RED}❌ Failed to switch to local branch '$TARGET_BRANCH' in $repo_name.${NC}"
                    exit 60
                fi
            else
                if ! git switch --track "origin/$TARGET_BRANCH"; then
                    echo -e "${RED}❌ Failed to create local branch '$TARGET_BRANCH' tracking origin/$TARGET_BRANCH in $repo_name.${NC}"
                    exit 70
                fi
            fi

            echo -e "${GREEN}→ Pulling latest changes from origin/$TARGET_BRANCH...${NC}"

            if git pull --ff-only origin "$TARGET_BRANCH"; then
                exit 0
            else
                echo -e "${RED}❌ Pull failed in $repo_name.${NC}"
                exit 50
            fi
        fi
    )

    status=$?

    case "$status" in
        0)
            OK_REPOS+=("${repo_name} - OK")
            ;;
        10)
            FAILED_REPOS+=("${repo_name} - NOT OK: Detached HEAD")
            ;;
        20)
            FAILED_REPOS+=("${repo_name} - NOT OK: Uncommitted changes")
            ;;
        30)
            FAILED_REPOS+=("${repo_name} - NOT OK: Fetch failed")
            ;;
        40)
            FAILED_REPOS+=("${repo_name} - NOT OK: Remote branch '$TARGET_BRANCH' does not exist")
            ;;
        50)
            FAILED_REPOS+=("${repo_name} - NOT OK: Pull failed")
            ;;
        60)
            FAILED_REPOS+=("${repo_name} - NOT OK: Failed to switch to local branch '$TARGET_BRANCH'")
            ;;
        70)
            FAILED_REPOS+=("${repo_name} - NOT OK: Failed to create tracking branch '$TARGET_BRANCH'")
            ;;
        *)
            FAILED_REPOS+=("${repo_name} - NOT OK: Unexpected error")
            ;;
    esac

    echo "-----------------------------------"
done

echo
echo -e "${YELLOW}Update summary:${NC}"
echo

if [[ ${#OK_REPOS[@]} -gt 0 ]]; then
    echo -e "${GREEN}Updated repositories:${NC}"
    for result in "${OK_REPOS[@]}"; do
        echo -e "${GREEN}✔ $result${NC}"
    done
    echo
fi

if [[ ${#FAILED_REPOS[@]} -gt 0 ]]; then
    echo -e "${RED}Repositories that could NOT be updated:${NC}"
    for result in "${FAILED_REPOS[@]}"; do
        echo -e "${RED}✘ $result${NC}"
    done
    echo
fi

if [[ ${#SKIPPED_REPOS[@]} -gt 0 ]]; then
    echo -e "${YELLOW}Skipped directories:${NC}"
    for result in "${SKIPPED_REPOS[@]}"; do
        echo -e "${YELLOW}- $result${NC}"
    done
    echo
fi

echo -e "${YELLOW}All repositories processed.${NC}"

if [[ ${#FAILED_REPOS[@]} -gt 0 ]]; then
    exit 1
fi

exit 0