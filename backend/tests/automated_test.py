#!/usr/bin/env python3
"""
Automated Testing Script for NLytics
Tests a wide variety of prompts and captures results
"""
import requests
import json
import time
from datetime import datetime
from pathlib import Path
import sys

# API Configuration
API_URL = "http://localhost:5000/api"
STOCK_DATA_FILE = "samples/stock_data_july_2025.csv"

# Test Prompts organized by category
TEST_PROMPTS = {
    "Basic Aggregations": [
        "Which stock had the highest closing price in the entire dataset?",
        "What's the average PE ratio across all stocks?",
        "Show me total trading volume by sector",
    ],
    
    "Growth & Performance": [
        "Which stock grew the most from open to close?",
        "Find the top 10 most volatile stocks based on the difference between high and low prices",
        "Show me stocks that closed higher than they opened, ranked by percentage gain",
    ],
    
    "Sector Analysis": [
        "Compare average market cap by sector",
        "Which sector has the highest average dividend yield?",
        "Show me the technology sector's average PE ratio compared to healthcare",
    ],
    
    "Complex Queries": [
        "Find undervalued stocks with PE ratio below 15 and dividend yield above 2%",
        "Which stocks are trading near their 52-week high? Show me those within 5% of their peak",
        "Compare the correlation between volume traded and price volatility",
    ],
    
    "Statistical Insights": [
        "Show me outliers in market cap - which companies are way above or below average?",
        "What's the distribution of dividend yields? How many stocks pay dividends vs don't?",
        "Find stocks with abnormally high trading volume compared to their sector average",
    ],
    
    "Ranking & Top Lists": [
        "Top 15 stocks by market cap with their sector and PE ratio",
        "Bottom 10 performers - stocks with the biggest drop from high to close price",
        "Most expensive stocks by closing price across all sectors",
    ],
    
    "Crazy Complex": [
        "Find technology stocks with PE ratio above 30, volume over 10 million, and dividend yield of zero, then rank them by EPS",
        "Show me the average difference between 52-week high and current close price, grouped by sector, but only for stocks with market cap over 100 billion",
        "Compare intraday volatility (high minus low) as a percentage of open price across sectors",
    ],
    
    "Investment Screening": [
        "Find value stocks: PE ratio under 20, dividend yield over 1%, and EPS positive",
        "Show me growth stocks: high PE ratio (over 35), zero dividends, and EPS growth potential",
        "Defensive plays: stocks with dividend yield over 3% and low volatility",
    ],
    
    "Natural Language": [
        "yo what's the stock with the biggest gains?",
        "gimme top 5 tech stocks by market cap",
        "how many stocks are in the financials sector?",
    ],
    
    "Edge Cases": [
        "Show me everything about AAPL",
        "Compare AAPL, MSFT, and AMZN across all metrics",
        "Which stocks have dividend yield of exactly 0?",
    ],
}


class NLyticsTestRunner:
    def __init__(self):
        self.session_id = None
        self.results = []
        self.start_time = None
        
    def create_session(self):
        """Create a new NLytics session"""
        print("🔗 Creating new session...")
        try:
            response = requests.post(f"{API_URL}/session/new")
            response.raise_for_status()
            data = response.json()
            self.session_id = data['session_id']
            print(f"✅ Session created: {self.session_id}")
            return True
        except Exception as e:
            print(f"❌ Failed to create session: {e}")
            return False
    
    def upload_file(self):
        """Upload the stock data file"""
        print(f"\n📤 Uploading {STOCK_DATA_FILE}...")
        try:
            with open(STOCK_DATA_FILE, 'rb') as f:
                files = {'file': f}
                data = {'session_id': self.session_id}
                response = requests.post(f"{API_URL}/upload", files=files, data=data)
                response.raise_for_status()
                result = response.json()
                
                if result.get('success'):
                    print("✅ File uploaded successfully!")
                    # Print dataset info
                    if result.get('messages'):
                        for msg in result['messages']:
                            if 'rows' in msg.get('content', ''):
                                print(f"   {msg['content'][:100]}...")
                    return True
                else:
                    print(f"❌ Upload failed: {result.get('error', 'Unknown error')}")
                    return False
        except Exception as e:
            print(f"❌ Upload error: {e}")
            return False
    
    def test_query(self, category, prompt, prompt_num, total_prompts):
        """Test a single query and record results"""
        print(f"\n{'='*80}")
        print(f"📊 Test {prompt_num}/{total_prompts}: {category}")
        print(f"💬 Query: {prompt[:70]}{'...' if len(prompt) > 70 else ''}")
        print(f"{'='*80}")
        
        result = {
            'category': category,
            'prompt': prompt,
            'success': False,
            'response_time': 0,
            'has_visualization': False,
            'has_insights': False,
            'has_code': False,
            'error': None,
            'timestamp': datetime.now().isoformat()
        }
        
        start_time = time.time()
        
        try:
            response = requests.post(
                f"{API_URL}/chat",
                json={
                    'session_id': self.session_id,
                    'message': prompt
                },
                timeout=60  # 60 second timeout
            )
            response.raise_for_status()
            data = response.json()
            
            result['response_time'] = time.time() - start_time
            
            if data.get('success'):
                result['success'] = True
                
                # Analyze response
                main_msg = data.get('message', {})
                additional_msgs = data.get('additional_messages', [])
                all_messages = [main_msg] + additional_msgs
                
                for msg in all_messages:
                    metadata = msg.get('metadata', {})
                    
                    # Check for code
                    if metadata.get('code') or metadata.get('type') == 'generated_code':
                        result['has_code'] = True
                    
                    # Check for visualization
                    if metadata.get('insights', {}).get('visualization', {}).get('suitable'):
                        result['has_visualization'] = True
                    
                    # Check for insights
                    if metadata.get('type') in ['insights', 'answer']:
                        result['has_insights'] = True
                
                # Print summary
                print(f"✅ SUCCESS in {result['response_time']:.2f}s")
                print(f"   📝 Generated Code: {'Yes' if result['has_code'] else 'No'}")
                print(f"   📊 Visualization: {'Yes' if result['has_visualization'] else 'No'}")
                print(f"   💡 Insights: {'Yes' if result['has_insights'] else 'No'}")
                
                # Print first message content snippet
                if main_msg.get('content'):
                    content = main_msg['content'][:150].replace('\n', ' ')
                    print(f"   💬 Response: {content}...")
                
            else:
                result['error'] = data.get('error', 'Unknown error')
                print(f"❌ FAILED: {result['error']}")
                
        except requests.exceptions.Timeout:
            result['error'] = 'Request timeout (>60s)'
            result['response_time'] = 60
            print(f"⏱️ TIMEOUT after 60 seconds")
            
        except Exception as e:
            result['error'] = str(e)
            result['response_time'] = time.time() - start_time
            print(f"❌ ERROR: {e}")
        
        self.results.append(result)
        
        # Small delay between requests
        time.sleep(1)
        
        return result
    
    def run_tests(self, categories=None, max_per_category=None):
        """Run all tests"""
        self.start_time = time.time()
        
        print("\n" + "="*80)
        print("🧪 NLytics Automated Test Suite")
        print("="*80)
        
        # Create session
        if not self.create_session():
            return False
        
        # Upload file
        if not self.upload_file():
            return False
        
        # Wait a bit for preprocessing
        print("\n⏳ Waiting for preprocessing to complete...")
        time.sleep(3)
        
        # Run tests
        total_prompts = sum(
            len(prompts[:max_per_category] if max_per_category else prompts)
            for cat, prompts in TEST_PROMPTS.items()
            if categories is None or cat in categories
        )
        
        prompt_num = 0
        
        for category, prompts in TEST_PROMPTS.items():
            if categories and category not in categories:
                continue
            
            prompts_to_test = prompts[:max_per_category] if max_per_category else prompts
            
            for prompt in prompts_to_test:
                prompt_num += 1
                self.test_query(category, prompt, prompt_num, total_prompts)
        
        # Generate report
        self.generate_report()
        
        return True
    
    def generate_report(self):
        """Generate and print test report"""
        total_time = time.time() - self.start_time
        total_tests = len(self.results)
        successful = sum(1 for r in self.results if r['success'])
        failed = total_tests - successful
        
        avg_response_time = sum(r['response_time'] for r in self.results) / total_tests if total_tests > 0 else 0
        
        with_code = sum(1 for r in self.results if r['has_code'])
        with_viz = sum(1 for r in self.results if r['has_visualization'])
        with_insights = sum(1 for r in self.results if r['has_insights'])
        
        print("\n" + "="*80)
        print("📊 TEST RESULTS SUMMARY")
        print("="*80)
        print(f"\n⏱️  Total Test Duration: {total_time:.1f}s")
        print(f"📝 Total Tests: {total_tests}")
        print(f"✅ Successful: {successful} ({successful/total_tests*100:.1f}%)")
        print(f"❌ Failed: {failed} ({failed/total_tests*100:.1f}%)")
        print(f"\n⚡ Average Response Time: {avg_response_time:.2f}s")
        print(f"📝 Tests with Generated Code: {with_code} ({with_code/total_tests*100:.1f}%)")
        print(f"📊 Tests with Visualizations: {with_viz} ({with_viz/total_tests*100:.1f}%)")
        print(f"💡 Tests with Insights: {with_insights} ({with_insights/total_tests*100:.1f}%)")
        
        # Category breakdown
        print("\n📋 Results by Category:")
        categories = {}
        for r in self.results:
            cat = r['category']
            if cat not in categories:
                categories[cat] = {'total': 0, 'success': 0}
            categories[cat]['total'] += 1
            if r['success']:
                categories[cat]['success'] += 1
        
        for cat, stats in categories.items():
            success_rate = stats['success'] / stats['total'] * 100
            status = "✅" if success_rate == 100 else "⚠️" if success_rate >= 50 else "❌"
            print(f"   {status} {cat}: {stats['success']}/{stats['total']} ({success_rate:.0f}%)")
        
        # Failed tests
        if failed > 0:
            print(f"\n❌ Failed Tests ({failed}):")
            for r in self.results:
                if not r['success']:
                    print(f"   • {r['category']}: {r['prompt'][:60]}...")
                    print(f"     Error: {r['error']}")
        
        # Save detailed results to JSON
        self.save_results()
        
        print("\n" + "="*80)
    
    def save_results(self):
        """Save detailed results to JSON file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"test_results_{timestamp}.json"
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'total_tests': len(self.results),
            'successful': sum(1 for r in self.results if r['success']),
            'failed': sum(1 for r in self.results if not r['success']),
            'total_time': time.time() - self.start_time,
            'results': self.results
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Detailed results saved to: {filename}")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run automated NLytics tests')
    parser.add_argument('--categories', nargs='+', help='Specific categories to test')
    parser.add_argument('--max-per-category', type=int, help='Max prompts per category')
    parser.add_argument('--quick', action='store_true', help='Quick test (1 prompt per category)')
    
    args = parser.parse_args()
    
    runner = NLyticsTestRunner()
    
    if args.quick:
        print("🚀 Running QUICK test mode (1 prompt per category)")
        runner.run_tests(max_per_category=1)
    else:
        runner.run_tests(
            categories=args.categories,
            max_per_category=args.max_per_category
        )


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
