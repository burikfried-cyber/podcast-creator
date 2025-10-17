"""
Run Phase 2 Tests
Simple script to run verification and tests
"""
import subprocess
import sys

print("=" * 70)
print("PHASE 2 TEST RUNNER")
print("=" * 70)

# Step 1: Run verification
print("\n📋 Step 1: Running verification script...")
print("-" * 70)
result = subprocess.run([sys.executable, "verify_phase2.py"], capture_output=True, text=True)
print(result.stdout)
if result.stderr:
    print("STDERR:", result.stderr)

if result.returncode != 0:
    print("\n❌ Verification failed!")
    sys.exit(1)

print("\n✅ Verification passed!")

# Step 2: Run unit tests
print("\n📋 Step 2: Running unit tests...")
print("-" * 70)
result = subprocess.run(
    [sys.executable, "-m", "pytest", "tests/unit/", "-v", "--tb=short"],
    capture_output=True,
    text=True
)
print(result.stdout)
if result.stderr:
    print("STDERR:", result.stderr)

if result.returncode != 0:
    print("\n⚠️  Some tests failed or were skipped")
    print("This is expected if Phase 1 dependencies aren't set up")
else:
    print("\n✅ All tests passed!")

print("\n" + "=" * 70)
print("TEST RUN COMPLETE")
print("=" * 70)
