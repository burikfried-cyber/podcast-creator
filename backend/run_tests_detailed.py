"""
Run tests with detailed output capture
"""
import subprocess
import sys

print("=" * 80)
print("RUNNING PHASE 2 UNIT TESTS")
print("=" * 80)

# Run pytest with detailed output
result = subprocess.run(
    [
        sys.executable, "-m", "pytest",
        "tests/unit/",
        "-v",
        "--tb=short",
        "--maxfail=5",  # Stop after 5 failures
        "-x",  # Stop on first failure for debugging
    ],
    capture_output=True,
    text=True,
    timeout=300  # 5 minute timeout
)

print(result.stdout)
if result.stderr:
    print("\n" + "=" * 80)
    print("STDERR:")
    print("=" * 80)
    print(result.stderr)

print("\n" + "=" * 80)
print(f"EXIT CODE: {result.returncode}")
print("=" * 80)

# Parse summary
if "passed" in result.stdout:
    lines = result.stdout.split('\n')
    for line in lines:
        if 'passed' in line or 'failed' in line or 'error' in line:
            print(f"\n📊 {line}")
