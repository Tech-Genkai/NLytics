#!/usr/bin/env python3
"""
API Test Script for NLytics
Demonstrates all API endpoints with examples
"""
import requests
import json
from pathlib import Path

API_BASE = "http://localhost:5000/api/v1"

def print_section(title):
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60 + "\n")

def test_health_check():
    print_section("Health Check")
    response = requests.get("http://localhost:5000/api/health")
    print(json.dumps(response.json(), indent=2))

def test_analyze():
    print_section("Complete Analysis (One-Shot)")
    
    # Use sample stock data
    file_path = Path("samples/stock_data_july_2025.csv")
    
    if not file_path.exists():
        print(f"[ERROR] Sample file not found: {file_path}")
        return None
    
    print(f"[UPLOAD] File: {file_path}")
    print(f"[QUERY] 'top 5 stocks by volume'")
    
    with open(file_path, 'rb') as f:
        response = requests.post(
            f"{API_BASE}/analyze",
            files={'file': f},
            data={
                'query': 'top 5 stocks by volume',
                'return_code': 'true',
                'return_visualization': 'true'
            }
        )
    
    if response.status_code == 200:
        data = response.json()
        print("\n[SUCCESS]")
        print(f"\n[Query Understanding]")
        print(f"   Original: {data['query']['original']}")
        print(f"   Refined: {data['query'].get('refined', 'N/A')}")
        print(f"   Intent: {data['query']['intent']['type']}")
        
        print(f"\n[Generated Code]")
        for line in data['code']['generated'].split('\n'):
            print(f"   {line}")
        print(f"   Execution time: {data['code']['execution_time']:.3f}s")
        
        print(f"\n[Result]")
        print(f"   Type: {data['result']['type']}")
        print(f"   Data preview:")
        for item in data['result']['data'][:3]:
            print(f"      {item}")
        
        if data.get('visualization') and data['visualization'].get('suitable'):
            viz = data['visualization']
            print(f"\n[Visualization]")
            print(f"   Type: {viz['type']}")
            print(f"   Colors: {len(viz.get('colors', []))} different colors")
            print(f"   Labels: {viz.get('x_values', [])[:5]}")
        
        print(f"\n[Insights]")
        print(f"   {data['insights']['narrative']}")
        
        print(f"\n[Answer]")
        print(f"   {data['answer'][:200]}...")
        
        return data
    else:
        print(f"[ERROR] {response.status_code}: {response.text}")
        return None

def test_code_validation():
    print_section("Code Validation")
    
    # Test valid code
    print("Testing VALID code:")
    response = requests.post(
        f"{API_BASE}/code/validate",
        json={
            'code': "df.nlargest(10, 'Volume')[['Symbol', 'Volume']]",
            'columns': ['Symbol', 'Volume', 'Close', 'Open']
        }
    )
    
    result = response.json()
    print(f"   Code: df.nlargest(10, 'Volume')[['Symbol', 'Volume']]")
    if 'error' in result:
        print(f"   [ERROR]: {result['error']}")
        return
    print(f"   Valid: {result['valid']}")
    print(f"   Errors: {result.get('errors', [])}")
    
    # Test invalid code
    print("\nTesting INVALID code (has eval):")
    response = requests.post(
        f"{API_BASE}/code/validate",
        json={
            'code': "eval('df.head()')",
            'columns': ['Symbol', 'Volume']
        }
    )
    
    result = response.json()
    print(f"   Code: eval('df.head()')")
    if 'error' in result:
        print(f"   [ERROR]: {result['error']}")
        return
    print(f"   Valid: {result['valid']}")
    print(f"   Errors: {result.get('errors', [])}")

def main():
    print("\n" + "NLytics API Test Suite".center(60))
    
    try:
        # Test 1: Health check
        test_health_check()
        
        # Test 2: Complete analysis
        test_analyze()
        
        # Test 3: Code validation
        test_code_validation()
        
        print_section("Summary")
        print("[SUCCESS] All tests completed!")
        print("\n[DOCS] For full API documentation, see: docs/API.md")
        print("[API] Base URL: http://localhost:5000/api/v1")
        
    except requests.exceptions.ConnectionError:
        print("\n[ERROR] Connection Error!")
        print("   Make sure NLytics server is running:")
        print("   python start.py")
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
