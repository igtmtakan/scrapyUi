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
    """メイン関数（根本対応版）"""
    restart_count = 0
    max_restarts = 5

    while restart_count < max_restarts:
        try:
            # シグナルハンドラーを設定
            signal.signal(signal.SIGINT, signal_handler)
            signal.signal(signal.SIGTERM, signal_handler)

            logger.info(f'🚀 統一スケジューラーを起動中... (試行 {restart_count + 1}/{max_restarts})')

            # スケジューラーサービスをインポート
            from app.services.scheduler_service import scheduler_service

            # スケジューラーを起動
            scheduler_service.start()
            logger.info('✅ 統一スケジューラーが起動しました')

            # スケジューラーの状態を表示
            status = scheduler_service.get_status()
            logger.info(f'📊 スケジューラー状態: {status.get("running", False)}')
            logger.info(f'📋 アクティブなスケジュール: {status.get("active_schedules", 0)}個')

            # 健全性監視ループ
            last_health_check = 0
            health_check_interval = 60  # 60秒ごとに健全性チェック

            try:
                while True:
                    import time
                    current_time = time.time()

                    # 定期的な健全性チェック
                    if current_time - last_health_check > health_check_interval:
                        status = scheduler_service.get_status()
                        if not status.get("running", False):
                            logger.warning("⚠️ スケジューラーが停止しています。再起動を試行...")
                            raise Exception("Scheduler stopped unexpectedly")

                        last_health_check = current_time
                        logger.info(f"💓 Health check passed - Active schedules: {status.get('active_schedules', 0)}")

                    time.sleep(1)

            except KeyboardInterrupt:
                signal_handler(None, None)
                break

        except Exception as e:
            restart_count += 1
            logger.error(f'❌ 統一スケジューラーエラー (試行 {restart_count}/{max_restarts}): {str(e)}')

            if restart_count < max_restarts:
                wait_time = min(restart_count * 10, 60)  # 指数バックオフ（最大60秒）
                logger.info(f'🔄 {wait_time}秒後に再起動を試行します...')
                import time
                time.sleep(wait_time)
            else:
                logger.error('❌ 最大再起動回数に達しました。終了します。')
                sys.exit(1)

if __name__ == "__main__":
    main()
