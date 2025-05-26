import json
import pandas as pd
import os
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

class ExportService:
    """データエクスポートサービス"""

    def __init__(self):
        self.export_dir = Path(tempfile.gettempdir()) / "scrapy_exports"
        self.export_dir.mkdir(exist_ok=True)

    def export_to_json(self, data: List[Dict[str, Any]], filename: Optional[str] = None) -> str:
        """JSONエクスポート"""
        if filename is None:
            filename = f"export_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.json"

        filepath = self.export_dir / filename

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        return str(filepath)

    def export_to_csv(self, data: List[Dict[str, Any]], filename: Optional[str] = None) -> str:
        """CSVエクスポート"""
        if filename is None:
            filename = f"export_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv"

        filepath = self.export_dir / filename

        if not data:
            # 空のCSVファイルを作成
            pd.DataFrame().to_csv(filepath, index=False)
            return str(filepath)

        # データをフラット化
        flattened_data = self._flatten_data(data)
        df = pd.DataFrame(flattened_data)
        df.to_csv(filepath, index=False, encoding='utf-8')

        return str(filepath)

    def export_to_excel(self, data: List[Dict[str, Any]], filename: Optional[str] = None) -> str:
        """Excelエクスポート"""
        if filename is None:
            filename = f"export_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

        filepath = self.export_dir / filename

        if not data:
            # 空のExcelファイルを作成
            pd.DataFrame().to_excel(filepath, index=False)
            return str(filepath)

        # データをフラット化
        flattened_data = self._flatten_data(data)
        df = pd.DataFrame(flattened_data)
        df.to_excel(filepath, index=False)

        return str(filepath)

    def export_to_xml(self, data: List[Dict[str, Any]], filename: Optional[str] = None) -> str:
        """XMLエクスポート"""
        if filename is None:
            filename = f"export_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.xml"

        filepath = self.export_dir / filename

        root = ET.Element("data")

        for item in data:
            item_element = ET.SubElement(root, "item")
            for key, value in item.items():
                if isinstance(value, dict):
                    # ネストされた辞書は文字列として保存
                    value = json.dumps(value)
                elif isinstance(value, list):
                    # リストは文字列として保存
                    value = json.dumps(value)

                child = ET.SubElement(item_element, key)
                child.text = str(value) if value is not None else ""

        tree = ET.ElementTree(root)
        tree.write(filepath, encoding='utf-8', xml_declaration=True)

        return str(filepath)

    def export_to_parquet(self, data: List[Dict[str, Any]], filename: Optional[str] = None) -> str:
        """Parquetエクスポート"""
        if filename is None:
            filename = f"export_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.parquet"

        filepath = self.export_dir / filename

        if not data:
            # 空のParquetファイルを作成
            pd.DataFrame().to_parquet(filepath, index=False)
            return str(filepath)

        # データをフラット化
        flattened_data = self._flatten_data(data)
        df = pd.DataFrame(flattened_data)
        df.to_parquet(filepath, index=False)

        return str(filepath)

    def export_with_template(
        self,
        data: List[Dict[str, Any]],
        template_type: str = "scrapy_results",
        custom_fields: Optional[List[str]] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> str:
        """テンプレートを使用したエクスポート"""

        # フィルタリング
        if filters:
            data = self._apply_filters(data, filters)

        # フィールド選択
        if custom_fields:
            data = self._select_fields(data, custom_fields)

        if template_type == "scrapy_results":
            return self._export_scrapy_results_template(data)
        else:
            return self.export_to_excel(data)

    def _export_scrapy_results_template(self, data: List[Dict[str, Any]]) -> str:
        """Scrapy結果テンプレートエクスポート"""
        filename = f"scrapy_results_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        filepath = self.export_dir / filename

        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            # 結果シート
            if data:
                flattened_data = self._flatten_data(data)
                results_df = pd.DataFrame(flattened_data)
            else:
                results_df = pd.DataFrame()
            results_df.to_excel(writer, sheet_name='Results', index=False)

            # サマリーシート
            summary_data = {
                'Total Results': [len(data)],
                'Export Date': [pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')]
            }
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(writer, sheet_name='Summary', index=False)

            # 統計シート
            if data and flattened_data:
                stats_data = []
                for field in results_df.columns:
                    stats_data.append({
                        'Field': field,
                        'Type': str(results_df[field].dtype),
                        'Non-null Count': results_df[field].count()
                    })
                stats_df = pd.DataFrame(stats_data)
            else:
                stats_df = pd.DataFrame({'Field': [], 'Type': [], 'Non-null Count': []})
            stats_df.to_excel(writer, sheet_name='Statistics', index=False)

        return str(filepath)

    def _flatten_data(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """データをフラット化"""
        if not data:
            return []

        flattened = []
        for item in data:
            flat_item = self._flatten_dict(item)
            flattened.append(flat_item)

        return flattened

    def _flatten_dict(self, d: Dict[str, Any], parent_key: str = '', sep: str = '_') -> Dict[str, Any]:
        """辞書を再帰的にフラット化"""
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(self._flatten_dict(v, new_key, sep=sep).items())
            elif isinstance(v, list):
                # リストは文字列として保存
                items.append((new_key, json.dumps(v)))
            else:
                items.append((new_key, v))
        return dict(items)

    def _apply_filters(self, data: List[Dict[str, Any]], filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """フィルタを適用"""
        filtered_data = data

        # 日付フィルタ
        if 'date_from' in filters and 'date_to' in filters and 'date_field' in filters:
            date_field = filters['date_field']
            date_from = pd.to_datetime(filters['date_from'])
            date_to = pd.to_datetime(filters['date_to'])

            filtered_data = [
                item for item in filtered_data
                if date_field in item and
                date_from <= pd.to_datetime(item[date_field]) <= date_to
            ]

        return filtered_data

    def _select_fields(self, data: List[Dict[str, Any]], fields: List[str]) -> List[Dict[str, Any]]:
        """指定されたフィールドのみを選択"""
        if not data:
            return data

        selected_data = []
        for item in data:
            selected_item = {}
            for field in fields:
                if field in item:
                    selected_item[field] = item[field]
            selected_data.append(selected_item)

        return selected_data