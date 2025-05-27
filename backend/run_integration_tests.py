#!/usr/bin/env python3
"""
ScrapyUI 統合テスト実行スクリプト
"""
import os
import sys
import subprocess
import time
import argparse
import json
from pathlib import Path
from datetime import datetime


class IntegrationTestRunner:
    """統合テスト実行クラス"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.test_results = {}
        self.start_time = None
        
    def setup_environment(self):
        """テスト環境セットアップ"""
        print("🔧 Setting up test environment...")
        
        # 環境変数設定
        os.environ["TESTING"] = "true"
        os.environ["DATABASE_URL"] = "sqlite:///./test_integration.db"
        os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-integration"
        
        # テスト用ディレクトリ作成
        test_dirs = [
            "tests/integration/temp",
            "tests/integration/logs",
            "tests/integration/results"
        ]
        
        for test_dir in test_dirs:
            (self.project_root / test_dir).mkdir(parents=True, exist_ok=True)
        
        print("✅ Test environment setup completed")
    
    def check_dependencies(self):
        """依存関係チェック"""
        print("📦 Checking dependencies...")
        
        required_packages = [
            "pytest",
            "pytest-asyncio",
            "pytest-cov",
            "httpx",
            "websockets",
            "psutil"
        ]
        
        missing_packages = []
        for package in required_packages:
            try:
                __import__(package.replace("-", "_"))
            except ImportError:
                missing_packages.append(package)
        
        if missing_packages:
            print(f"❌ Missing packages: {', '.join(missing_packages)}")
            print("Please install them with: pip install " + " ".join(missing_packages))
            return False
        
        print("✅ All dependencies are available")
        return True
    
    def run_test_suite(self, test_type="all", verbose=False, coverage=False):
        """テストスイート実行"""
        print(f"🚀 Running {test_type} integration tests...")
        self.start_time = time.time()
        
        # pytest コマンド構築
        cmd = ["python", "-m", "pytest"]
        
        # テストタイプに応じたフィルター
        if test_type == "full_system":
            cmd.extend(["-m", "integration", "tests/integration/test_full_system_integration.py"])
        elif test_type == "nodejs":
            cmd.extend(["-m", "integration", "tests/integration/test_nodejs_integration.py"])
        elif test_type == "websocket":
            cmd.extend(["-m", "websocket", "tests/integration/test_websocket_integration.py"])
        elif test_type == "performance":
            cmd.extend(["-m", "performance", "tests/integration/test_performance_integration.py"])
        elif test_type == "e2e":
            cmd.extend(["-m", "e2e", "tests/integration/test_e2e_integration.py"])
        elif test_type == "all":
            cmd.extend(["tests/integration/"])
        else:
            cmd.extend([f"tests/integration/test_{test_type}_integration.py"])
        
        # オプション追加
        if verbose:
            cmd.extend(["-v", "-s"])
        
        if coverage:
            cmd.extend([
                "--cov=app",
                "--cov-report=html:tests/integration/results/coverage_html",
                "--cov-report=json:tests/integration/results/coverage.json",
                "--cov-report=term"
            ])
        
        # JUnit XML レポート
        cmd.extend([
            "--junit-xml=tests/integration/results/junit.xml",
            "--tb=short"
        ])
        
        # テスト実行
        try:
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=1800  # 30分タイムアウト
            )
            
            self.test_results[test_type] = {
                "return_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "execution_time": time.time() - self.start_time
            }
            
            if result.returncode == 0:
                print(f"✅ {test_type} tests passed")
            else:
                print(f"❌ {test_type} tests failed")
                if verbose:
                    print("STDOUT:", result.stdout)
                    print("STDERR:", result.stderr)
            
            return result.returncode == 0
            
        except subprocess.TimeoutExpired:
            print(f"⏰ {test_type} tests timed out")
            return False
        except Exception as e:
            print(f"💥 Error running {test_type} tests: {e}")
            return False
    
    def run_specific_tests(self, test_patterns, verbose=False):
        """特定のテスト実行"""
        print(f"🎯 Running specific tests: {', '.join(test_patterns)}")
        
        cmd = ["python", "-m", "pytest"]
        cmd.extend(test_patterns)
        
        if verbose:
            cmd.extend(["-v", "-s"])
        
        try:
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                print("✅ Specific tests passed")
            else:
                print("❌ Specific tests failed")
                if verbose:
                    print("STDOUT:", result.stdout)
                    print("STDERR:", result.stderr)
            
            return result.returncode == 0
            
        except Exception as e:
            print(f"💥 Error running specific tests: {e}")
            return False
    
    def generate_report(self):
        """テストレポート生成"""
        print("📊 Generating test report...")
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "total_execution_time": time.time() - self.start_time if self.start_time else 0,
            "test_results": self.test_results,
            "summary": {
                "total_suites": len(self.test_results),
                "passed_suites": sum(1 for r in self.test_results.values() if r["return_code"] == 0),
                "failed_suites": sum(1 for r in self.test_results.values() if r["return_code"] != 0)
            }
        }
        
        # JSON レポート保存
        report_file = self.project_root / "tests/integration/results/integration_test_report.json"
        with open(report_file, "w") as f:
            json.dump(report, f, indent=2)
        
        # コンソール出力
        print("\n" + "=" * 60)
        print("📋 INTEGRATION TEST REPORT")
        print("=" * 60)
        print(f"Total execution time: {report['total_execution_time']:.2f} seconds")
        print(f"Test suites run: {report['summary']['total_suites']}")
        print(f"Passed: {report['summary']['passed_suites']}")
        print(f"Failed: {report['summary']['failed_suites']}")
        
        for test_type, result in self.test_results.items():
            status = "✅ PASSED" if result["return_code"] == 0 else "❌ FAILED"
            print(f"  {test_type}: {status} ({result['execution_time']:.2f}s)")
        
        print(f"\nDetailed report saved to: {report_file}")
        
        return report
    
    def cleanup(self):
        """テスト後のクリーンアップ"""
        print("🧹 Cleaning up test environment...")
        
        # テスト用データベース削除
        test_db_files = [
            "test_integration.db",
            "test_integration.db-shm",
            "test_integration.db-wal"
        ]
        
        for db_file in test_db_files:
            db_path = self.project_root / db_file
            if db_path.exists():
                db_path.unlink()
        
        print("✅ Cleanup completed")


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(description="ScrapyUI Integration Test Runner")
    parser.add_argument(
        "--type",
        choices=["all", "full_system", "nodejs", "websocket", "performance", "e2e"],
        default="all",
        help="Test type to run"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output"
    )
    parser.add_argument(
        "--coverage", "-c",
        action="store_true",
        help="Generate coverage report"
    )
    parser.add_argument(
        "--specific", "-s",
        nargs="+",
        help="Run specific test files or patterns"
    )
    parser.add_argument(
        "--no-cleanup",
        action="store_true",
        help="Skip cleanup after tests"
    )
    
    args = parser.parse_args()
    
    runner = IntegrationTestRunner()
    
    try:
        # 環境セットアップ
        runner.setup_environment()
        
        # 依存関係チェック
        if not runner.check_dependencies():
            sys.exit(1)
        
        # テスト実行
        success = True
        
        if args.specific:
            # 特定のテスト実行
            success = runner.run_specific_tests(args.specific, args.verbose)
        else:
            # テストスイート実行
            if args.type == "all":
                # 全テストタイプを順次実行
                test_types = ["full_system", "nodejs", "websocket", "performance", "e2e"]
                for test_type in test_types:
                    result = runner.run_test_suite(test_type, args.verbose, args.coverage)
                    if not result:
                        success = False
            else:
                success = runner.run_test_suite(args.type, args.verbose, args.coverage)
        
        # レポート生成
        report = runner.generate_report()
        
        # 結果に応じた終了コード
        if success:
            print("\n🎉 All integration tests completed successfully!")
            exit_code = 0
        else:
            print("\n💥 Some integration tests failed!")
            exit_code = 1
        
    except KeyboardInterrupt:
        print("\n⚠️ Tests interrupted by user")
        exit_code = 130
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        exit_code = 1
    finally:
        # クリーンアップ
        if not args.no_cleanup:
            runner.cleanup()
    
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
