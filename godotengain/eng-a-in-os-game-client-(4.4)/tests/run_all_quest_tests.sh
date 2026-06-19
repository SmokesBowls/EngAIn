#!/bin/bash
echo "🧪 Running all Quest3D tests..."
echo "========================================"

cd ~/Downloads/EngAIn/godotengain/engainos/core

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

test_passed() {
    echo -e "${GREEN}✅ $1${NC}"
}

test_failed() {
    echo -e "${RED}❌ $1${NC}"
}

# Test 1: Built-in kernel tests
echo "1. Running kernel tests..."
python quest3d_mr.py > /tmp/kernel_test.log 2>&1
if [ $? -eq 0 ]; then
    test_passed "Kernel tests passed"
else
    test_failed "Kernel tests failed"
    cat /tmp/kernel_test.log
fi

# Test 2: Built-in integration tests
echo "\n2. Running integration tests..."
python quest3d_integration.py > /tmp/integration_test.log 2>&1
if [ $? -eq 0 ]; then
    test_passed "Integration tests passed"
else
    test_failed "Integration tests failed"
    cat /tmp/integration_test.log
fi

# Test 3: Sample quests
echo "\n3. Creating sample quests..."
python -c "
from quest3d_integration import Quest3DIntegration
qs = Quest3DIntegration()
qs.register_quest({'id':'test','name':'Test','description':'Test','objectives':[],'rewards':[]})
print('✅ Sample quest created')
" > /tmp/sample_test.log 2>&1
if [ $? -eq 0 ]; then
    test_passed "Sample quest creation passed"
else
    test_failed "Sample quest creation failed"
    cat /tmp/sample_test.log
fi

echo "\n========================================"
echo "Test suite complete!"
