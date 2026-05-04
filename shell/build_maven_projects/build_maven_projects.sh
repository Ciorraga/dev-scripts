#!/usr/bin/env bash

# Colors for better readability
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No color

# Default values
MAVEN_GOALS="clean install"
SKIP_TESTS=false
OFFLINE=false
TARGET_PATH="."

declare -a OK_PROJECTS
declare -a FAILED_PROJECTS
declare -a SKIPPED_DIRS

print_usage() {
    echo "Usage: $(basename "$0") [options]"
    echo
    echo "Options:"
    echo "  -p <path>      Path containing Maven projects. Default: current directory."
    echo "  -g <goals>     Maven goals to run. Default: \"clean install\""
    echo "  --skip-tests   Skip test execution using -DskipTests"
    echo "  --offline      Run Maven in offline mode using -o"
    echo "  -h, --help     Show this help message"
    echo
    echo "Examples:"
    echo "  $(basename "$0")"
    echo "  $(basename "$0") -p ~/workspace/services"
    echo "  $(basename "$0") --skip-tests"
    echo "  $(basename "$0") -p ~/workspace/services --skip-tests"
    echo "  $(basename "$0") -g \"clean package\""
    echo "  $(basename "$0") -p ~/workspace/services -g \"clean verify\" --skip-tests"
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        -p|--path)
            if [[ -z "${2:-}" ]]; then
                echo -e "${RED}Error: Option $1 requires a path.${NC}"
                echo
                print_usage
                exit 1
            fi
            TARGET_PATH="$2"
            shift 2
            ;;
        -g)
            if [[ -z "${2:-}" ]]; then
                echo -e "${RED}Error: Option -g requires an argument.${NC}"
                echo
                print_usage
                exit 1
            fi
            MAVEN_GOALS="$2"
            shift 2
            ;;
        --skip-tests)
            SKIP_TESTS=true
            shift
            ;;
        --offline)
            OFFLINE=true
            shift
            ;;
        -h|--help)
            print_usage
            exit 0
            ;;
        *)
            echo -e "${RED}Error: Unknown option '$1'.${NC}"
            echo
            print_usage
            exit 1
            ;;
    esac
done

if [[ ! -d "$TARGET_PATH" ]]; then
    echo -e "${RED}Error: Path '$TARGET_PATH' does not exist or is not a directory.${NC}"
    exit 1
fi

TARGET_PATH="$(cd "$TARGET_PATH" && pwd)"

echo -e "${YELLOW}Starting Maven projects build process...${NC}"
echo -e "${BLUE}Target path: ${TARGET_PATH}${NC}"
echo -e "${BLUE}Maven goals: ${MAVEN_GOALS}${NC}"

if [[ "$SKIP_TESTS" == true ]]; then
    echo -e "${BLUE}Skip tests: enabled${NC}"
fi

if [[ "$OFFLINE" == true ]]; then
    echo -e "${BLUE}Offline mode: enabled${NC}"
fi

echo

for dir in "$TARGET_PATH"/*/; do
    [[ -d "$dir" ]] || continue

    project_name=$(basename "$dir")

    if [[ ! -f "$dir/pom.xml" ]]; then
        echo -e "${YELLOW}⚠️  $project_name is not a Maven project. Skipping...${NC}"
        SKIPPED_DIRS+=("${project_name} - SKIPPED: pom.xml not found")
        continue
    fi

    echo -e "${GREEN}Processing Maven project: $project_name${NC}"

    (
        cd "$dir" || exit 10

        if [[ -x "./mvnw" ]]; then
            MAVEN_CMD="./mvnw"
        elif [[ -f "./mvnw" ]]; then
            chmod +x ./mvnw
            MAVEN_CMD="./mvnw"
        elif command -v mvn >/dev/null 2>&1; then
            MAVEN_CMD="mvn"
        else
            echo -e "${RED}❌ Maven is not installed and Maven Wrapper was not found.${NC}"
            exit 20
        fi

        MAVEN_ARGS=()

        if [[ "$OFFLINE" == true ]]; then
            MAVEN_ARGS+=("-o")
        fi

        read -r -a GOALS_ARRAY <<< "$MAVEN_GOALS"
        MAVEN_ARGS+=("${GOALS_ARRAY[@]}")

        if [[ "$SKIP_TESTS" == true ]]; then
            MAVEN_ARGS+=("-DskipTests")
        fi

        echo -e "${YELLOW}Running '${MAVEN_CMD} ${MAVEN_ARGS[*]}' in $project_name...${NC}"

        if "$MAVEN_CMD" "${MAVEN_ARGS[@]}"; then
            exit 0
        else
            exit 30
        fi
    )

    status=$?

    case "$status" in
        0)
            OK_PROJECTS+=("${project_name} - OK")
            ;;
        10)
            FAILED_PROJECTS+=("${project_name} - NOT OK: Could not enter project directory")
            ;;
        20)
            FAILED_PROJECTS+=("${project_name} - NOT OK: Maven not available")
            ;;
        30)
            FAILED_PROJECTS+=("${project_name} - NOT OK: Build failed")
            ;;
        *)
            FAILED_PROJECTS+=("${project_name} - NOT OK: Unexpected error")
            ;;
    esac

    echo "-----------------------------------"
done

echo
echo -e "${YELLOW}Build summary:${NC}"
echo

if [[ ${#OK_PROJECTS[@]} -gt 0 ]]; then
    echo -e "${GREEN}Successful builds:${NC}"
    for result in "${OK_PROJECTS[@]}"; do
        echo -e "${GREEN}✔ $result${NC}"
    done
    echo
fi

if [[ ${#FAILED_PROJECTS[@]} -gt 0 ]]; then
    echo -e "${RED}Failed builds:${NC}"
    for result in "${FAILED_PROJECTS[@]}"; do
        echo -e "${RED}✘ $result${NC}"
    done
    echo
fi

if [[ ${#SKIPPED_DIRS[@]} -gt 0 ]]; then
    echo -e "${YELLOW}Skipped directories:${NC}"
    for result in "${SKIPPED_DIRS[@]}"; do
        echo -e "${YELLOW}- $result${NC}"
    done
    echo
fi

echo -e "${YELLOW}Build process completed.${NC}"

if [[ ${#FAILED_PROJECTS[@]} -gt 0 ]]; then
    exit 1
fi

exit 0