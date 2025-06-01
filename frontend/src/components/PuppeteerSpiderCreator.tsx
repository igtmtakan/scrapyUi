/**
 * Puppeteerスパイダー作成コンポーネント
 * Node.js Puppeteerを使用したスパイダーの作成UI
 */

import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';

interface PuppeteerSpiderCreatorProps {
  projectId: string;
  onSpiderCreated: (spider: any) => void;
  onCancel: () => void;
}

interface ExtractData {
  selectors: Record<string, string>;
  javascript: string;
}

interface Action {
  type: 'click' | 'type' | 'wait' | 'scroll' | 'hover';
  selector?: string;
  value?: string;
  delay?: number;
}

export default function PuppeteerSpiderCreator({ 
  projectId, 
  onSpiderCreated, 
  onCancel 
}: PuppeteerSpiderCreatorProps) {
  const [spiderName, setSpiderName] = useState('');
  const [spiderType, setSpiderType] = useState<'spa' | 'dynamic'>('spa');
  const [startUrls, setStartUrls] = useState(['']);
  const [extractData, setExtractData] = useState<ExtractData>({
    selectors: { title: 'h1', description: 'p' },
    javascript: ''
  });
  const [actions, setActions] = useState<Action[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const addStartUrl = () => {
    setStartUrls([...startUrls, '']);
  };

  const updateStartUrl = (index: number, value: string) => {
    const newUrls = [...startUrls];
    newUrls[index] = value;
    setStartUrls(newUrls);
  };

  const removeStartUrl = (index: number) => {
    setStartUrls(startUrls.filter((_, i) => i !== index));
  };

  const addSelector = () => {
    const key = `field_${Object.keys(extractData.selectors).length + 1}`;
    setExtractData({
      ...extractData,
      selectors: { ...extractData.selectors, [key]: '' }
    });
  };

  const updateSelector = (key: string, value: string) => {
    setExtractData({
      ...extractData,
      selectors: { ...extractData.selectors, [key]: value }
    });
  };

  const removeSelector = (key: string) => {
    const newSelectors = { ...extractData.selectors };
    delete newSelectors[key];
    setExtractData({ ...extractData, selectors: newSelectors });
  };

  const addAction = () => {
    setActions([...actions, { type: 'click', selector: '', value: '' }]);
  };

  const updateAction = (index: number, field: keyof Action, value: any) => {
    const newActions = [...actions];
    newActions[index] = { ...newActions[index], [field]: value };
    setActions(newActions);
  };

  const removeAction = (index: number) => {
    setActions(actions.filter((_, i) => i !== index));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);

    try {
      const requestData = {
        spider_name: spiderName,
        start_urls: startUrls.filter(url => url.trim() !== ''),
        spider_type: spiderType,
        extract_data: extractData,
        actions: spiderType === 'dynamic' ? actions : [],
        custom_settings: {
          DOWNLOAD_DELAY: 2,
          CONCURRENT_REQUESTS: 1
        }
      };

      const response = await fetch(`/api/spiders/puppeteer?project_id=${projectId}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestData),
      });

      if (!response.ok) {
        throw new Error('Failed to create Puppeteer spider');
      }

      const spider = await response.json();
      onSpiderCreated(spider);
    } catch (error) {
      console.error('Error creating Puppeteer spider:', error);
      alert('Puppeteerスパイダーの作成に失敗しました');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto p-6 bg-gray-900 text-white rounded-lg">
      <h2 className="text-2xl font-bold mb-6">🚀 Puppeteerスパイダー作成</h2>
      
      <form onSubmit={handleSubmit} className="space-y-6">
        {/* 基本設定 */}
        <div className="space-y-4">
          <h3 className="text-lg font-semibold">基本設定</h3>
          
          <div>
            <label className="block text-sm font-medium mb-2">スパイダー名</label>
            <Input
              value={spiderName}
              onChange={(e) => setSpiderName(e.target.value)}
              placeholder="例: my_puppeteer_spider"
              required
              className="bg-gray-800 border-gray-700"
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">スパイダータイプ</label>
            <Select value={spiderType} onValueChange={(value: 'spa' | 'dynamic') => setSpiderType(value)}>
              <SelectTrigger className="bg-gray-800 border-gray-700">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="spa">SPA (Single Page Application)</SelectItem>
                <SelectItem value="dynamic">Dynamic (アクション実行)</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>

        {/* 開始URL */}
        <div className="space-y-4">
          <h3 className="text-lg font-semibold">開始URL</h3>
          {startUrls.map((url, index) => (
            <div key={index} className="flex gap-2">
              <Input
                value={url}
                onChange={(e) => updateStartUrl(index, e.target.value)}
                placeholder="https://example.com"
                className="bg-gray-800 border-gray-700"
              />
              {startUrls.length > 1 && (
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => removeStartUrl(index)}
                  className="px-3"
                >
                  削除
                </Button>
              )}
            </div>
          ))}
          <Button type="button" variant="outline" onClick={addStartUrl}>
            URL追加
          </Button>
        </div>

        {/* データ抽出設定 */}
        <div className="space-y-4">
          <h3 className="text-lg font-semibold">データ抽出設定</h3>
          
          <div>
            <label className="block text-sm font-medium mb-2">CSSセレクター</label>
            {Object.entries(extractData.selectors).map(([key, value]) => (
              <div key={key} className="flex gap-2 mb-2">
                <Input
                  value={key}
                  onChange={(e) => {
                    const newKey = e.target.value;
                    const newSelectors = { ...extractData.selectors };
                    delete newSelectors[key];
                    newSelectors[newKey] = value;
                    setExtractData({ ...extractData, selectors: newSelectors });
                  }}
                  placeholder="フィールド名"
                  className="bg-gray-800 border-gray-700 w-1/3"
                />
                <Input
                  value={value}
                  onChange={(e) => updateSelector(key, e.target.value)}
                  placeholder="CSSセレクター (例: h1, .class, #id)"
                  className="bg-gray-800 border-gray-700 flex-1"
                />
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => removeSelector(key)}
                  className="px-3"
                >
                  削除
                </Button>
              </div>
            ))}
            <Button type="button" variant="outline" onClick={addSelector}>
              セレクター追加
            </Button>
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">カスタムJavaScript (オプション)</label>
            <Textarea
              value={extractData.javascript}
              onChange={(e) => setExtractData({ ...extractData, javascript: e.target.value })}
              placeholder="return { customData: document.title };"
              className="bg-gray-800 border-gray-700 h-32"
            />
          </div>
        </div>

        {/* 動的アクション (dynamicタイプの場合) */}
        {spiderType === 'dynamic' && (
          <div className="space-y-4">
            <h3 className="text-lg font-semibold">動的アクション</h3>
            {actions.map((action, index) => (
              <div key={index} className="border border-gray-700 p-4 rounded space-y-2">
                <div className="flex gap-2">
                  <Select 
                    value={action.type} 
                    onValueChange={(value) => updateAction(index, 'type', value)}
                  >
                    <SelectTrigger className="bg-gray-800 border-gray-700 w-32">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="click">クリック</SelectItem>
                      <SelectItem value="type">入力</SelectItem>
                      <SelectItem value="wait">待機</SelectItem>
                      <SelectItem value="scroll">スクロール</SelectItem>
                      <SelectItem value="hover">ホバー</SelectItem>
                    </SelectContent>
                  </Select>
                  
                  {(action.type === 'click' || action.type === 'type' || action.type === 'hover') && (
                    <Input
                      value={action.selector || ''}
                      onChange={(e) => updateAction(index, 'selector', e.target.value)}
                      placeholder="CSSセレクター"
                      className="bg-gray-800 border-gray-700 flex-1"
                    />
                  )}
                  
                  {action.type === 'type' && (
                    <Input
                      value={action.value || ''}
                      onChange={(e) => updateAction(index, 'value', e.target.value)}
                      placeholder="入力値"
                      className="bg-gray-800 border-gray-700 flex-1"
                    />
                  )}
                  
                  {action.type === 'wait' && (
                    <Input
                      type="number"
                      value={action.delay || ''}
                      onChange={(e) => updateAction(index, 'delay', parseInt(e.target.value))}
                      placeholder="待機時間(ms)"
                      className="bg-gray-800 border-gray-700 w-32"
                    />
                  )}
                  
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => removeAction(index)}
                    className="px-3"
                  >
                    削除
                  </Button>
                </div>
              </div>
            ))}
            <Button type="button" variant="outline" onClick={addAction}>
              アクション追加
            </Button>
          </div>
        )}

        {/* ボタン */}
        <div className="flex gap-4 pt-6">
          <Button type="submit" disabled={isLoading} className="bg-blue-600 hover:bg-blue-700">
            {isLoading ? '作成中...' : 'スパイダー作成'}
          </Button>
          <Button type="button" variant="outline" onClick={onCancel}>
            キャンセル
          </Button>
        </div>
      </form>
    </div>
  );
}
