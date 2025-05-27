import os
import re
import ast
from typing import Dict, List, Tuple, Optional
from sqlalchemy.orm import Session
from pathlib import Path

from ..database import SessionLocal, Spider as DBSpider, Project as DBProject
from ..services.scrapy_service import ScrapyPlaywrightService


class DatabaseFileSystemIntegrityService:
    """
    データベースとファイルシステムの整合性を管理するサービス
    """

    def __init__(self):
        self.scrapy_service = ScrapyPlaywrightService()
        self.base_dir = Path("scrapy_projects")

    def scan_all_spider_files(self) -> Dict[str, Dict]:
        """
        全プロジェクトのスパイダーファイルをスキャンして情報を取得
        """
        spider_files = {}

        if not self.base_dir.exists():
            print(f"❌ Base directory {self.base_dir} does not exist")
            return spider_files

        # 全プロジェクトディレクトリをスキャン
        for project_dir in self.base_dir.iterdir():
            if not project_dir.is_dir():
                continue

            project_name = project_dir.name
            spiders_dir = project_dir / project_name / "spiders"

            if not spiders_dir.exists():
                continue

            # スパイダーファイルをスキャン
            for spider_file in spiders_dir.glob("*.py"):
                if spider_file.name == "__init__.py":
                    continue

                spider_info = self._extract_spider_info(spider_file, project_name)
                if spider_info:
                    key = f"{project_name}:{spider_info['name']}"
                    spider_files[key] = spider_info

        return spider_files

    def _extract_spider_info(self, file_path: Path, project_name: str) -> Optional[Dict]:
        """
        スパイダーファイルから情報を抽出
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # name属性を抽出
            name_match = re.search(r'name\s*=\s*[\'"]([^\'"]+)[\'"]', content)
            if not name_match:
                return None

            spider_name = name_match.group(1)

            # クラス名を抽出
            class_match = re.search(r'class\s+(\w+)\s*\([^)]*Spider[^)]*\)', content)
            class_name = class_match.group(1) if class_match else "UnknownSpider"

            return {
                'name': spider_name,
                'class_name': class_name,
                'file_path': str(file_path),
                'project_name': project_name,
                'file_exists': True,
                'content_preview': content[:200] + "..." if len(content) > 200 else content
            }

        except Exception as e:
            print(f"❌ Error reading {file_path}: {e}")
            return None

    def get_database_spiders(self) -> Dict[str, Dict]:
        """
        データベースから全スパイダー情報を取得
        """
        db = SessionLocal()
        database_spiders = {}

        try:
            spiders = db.query(DBSpider).all()
            projects = {p.id: p.name for p in db.query(DBProject).all()}

            for spider in spiders:
                project_name = projects.get(spider.project_id, "unknown_project")
                key = f"{project_name}:{spider.name}"

                database_spiders[key] = {
                    'id': spider.id,
                    'name': spider.name,
                    'project_id': spider.project_id,
                    'project_name': project_name,
                    'created_at': spider.created_at,
                    'updated_at': spider.updated_at,
                    'code': spider.code,  # 'script' -> 'code'に修正
                    'in_database': True
                }

        except Exception as e:
            print(f"❌ Error querying database: {e}")
        finally:
            db.close()

        return database_spiders

    def check_integrity(self) -> Dict:
        """
        整合性をチェックして問題を特定
        """
        print("🔍 Starting integrity check...")

        # ファイルシステムとデータベースの情報を取得
        file_spiders = self.scan_all_spider_files()
        db_spiders = self.get_database_spiders()

        # 整合性チェック結果
        result = {
            'file_only': {},      # ファイルのみ存在
            'db_only': {},        # データベースのみ存在
            'both_exist': {},     # 両方存在
            'mismatched': {},     # 内容不一致
            'summary': {}
        }

        # ファイルのみ存在するスパイダー
        for key, spider in file_spiders.items():
            if key not in db_spiders:
                result['file_only'][key] = spider

        # データベースのみ存在するスパイダー
        for key, spider in db_spiders.items():
            if key not in file_spiders:
                result['db_only'][key] = spider

        # 両方存在するスパイダー
        for key in set(file_spiders.keys()) & set(db_spiders.keys()):
            result['both_exist'][key] = {
                'file': file_spiders[key],
                'database': db_spiders[key]
            }

        # サマリー
        result['summary'] = {
            'total_files': len(file_spiders),
            'total_database': len(db_spiders),
            'file_only_count': len(result['file_only']),
            'db_only_count': len(result['db_only']),
            'both_exist_count': len(result['both_exist']),
            'integrity_ok': len(result['file_only']) == 0 and len(result['db_only']) == 0
        }

        return result

    def fix_integrity_issues(self, auto_fix: bool = False) -> Dict:
        """
        整合性の問題を修復
        """
        print("🔧 Starting integrity fix...")

        integrity_result = self.check_integrity()
        fix_result = {
            'removed_orphaned_db_entries': [],
            'created_missing_db_entries': [],
            'errors': [],
            'summary': {}
        }

        db = SessionLocal()

        try:
            # データベースのみ存在する（孤立した）エントリを削除
            for key, spider in integrity_result['db_only'].items():
                try:
                    if auto_fix:
                        db_spider = db.query(DBSpider).filter(DBSpider.id == spider['id']).first()
                        if db_spider:
                            db.delete(db_spider)
                            fix_result['removed_orphaned_db_entries'].append({
                                'id': spider['id'],
                                'name': spider['name'],
                                'project': spider['project_name']
                            })
                            print(f"🗑️ Removed orphaned spider: {spider['name']} (ID: {spider['id']})")
                    else:
                        print(f"⚠️ Would remove orphaned spider: {spider['name']} (ID: {spider['id']})")

                except Exception as e:
                    error_msg = f"Error removing spider {spider['name']}: {str(e)}"
                    fix_result['errors'].append(error_msg)
                    print(f"❌ {error_msg}")

            if auto_fix:
                db.commit()
                print("✅ Database cleanup completed")
            else:
                print("ℹ️ Dry run completed - no changes made")

        except Exception as e:
            db.rollback()
            error_msg = f"Database operation failed: {str(e)}"
            fix_result['errors'].append(error_msg)
            print(f"❌ {error_msg}")
        finally:
            db.close()

        # サマリー
        fix_result['summary'] = {
            'orphaned_entries_found': len(integrity_result['db_only']),
            'orphaned_entries_removed': len(fix_result['removed_orphaned_db_entries']),
            'missing_entries_found': len(integrity_result['file_only']),
            'missing_entries_created': len(fix_result['created_missing_db_entries']),
            'errors_count': len(fix_result['errors']),
            'auto_fix_enabled': auto_fix
        }

        return fix_result

    def generate_integrity_report(self) -> str:
        """
        整合性レポートを生成
        """
        integrity_result = self.check_integrity()

        report = []
        report.append("📊 DATABASE-FILESYSTEM INTEGRITY REPORT")
        report.append("=" * 60)
        report.append("")

        # サマリー
        summary = integrity_result['summary']
        report.append(f"📈 SUMMARY:")
        report.append(f"  Total Files: {summary['total_files']}")
        report.append(f"  Total Database: {summary['total_database']}")
        report.append(f"  File Only: {summary['file_only_count']}")
        report.append(f"  Database Only: {summary['db_only_count']}")
        report.append(f"  Both Exist: {summary['both_exist_count']}")
        report.append(f"  Integrity OK: {'✅' if summary['integrity_ok'] else '❌'}")
        report.append("")

        # ファイルのみ存在
        if integrity_result['file_only']:
            report.append("📁 FILES WITHOUT DATABASE ENTRIES:")
            for key, spider in integrity_result['file_only'].items():
                report.append(f"  📄 {spider['name']} ({spider['project_name']})")
                report.append(f"     File: {spider['file_path']}")
            report.append("")

        # データベースのみ存在
        if integrity_result['db_only']:
            report.append("🗄️ DATABASE ENTRIES WITHOUT FILES:")
            for key, spider in integrity_result['db_only'].items():
                report.append(f"  🕷️ {spider['name']} ({spider['project_name']})")
                report.append(f"     ID: {spider['id']}")
                report.append(f"     Created: {spider['created_at']}")
            report.append("")

        # 両方存在
        if integrity_result['both_exist']:
            report.append("✅ SYNCHRONIZED SPIDERS:")
            for key, data in integrity_result['both_exist'].items():
                spider = data['file']
                report.append(f"  🔗 {spider['name']} ({spider['project_name']})")
            report.append("")

        return "\n".join(report)


# グローバルインスタンス
integrity_service = DatabaseFileSystemIntegrityService()
