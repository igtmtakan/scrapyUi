'use client';

import React, { useState } from 'react';
import { Trash2, AlertTriangle, CheckCircle, Loader2 } from 'lucide-react';
import { apiClient } from '@/lib/api';

interface ClearResult {
  status: string;
  cleared_tasks: {
    celery_active: number;
    celery_reserved: number;
    db_running: number;
    db_pending: number;
  };
  operations: string[];
  final_status: {
    running_tasks: number;
    pending_tasks: number;
    all_cleared: boolean;
  };
}

export function WorkerTaskClearButton() {
  const [isOpen, setIsOpen] = useState(false);
  const [isClearing, setIsClearing] = useState(false);
  const [clearResult, setClearResult] = useState<ClearResult | null>(null);

  const handleClearTasks = async () => {
    setIsClearing(true);
    setClearResult(null);

    try {
      const result = await apiClient.clearWorkerTasks();
      setClearResult(result);

      if (result.final_status.all_cleared) {
        alert(`ワーカータスクのクリアが完了しました\n${result.cleared_tasks.celery_active + result.cleared_tasks.celery_reserved + result.cleared_tasks.db_running + result.cleared_tasks.db_pending}件のタスクをクリアしました`);
      } else {
        alert(`一部のタスクが残っています\n実行中: ${result.final_status.running_tasks}件, ペンディング: ${result.final_status.pending_tasks}件`);
      }
    } catch (error) {
      console.error('Worker task clear error:', error);
      alert(`ワーカータスクのクリアに失敗しました\n${error instanceof Error ? error.message : '不明なエラーが発生しました'}`);
    } finally {
      setIsClearing(false);
    }
  };

  const getTotalClearedTasks = (cleared: ClearResult['cleared_tasks']) => {
    return cleared.celery_active + cleared.celery_reserved + cleared.db_running + cleared.db_pending;
  };

  const getBadgeClass = (count: number) => {
    return count === 0
      ? "inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800"
      : "inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800";
  };

  return (
    <>
      <button
        onClick={() => setIsOpen(true)}
        className="inline-flex items-center px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed text-sm gap-2"
        title="すべてのワーカータスクをクリアします"
      >
        <Trash2 className="h-4 w-4" />
        ワーカークリア
      </button>

      {isOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-4xl max-h-[90vh] overflow-y-auto">
            <div className="flex items-center gap-2 mb-4">
              <AlertTriangle className="h-5 w-5 text-orange-500" />
              <h2 className="text-xl font-bold">ワーカータスククリア</h2>
            </div>

            <p className="text-gray-600 mb-6">
              すべてのCeleryワーカータスクとデータベース内のアクティブなタスクをクリアします。
              この操作は取り消すことができません。
            </p>

            <div className="space-y-4">
              <div className="p-4 bg-orange-50 border border-orange-200 rounded-md">
                <div className="flex items-center gap-2 mb-2">
                  <AlertTriangle className="h-4 w-4 text-orange-600" />
                  <h3 className="font-medium text-orange-800">注意事項</h3>
                </div>
                <div className="text-sm text-orange-700">
                  この操作により以下が実行されます：
                  <ul className="mt-2 list-disc list-inside space-y-1">
                    <li>アクティブなCeleryタスクの取り消し</li>
                    <li>予約されたCeleryタスクの取り消し</li>
                    <li>Celeryキューのパージ</li>
                    <li>データベース内の実行中・ペンディングタスクをキャンセル状態に変更</li>
                    <li>実行中のScrapyプロセスの停止</li>
                  </ul>
                </div>
              </div>

              {clearResult && (
                <div className="space-y-3">
                  <div className="flex items-center gap-2">
                    {clearResult.final_status.all_cleared ? (
                      <CheckCircle className="h-5 w-5 text-green-500" />
                    ) : (
                      <AlertTriangle className="h-5 w-5 text-orange-500" />
                    )}
                    <h3 className="font-semibold">
                      {clearResult.final_status.all_cleared ? 'クリア完了' : 'クリア結果'}
                    </h3>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <h4 className="text-sm font-medium">クリアされたタスク</h4>
                      <div className="space-y-1">
                        <div className="flex justify-between text-sm">
                          <span>Celeryアクティブ:</span>
                          <span className={getBadgeClass(clearResult.cleared_tasks.celery_active)}>
                            {clearResult.cleared_tasks.celery_active}
                          </span>
                        </div>
                        <div className="flex justify-between text-sm">
                          <span>Celery予約:</span>
                          <span className={getBadgeClass(clearResult.cleared_tasks.celery_reserved)}>
                            {clearResult.cleared_tasks.celery_reserved}
                          </span>
                        </div>
                        <div className="flex justify-between text-sm">
                          <span>DB実行中:</span>
                          <span className={getBadgeClass(clearResult.cleared_tasks.db_running)}>
                            {clearResult.cleared_tasks.db_running}
                          </span>
                        </div>
                        <div className="flex justify-between text-sm">
                          <span>DBペンディング:</span>
                          <span className={getBadgeClass(clearResult.cleared_tasks.db_pending)}>
                            {clearResult.cleared_tasks.db_pending}
                          </span>
                        </div>
                        <div className="flex justify-between text-sm font-medium border-t pt-1">
                          <span>合計:</span>
                          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                            {getTotalClearedTasks(clearResult.cleared_tasks)}
                          </span>
                        </div>
                      </div>
                    </div>

                    <div className="space-y-2">
                      <h4 className="text-sm font-medium">最終状態</h4>
                      <div className="space-y-1">
                        <div className="flex justify-between text-sm">
                          <span>実行中タスク:</span>
                          <span className={clearResult.final_status.running_tasks === 0 ? getBadgeClass(0) : getBadgeClass(1)}>
                            {clearResult.final_status.running_tasks}
                          </span>
                        </div>
                        <div className="flex justify-between text-sm">
                          <span>ペンディングタスク:</span>
                          <span className={clearResult.final_status.pending_tasks === 0 ? getBadgeClass(0) : getBadgeClass(1)}>
                            {clearResult.final_status.pending_tasks}
                          </span>
                        </div>
                        <div className="flex justify-between text-sm font-medium border-t pt-1">
                          <span>ステータス:</span>
                          <span className={clearResult.final_status.all_cleared ? getBadgeClass(0) : getBadgeClass(1)}>
                            {clearResult.final_status.all_cleared ? "完全クリア" : "一部残存"}
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="space-y-2">
                    <h4 className="text-sm font-medium">実行ログ</h4>
                    <div className="bg-gray-50 p-3 rounded-md max-h-32 overflow-y-auto">
                      <ul className="space-y-1 text-xs">
                        {clearResult.operations.map((operation, index) => (
                          <li key={index} className="flex items-start gap-2">
                            <span className="text-gray-500">{index + 1}.</span>
                            <span>{operation}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  </div>
                </div>
              )}
            </div>

            <div className="flex justify-end space-x-3 pt-6">
              <button
                type="button"
                onClick={() => setIsOpen(false)}
                className="px-4 py-2 text-gray-600 border border-gray-300 rounded-md hover:bg-gray-50"
              >
                閉じる
              </button>
              {!clearResult && (
                <button
                  onClick={handleClearTasks}
                  disabled={isClearing}
                  className="inline-flex items-center px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed gap-2"
                >
                  {isClearing ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin" />
                      クリア中...
                    </>
                  ) : (
                    <>
                      <Trash2 className="h-4 w-4" />
                      実行
                    </>
                  )}
                </button>
              )}
            </div>
          </div>
        </div>
      )}
    </>
  );
}
