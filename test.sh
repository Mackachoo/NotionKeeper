#!/bin/bash
# Quick test script for NotionKeeper converter

echo "🧪 Testing NotionKeeper Converter"
echo "=================================="
echo ""

# Test 1: LegendKeeper JSON to Notion
echo "📝 Test 1: Converting LegendKeeper JSON → Notion"
python3 converter.py lk-to-notion exports/legendkeeper/Realms.json imports/notion/test1/
echo ""

# Test 2: Notion to LegendKeeper
echo "📝 Test 2: Converting Notion → LegendKeeper"
python3 converter.py notion-to-lk "exports/notion/realms/Realms 4685d0dc1aa74932991bf15ace69472a" imports/legendkeeper/test2/
echo ""

# Test 3: LegendKeeper Markdown to Notion (if it exists)
if [ -d "exports/legendkeeper/Realms/Realms" ]; then
    echo "📝 Test 3: Converting LegendKeeper Markdown → Notion"
    python3 converter.py lk-to-notion exports/legendkeeper/Realms/Realms imports/notion/test3/
    echo ""
fi

echo "✅ All tests complete!"
echo ""
echo "📁 Check the imports/ directory for results"
echo "📝 Check the logs/ directory for detailed logs"
