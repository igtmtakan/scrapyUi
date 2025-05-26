'use client';

import { useState, useEffect } from 'react';
import { 
  GitBranch, 
  GitCommit, 
  GitMerge, 
  History, 
  Plus, 
  Save,
  RefreshCw,
  Clock,
  User,
  MessageSquare
} from 'lucide-react';
import { apiClient } from '@/lib/api';

interface Commit {
  hash: string;
  author_name: string;
  author_email: string;
  date: string;
  message: string;
}

interface GitStatus {
  modified: string[];
  added: string[];
  deleted: string[];
  untracked: string[];
}

interface GitIntegrationProps {
  projectId: string;
}

export default function GitIntegration({ projectId }: GitIntegrationProps) {
  const [isInitialized, setIsInitialized] = useState(false);
  const [status, setStatus] = useState<GitStatus | null>(null);
  const [commits, setCommits] = useState<Commit[]>([]);
  const [branches, setBranches] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [commitMessage, setCommitMessage] = useState('');
  const [newBranchName, setNewBranchName] = useState('');
  const [showCommitForm, setShowCommitForm] = useState(false);
  const [showBranchForm, setShowBranchForm] = useState(false);

  useEffect(() => {
    loadGitData();
  }, [projectId]);

  const loadGitData = async () => {
    try {
      setIsLoading(true);
      
      // Gitステータスを取得
      try {
        const statusData = await apiClient.request(`/api/projects/${projectId}/git/status`);
        setStatus(statusData);
        setIsInitialized(true);
        
        // コミット履歴とブランチを取得
        const [commitsData, branchesData] = await Promise.all([
          apiClient.request(`/api/projects/${projectId}/git/commits`),
          apiClient.request(`/api/projects/${projectId}/git/branches`)
        ]);
        
        setCommits(commitsData.commits || []);
        setBranches(branchesData.branches || []);
        
      } catch (error) {
        // Gitが初期化されていない場合
        setIsInitialized(false);
      }
    } catch (error) {
      console.error('Failed to load Git data:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const initializeGit = async () => {
    try {
      await apiClient.request(`/api/projects/${projectId}/git/init`, {
        method: 'POST'
      });
      
      alert('Gitリポジトリが初期化されました');
      await loadGitData();
    } catch (error) {
      console.error('Failed to initialize Git:', error);
      alert('Gitリポジトリの初期化に失敗しました');
    }
  };

  const createCommit = async () => {
    if (!commitMessage.trim()) {
      alert('コミットメッセージを入力してください');
      return;
    }

    try {
      await apiClient.request(`/api/projects/${projectId}/git/commit`, {
        method: 'POST',
        body: JSON.stringify({
          message: commitMessage,
          author: 'ScrapyUI User'
        })
      });

      setCommitMessage('');
      setShowCommitForm(false);
      alert('コミットが作成されました');
      await loadGitData();
    } catch (error) {
      console.error('Failed to create commit:', error);
      alert('コミットの作成に失敗しました');
    }
  };

  const createBranch = async () => {
    if (!newBranchName.trim()) {
      alert('ブランチ名を入力してください');
      return;
    }

    try {
      await apiClient.request(`/api/projects/${projectId}/git/branches`, {
        method: 'POST',
        body: JSON.stringify({
          name: newBranchName
        })
      });

      setNewBranchName('');
      setShowBranchForm(false);
      alert('ブランチが作成されました');
      await loadGitData();
    } catch (error) {
      console.error('Failed to create branch:', error);
      alert('ブランチの作成に失敗しました');
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString('ja-JP');
  };

  if (isLoading) {
    return (
      <div className="bg-gray-800 rounded-lg p-6">
        <div className="flex items-center justify-center">
          <RefreshCw className="h-6 w-6 animate-spin text-blue-400" />
          <span className="ml-2 text-gray-300">Git情報を読み込み中...</span>
        </div>
      </div>
    );
  }

  if (!isInitialized) {
    return (
      <div className="bg-gray-800 rounded-lg p-6">
        <div className="text-center">
          <GitBranch className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-white mb-2">Gitリポジトリが初期化されていません</h3>
          <p className="text-gray-400 mb-4">
            バージョン管理を開始するには、Gitリポジトリを初期化してください。
          </p>
          <button
            onClick={initializeGit}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
          >
            Gitリポジトリを初期化
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Git Status */}
      <div className="bg-gray-800 rounded-lg p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-blue-400 flex items-center">
            <GitBranch className="h-5 w-5 mr-2" />
            Git ステータス
          </h3>
          <button
            onClick={loadGitData}
            className="p-2 text-gray-400 hover:text-white transition-colors"
          >
            <RefreshCw className="h-4 w-4" />
          </button>
        </div>

        {status && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-gray-700 rounded-lg p-3">
              <div className="text-sm text-gray-400">変更済み</div>
              <div className="text-xl font-semibold text-yellow-400">{status.modified.length}</div>
            </div>
            <div className="bg-gray-700 rounded-lg p-3">
              <div className="text-sm text-gray-400">追加済み</div>
              <div className="text-xl font-semibold text-green-400">{status.added.length}</div>
            </div>
            <div className="bg-gray-700 rounded-lg p-3">
              <div className="text-sm text-gray-400">削除済み</div>
              <div className="text-xl font-semibold text-red-400">{status.deleted.length}</div>
            </div>
            <div className="bg-gray-700 rounded-lg p-3">
              <div className="text-sm text-gray-400">未追跡</div>
              <div className="text-xl font-semibold text-gray-400">{status.untracked.length}</div>
            </div>
          </div>
        )}

        <div className="mt-4 flex space-x-3">
          <button
            onClick={() => setShowCommitForm(!showCommitForm)}
            className="flex items-center space-x-2 px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors"
          >
            <GitCommit className="h-4 w-4" />
            <span>コミット</span>
          </button>
          <button
            onClick={() => setShowBranchForm(!showBranchForm)}
            className="flex items-center space-x-2 px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 transition-colors"
          >
            <GitMerge className="h-4 w-4" />
            <span>ブランチ作成</span>
          </button>
        </div>

        {/* Commit Form */}
        {showCommitForm && (
          <div className="mt-4 p-4 bg-gray-700 rounded-lg">
            <h4 className="text-sm font-semibold text-white mb-2">新しいコミット</h4>
            <textarea
              value={commitMessage}
              onChange={(e) => setCommitMessage(e.target.value)}
              placeholder="コミットメッセージを入力..."
              className="w-full p-3 bg-gray-600 text-white rounded-md resize-none"
              rows={3}
            />
            <div className="mt-3 flex space-x-2">
              <button
                onClick={createCommit}
                className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors"
              >
                コミット作成
              </button>
              <button
                onClick={() => setShowCommitForm(false)}
                className="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-500 transition-colors"
              >
                キャンセル
              </button>
            </div>
          </div>
        )}

        {/* Branch Form */}
        {showBranchForm && (
          <div className="mt-4 p-4 bg-gray-700 rounded-lg">
            <h4 className="text-sm font-semibold text-white mb-2">新しいブランチ</h4>
            <input
              type="text"
              value={newBranchName}
              onChange={(e) => setNewBranchName(e.target.value)}
              placeholder="ブランチ名を入力..."
              className="w-full p-3 bg-gray-600 text-white rounded-md"
            />
            <div className="mt-3 flex space-x-2">
              <button
                onClick={createBranch}
                className="px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 transition-colors"
              >
                ブランチ作成
              </button>
              <button
                onClick={() => setShowBranchForm(false)}
                className="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-500 transition-colors"
              >
                キャンセル
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Branches */}
      <div className="bg-gray-800 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-blue-400 flex items-center mb-4">
          <GitMerge className="h-5 w-5 mr-2" />
          ブランチ
        </h3>
        <div className="space-y-2">
          {branches.map((branch, index) => (
            <div key={index} className="flex items-center p-2 bg-gray-700 rounded-md">
              <GitBranch className="h-4 w-4 text-green-400 mr-2" />
              <span className="text-white">{branch}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Commit History */}
      <div className="bg-gray-800 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-blue-400 flex items-center mb-4">
          <History className="h-5 w-5 mr-2" />
          コミット履歴
        </h3>
        <div className="space-y-3 max-h-96 overflow-y-auto">
          {commits.map((commit, index) => (
            <div key={index} className="p-3 bg-gray-700 rounded-md">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-2 mb-1">
                    <MessageSquare className="h-4 w-4 text-blue-400" />
                    <span className="text-white font-medium">{commit.message}</span>
                  </div>
                  <div className="flex items-center space-x-4 text-sm text-gray-400">
                    <div className="flex items-center space-x-1">
                      <User className="h-3 w-3" />
                      <span>{commit.author_name}</span>
                    </div>
                    <div className="flex items-center space-x-1">
                      <Clock className="h-3 w-3" />
                      <span>{formatDate(commit.date)}</span>
                    </div>
                  </div>
                </div>
                <div className="text-xs text-gray-500 font-mono">
                  {commit.hash.substring(0, 8)}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
