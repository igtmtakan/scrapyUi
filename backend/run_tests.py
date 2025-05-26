#!/usr/bin/env python3
"""
テスト実行スクリプト
結合テスト、統合テスト、パフォーマンステストを実行
"""
import subprocess
import sys
import time
import os
from pathlib import Path


def run_command(command, description):
    """コマンドを実行し、結果を表示"""
    print(f"\n{'='*60}")
    print(f"🧪 {description}")
    print(f"{'='*60}")
    print(f"実行コマンド: {command}")
    print("-" * 60)

    start_time = time.time()
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    end_time = time.time()

    print(f"実行時間: {end_time - start_time:.2f}秒")
    print(f"終了コード: {result.returncode}")

    if result.stdout:
        print("\n📤 標準出力:")
        print(result.stdout)

    if result.stderr:
        print("\n❌ エラー出力:")
        print(result.stderr)

    return result.returncode == 0


def check_dependencies():
    """依存関係をチェック"""
    print("🔍 依存関係をチェック中...")

    required_packages = [
        "pytest",
        "pytest-asyncio",
        "httpx",
        "fastapi",
        "sqlalchemy",
        "numpy",
        "psutil"
    ]

    missing_packages = []

    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} - 未インストール")
            missing_packages.append(package)

    if missing_packages:
        print(f"\n⚠️  以下のパッケージをインストールしてください:")
        print(f"pip install {' '.join(missing_packages)}")
        return False

    return True


def run_unit_tests():
    """ユニットテストを実行"""
    return run_command(
        "python -m pytest tests/ -v --tb=short -x",
        "ユニットテスト実行"
    )


def run_integration_tests():
    """統合テストを実行"""
    return run_command(
        "TESTING=1 python -m pytest tests/test_integration.py -v --tb=short",
        "統合テスト実行"
    )


def run_performance_tests():
    """パフォーマンステストを実行"""
    return run_command(
        "TESTING=1 python -m pytest tests/test_performance.py -v --tb=short -s",
        "パフォーマンステスト実行"
    )


def run_api_tests():
    """API テストを実行"""
    return run_command(
        "python -m pytest tests/ -k 'test_api' -v --tb=short",
        "API テスト実行"
    )


def run_coverage_tests():
    """カバレッジテストを実行"""
    return run_command(
        "python -m pytest tests/ --cov=app --cov-report=html --cov-report=term",
        "カバレッジテスト実行"
    )


def run_security_tests():
    """セキュリティテストを実行"""
    return run_command(
        "python -m pytest tests/ -k 'security' -v --tb=short",
        "セキュリティテスト実行"
    )


def run_load_tests():
    """負荷テストを実行"""
    return run_command(
        "python -m pytest tests/test_performance.py::TestAPIPerformance::test_concurrent_project_operations -v -s",
        "負荷テスト実行"
    )


def generate_test_report():
    """テストレポートを生成"""
    print("\n📊 テストレポート生成中...")

    # JUnit XML レポート生成
    run_command(
        "python -m pytest tests/ --junitxml=test_results.xml",
        "JUnit XMLレポート生成"
    )

    # HTML レポート生成
    run_command(
        "python -m pytest tests/ --html=test_report.html --self-contained-html",
        "HTMLレポート生成"
    )


def validate_api_endpoints():
    """API エンドポイントの検証"""
    print("\n🔍 API エンドポイント検証中...")

    # サーバーが起動しているかチェック
    try:
        import requests
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("✅ API サーバーが正常に動作しています")

            # Swagger UI の確認
            swagger_response = requests.get("http://localhost:8000/docs", timeout=5)
            if swagger_response.status_code == 200:
                print("✅ Swagger UI が正常にアクセス可能です")
            else:
                print("❌ Swagger UI にアクセスできません")

            # OpenAPI スキーマの確認
            openapi_response = requests.get("http://localhost:8000/openapi.json", timeout=5)
            if openapi_response.status_code == 200:
                print("✅ OpenAPI スキーマが正常に生成されています")
                schema = openapi_response.json()
                print(f"   - タイトル: {schema.get('info', {}).get('title', 'N/A')}")
                print(f"   - バージョン: {schema.get('info', {}).get('version', 'N/A')}")
                print(f"   - エンドポイント数: {len(schema.get('paths', {}))}")
            else:
                print("❌ OpenAPI スキーマにアクセスできません")

        else:
            print("❌ API サーバーが応答しません")
            return False

    except requests.exceptions.RequestException:
        print("❌ API サーバーに接続できません")
        print("   サーバーが起動していることを確認してください:")
        print("   uvicorn app.main:app --reload")
        return False

    return True


def main():
    """メイン実行関数"""
    print("🚀 ScrapyUI テストスイート実行開始")
    print("=" * 60)

    # 作業ディレクトリの確認
    current_dir = Path.cwd()
    print(f"📁 作業ディレクトリ: {current_dir}")

    # 依存関係チェック
    if not check_dependencies():
        print("\n❌ 依存関係の問題により、テストを中止します")
        sys.exit(1)

    # テスト結果を記録
    test_results = {}

    # API エンドポイント検証
    test_results["api_validation"] = validate_api_endpoints()

    # 各種テストの実行
    test_suites = [
        ("unit_tests", "ユニットテスト", run_unit_tests),
        ("integration_tests", "統合テスト", run_integration_tests),
        ("api_tests", "API テスト", run_api_tests),
        ("performance_tests", "パフォーマンステスト", run_performance_tests),
        ("security_tests", "セキュリティテスト", run_security_tests),
        ("load_tests", "負荷テスト", run_load_tests),
    ]

    for test_key, test_name, test_func in test_suites:
        try:
            test_results[test_key] = test_func()
        except Exception as e:
            print(f"\n❌ {test_name}実行中にエラーが発生しました: {e}")
            test_results[test_key] = False

    # カバレッジテスト（オプション）
    if "--coverage" in sys.argv:
        test_results["coverage"] = run_coverage_tests()

    # テストレポート生成
    if "--report" in sys.argv:
        generate_test_report()

    # 結果サマリー
    print("\n" + "=" * 60)
    print("📊 テスト結果サマリー")
    print("=" * 60)

    total_tests = len(test_results)
    passed_tests = sum(1 for result in test_results.values() if result)
    failed_tests = total_tests - passed_tests

    for test_name, result in test_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")

    print("-" * 60)
    print(f"📈 総テスト数: {total_tests}")
    print(f"✅ 成功: {passed_tests}")
    print(f"❌ 失敗: {failed_tests}")
    print(f"📊 成功率: {(passed_tests/total_tests)*100:.1f}%")

    # 推奨事項
    print("\n💡 推奨事項:")
    if failed_tests > 0:
        print("- 失敗したテストの詳細を確認し、問題を修正してください")
        print("- テストログを確認して根本原因を特定してください")

    if not test_results.get("api_validation", False):
        print("- API サーバーが起動していることを確認してください")
        print("- ネットワーク接続とポート設定を確認してください")

    print("- 定期的にテストを実行して品質を維持してください")
    print("- カバレッジレポートを確認してテスト範囲を拡大してください")

    # 終了コード
    if failed_tests == 0:
        print("\n🎉 すべてのテストが成功しました！")
        sys.exit(0)
    else:
        print(f"\n⚠️  {failed_tests}個のテストが失敗しました")
        sys.exit(1)


if __name__ == "__main__":
    main()
