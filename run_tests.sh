#!/bin/bash
#
# Run comprehensive conversion tests
# This script runs multiple round-trip tests and collects results
#

set -e  # Exit on error

echo "════════════════════════════════════════════════════════════"
echo "  NotionKeeper Conversion Test Suite"
echo "════════════════════════════════════════════════════════════"
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Track results
TOTAL=0
PASSED=0
MINOR=0
FAILED=0

run_test() {
    local source=$1
    local chain=$2
    local description=$3
    
    TOTAL=$((TOTAL + 1))
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}Test ${TOTAL}: ${description}${NC}"
    echo -e "${BLUE}Chain: ${chain}${NC}"
    echo ""
    
    # Run test (capture output, don't exit on error)
    set +e  # Don't exit on error
    python3 test_converter.py "$source" "$chain"
    local exit_code=$?
    set -e  # Re-enable exit on error
    
    # Check the last report for result
    LAST_REPORT=$(ls -t testing/reports/test_report_*.txt 2>/dev/null | head -1)
    if [ -n "$LAST_REPORT" ]; then
        if grep -q "RESULT: PERFECT MATCH" "$LAST_REPORT"; then
            echo -e "${GREEN}✅ PASSED PERFECTLY${NC}"
            PASSED=$((PASSED + 1))
        elif grep -q "RESULT: MINOR DIFFERENCES" "$LAST_REPORT"; then
            echo -e "${YELLOW}⚠️  PASSED WITH MINOR DIFFERENCES${NC}"
            MINOR=$((MINOR + 1))
        elif grep -q "RESULT: SIGNIFICANT DIFFERENCES" "$LAST_REPORT"; then
            echo -e "${RED}❌ SIGNIFICANT DIFFERENCES FOUND${NC}"
            FAILED=$((FAILED + 1))
        else
            echo -e "${RED}❌ UNKNOWN RESULT${NC}"
            FAILED=$((FAILED + 1))
        fi
    else
        # No report means test crashed
        echo -e "${RED}❌ TEST CRASHED (no report generated)${NC}"
        FAILED=$((FAILED + 1))
    fi
    echo ""
}

# Check if test data exists
if [ ! -f "testing/Realms.json" ]; then
    echo -e "${RED}Error: testing/Realms.json not found${NC}"
    echo "Please ensure test data is in the testing/ directory"
    exit 1
fi

# Run tests
echo "Starting test suite..."
echo ""

# Test 1: LegendKeeper JSON round-trip
run_test \
    "testing/Realms.json" \
    "lk-json->notion->lk-json" \
    "LegendKeeper JSON → Notion → LegendKeeper JSON"

# Test 2: Notion round-trip (if exists)
if [ -d "testing/notion-realms/Realms 4685d0dc1aa74932991bf15ace69472a" ]; then
    run_test \
        "testing/notion-realms/Realms 4685d0dc1aa74932991bf15ace69472a" \
        "notion->lk-json->notion" \
        "Notion → LegendKeeper JSON → Notion"
else
    echo -e "${YELLOW}⚠️  Skipping Notion round-trip test (no test data)${NC}"
fi

# Test 3: LegendKeeper Markdown round-trip (if exists)
if [ -d "testing/legendkeeper-realms/Realms" ]; then
    run_test \
        "testing/legendkeeper-realms/Realms" \
        "lk-md->notion->lk-md" \
        "LegendKeeper Markdown → Notion → LegendKeeper Markdown"
else
    echo -e "${YELLOW}⚠️  Skipping LegendKeeper Markdown test (no test data)${NC}"
fi

# Print summary
echo "════════════════════════════════════════════════════════════"
echo "  Test Suite Summary"
echo "════════════════════════════════════════════════════════════"
echo ""
echo "Total tests:   $TOTAL"
echo -e "${GREEN}Passed:        $PASSED${NC}"
echo -e "${YELLOW}Minor diffs:   $MINOR${NC}"
echo -e "${RED}Failed:        $FAILED${NC}"
echo ""

# Overall result
if [ $FAILED -eq 0 ]; then
    if [ $MINOR -eq 0 ]; then
        echo -e "${GREEN}════════════════════════════════════════════════════════════${NC}"
        echo -e "${GREEN}  ✅ ALL TESTS PASSED PERFECTLY${NC}"
        echo -e "${GREEN}════════════════════════════════════════════════════════════${NC}"
        exit 0
    else
        echo -e "${YELLOW}════════════════════════════════════════════════════════════${NC}"
        echo -e "${YELLOW}  ⚠️  ALL TESTS PASSED WITH MINOR DIFFERENCES${NC}"
        echo -e "${YELLOW}════════════════════════════════════════════════════════════${NC}"
        exit 0
    fi
else
    echo -e "${RED}════════════════════════════════════════════════════════════${NC}"
    echo -e "${RED}  ❌ SOME TESTS FAILED${NC}"
    echo -e "${RED}════════════════════════════════════════════════════════════${NC}"
    exit 1
fi
