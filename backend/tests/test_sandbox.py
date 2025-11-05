#!/usr/bin/env python3
"""
Test sandbox security improvements
"""
import pandas as pd
from backend.services.safe_executor import SafeExecutor
from backend.services.code_validator import CodeValidator

def test_sandbox():
    executor = SafeExecutor()
    validator = CodeValidator()
    
    # Create test dataframe
    df = pd.DataFrame({
        'name': ['Alice', 'Bob', 'Charlie'],
        'age': [25, 30, 35],
        'salary': [50000, 60000, 70000]
    })
    
    print("="*80)
    print("SANDBOX SECURITY TESTS")
    print("="*80)
    
    # Test cases - all should fail
    malicious_codes = [
        ("Import OS", "import os; result = os.listdir('.')"),
        ("__import__ smuggling", "__import__('os').system('echo hacked')"),
        ("Getattr bypass", "getattr(__builtins__, 'eval')('1+1')"),
        ("File write via getattr", "getattr(open('hack.txt', 'w'), 'write')('pwned')"),
        ("Direct eval", "eval('1+1')"),
        ("Direct exec", "exec('print(\"hacked\")')"),
        ("Globals access", "globals()['__builtins__']"),
        ("Locals access", "result = locals()"),
        ("Dir introspection", "dir(__builtins__)"),
        ("Class access", "df.__class__.__bases__"),
        ("To CSV", "df.to_csv('leaked.csv')"),
    ]
    
    passed = 0
    failed = 0
    
    for name, code in malicious_codes:
        print(f"\n{'='*80}")
        print(f"Testing: {name}")
        print(f"Code: {code}")
        print(f"{'-'*80}")
        
        # Validate first
        validation = validator.validate(code, df.columns.tolist())
        
        if validation['valid']:
            print("❌ VALIDATION FAILED - Code passed validation (SECURITY ISSUE)")
            print(f"   Validation errors: {validation['errors']}")
            failed += 1
            
            # Try execution anyway
            result = executor.execute(code, df)
            if result['success']:
                print("🚨 CRITICAL: Code executed successfully (MAJOR SECURITY BREACH)")
            else:
                print(f"✓ Execution blocked: {result.get('error', 'Unknown')}")
        else:
            print(f"✅ VALIDATION BLOCKED - {len(validation['errors'])} errors found")
            for err in validation['errors'][:3]:  # Show first 3 errors
                print(f"   - {err['message']}")
            passed += 1
    
    print(f"\n{'='*80}")
    print(f"RESULTS: {passed}/{len(malicious_codes)} attacks blocked")
    print(f"{'='*80}")
    
    if failed > 0:
        print(f"\n⚠️  WARNING: {failed} attacks bypassed validation!")
        return False
    else:
        print("\n✅ All malicious code blocked successfully!")
        return True

if __name__ == "__main__":
    success = test_sandbox()
    exit(0 if success else 1)
