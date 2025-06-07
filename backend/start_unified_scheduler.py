#!/usr/bin/env python3
"""
統一スケジューラー起動スクリプト
根本対応後の統一スケジューラーを起動
"""

import signal
import sys
import logging
from pathlib import Path

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('unified_scheduler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def signal_handler(sig, frame):
    """シグナルハンドラー"""
    logger.info('\n🛑 統一スケジューラーを停止中...')
    try:
        from app.services.scheduler_service import scheduler_service
        scheduler_service.stop()
        logger.info('✅ 統一スケジューラーが停止しました')
    except Exception as e:
        logger.error(f'❌ 停止エラー: {str(e)}')
    sys.exit(0)

def main():
    """メイン関数"""
    try:
        # シグナルハンドラーを設定
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        logger.info('🚀 統一スケジューラーを起動中...')
        
        # スケジューラーサービスをインポート
        from app.services.scheduler_service import scheduler_service
        
        # スケジューラーを起動
        scheduler_service.start()
        logger.info('✅ 統一スケジューラーが起動しました')
        
        # スケジューラーの状態を表示
        status = scheduler_service.get_status()
        logger.info(f'📊 スケジューラー状態: {status.get("running", False)}')
        logger.info(f'📋 アクティブなスケジュール: {status.get("active_schedules", 0)}個')
        
        # 無限ループで待機
        try:
            while True:
                import time
                time.sleep(1)
        except KeyboardInterrupt:
            signal_handler(None, None)
            
    except Exception as e:
        logger.error(f'❌ 統一スケジューラー起動エラー: {str(e)}')
        sys.exit(1)

if __name__ == "__main__":
    main()
