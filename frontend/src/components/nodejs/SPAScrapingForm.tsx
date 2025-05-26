'use client';

import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Switch } from '@/components/ui/switch';
import { Badge } from '@/components/ui/badge';
import { 
  Globe, 
  Play, 
  Loader2, 
  Download, 
  Eye, 
  Code, 
  Settings,
  Plus,
  Trash2,
  AlertCircle
} from 'lucide-react';
import { nodejsService, SPAScrapingRequest, NodeJSResponse } from '@/services/nodejsService';

interface SPAScrapingFormProps {
  className?: string;
}

interface SelectorPair {
  key: string;
  selector: string;
}

export default function SPAScrapingForm({ className }: SPAScrapingFormProps) {
  const [formData, setFormData] = useState<SPAScrapingRequest>({
    url: '',
    waitFor: '',
    timeout: 30000,
    screenshot: false,
    viewport: {
      width: 1920,
      height: 1080
    },
    extractData: {
      selectors: {},
      javascript: ''
    }
  });

  const [selectors, setSelectors] = useState<SelectorPair[]>([
    { key: 'title', selector: 'h1' }
  ]);

  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<NodeJSResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleInputChange = (field: string, value: any) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleViewportChange = (field: 'width' | 'height', value: number) => {
    setFormData(prev => ({
      ...prev,
      viewport: {
        ...prev.viewport!,
        [field]: value
      }
    }));
  };

  const handleSelectorChange = (index: number, field: 'key' | 'selector', value: string) => {
    const newSelectors = [...selectors];
    newSelectors[index][field] = value;
    setSelectors(newSelectors);
    
    // Update form data
    const selectorsObj = newSelectors.reduce((acc, { key, selector }) => {
      if (key && selector) {
        acc[key] = selector;
      }
      return acc;
    }, {} as Record<string, string>);
    
    setFormData(prev => ({
      ...prev,
      extractData: {
        ...prev.extractData,
        selectors: selectorsObj
      }
    }));
  };

  const addSelector = () => {
    setSelectors(prev => [...prev, { key: '', selector: '' }]);
  };

  const removeSelector = (index: number) => {
    const newSelectors = selectors.filter((_, i) => i !== index);
    setSelectors(newSelectors);
    
    // Update form data
    const selectorsObj = newSelectors.reduce((acc, { key, selector }) => {
      if (key && selector) {
        acc[key] = selector;
      }
      return acc;
    }, {} as Record<string, string>);
    
    setFormData(prev => ({
      ...prev,
      extractData: {
        ...prev.extractData,
        selectors: selectorsObj
      }
    }));
  };

  const handleJavaScriptChange = (value: string) => {
    setFormData(prev => ({
      ...prev,
      extractData: {
        ...prev.extractData,
        javascript: value
      }
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!formData.url) {
      setError('URL is required');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      setResult(null);

      const response = await nodejsService.scrapeSPA(formData);
      setResult(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to scrape SPA');
    } finally {
      setLoading(false);
    }
  };

  const downloadResult = () => {
    if (!result) return;
    
    const dataStr = JSON.stringify(result, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `spa-scraping-${new Date().toISOString().split('T')[0]}.json`;
    link.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className={`space-y-6 ${className}`}>
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Globe className="w-5 h-5" />
            SPA Scraping
          </CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Basic Settings */}
            <div className="space-y-4">
              <div>
                <Label htmlFor="url">Target URL *</Label>
                <Input
                  id="url"
                  type="url"
                  placeholder="https://example.com"
                  value={formData.url}
                  onChange={(e) => handleInputChange('url', e.target.value)}
                  required
                />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="waitFor">Wait For (CSS Selector)</Label>
                  <Input
                    id="waitFor"
                    placeholder=".content, #main, [data-loaded]"
                    value={formData.waitFor}
                    onChange={(e) => handleInputChange('waitFor', e.target.value)}
                  />
                </div>
                <div>
                  <Label htmlFor="timeout">Timeout (ms)</Label>
                  <Input
                    id="timeout"
                    type="number"
                    min="1000"
                    max="60000"
                    value={formData.timeout}
                    onChange={(e) => handleInputChange('timeout', parseInt(e.target.value))}
                  />
                </div>
              </div>
            </div>

            {/* Viewport Settings */}
            <div className="space-y-4">
              <Label className="flex items-center gap-2">
                <Settings className="w-4 h-4" />
                Viewport Settings
              </Label>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="width">Width</Label>
                  <Input
                    id="width"
                    type="number"
                    min="320"
                    max="3840"
                    value={formData.viewport?.width}
                    onChange={(e) => handleViewportChange('width', parseInt(e.target.value))}
                  />
                </div>
                <div>
                  <Label htmlFor="height">Height</Label>
                  <Input
                    id="height"
                    type="number"
                    min="240"
                    max="2160"
                    value={formData.viewport?.height}
                    onChange={(e) => handleViewportChange('height', parseInt(e.target.value))}
                  />
                </div>
              </div>
            </div>

            {/* Data Extraction */}
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <Label className="flex items-center gap-2">
                  <Code className="w-4 h-4" />
                  Data Extraction Selectors
                </Label>
                <Button type="button" onClick={addSelector} variant="outline" size="sm">
                  <Plus className="w-4 h-4 mr-2" />
                  Add Selector
                </Button>
              </div>
              
              <div className="space-y-2">
                {selectors.map((selector, index) => (
                  <div key={index} className="flex gap-2 items-center">
                    <Input
                      placeholder="Key (e.g., title)"
                      value={selector.key}
                      onChange={(e) => handleSelectorChange(index, 'key', e.target.value)}
                      className="flex-1"
                    />
                    <Input
                      placeholder="CSS Selector (e.g., h1)"
                      value={selector.selector}
                      onChange={(e) => handleSelectorChange(index, 'selector', e.target.value)}
                      className="flex-1"
                    />
                    {selectors.length > 1 && (
                      <Button
                        type="button"
                        onClick={() => removeSelector(index)}
                        variant="outline"
                        size="sm"
                      >
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    )}
                  </div>
                ))}
              </div>
            </div>

            {/* Custom JavaScript */}
            <div className="space-y-2">
              <Label htmlFor="javascript">Custom JavaScript (Optional)</Label>
              <Textarea
                id="javascript"
                placeholder="return { customData: document.title };"
                value={formData.extractData?.javascript}
                onChange={(e) => handleJavaScriptChange(e.target.value)}
                rows={4}
              />
            </div>

            {/* Screenshot Option */}
            <div className="flex items-center space-x-2">
              <Switch
                id="screenshot"
                checked={formData.screenshot}
                onCheckedChange={(checked) => handleInputChange('screenshot', checked)}
              />
              <Label htmlFor="screenshot" className="flex items-center gap-2">
                <Eye className="w-4 h-4" />
                Capture Screenshot
              </Label>
            </div>

            {/* Submit Button */}
            <Button type="submit" disabled={loading} className="w-full">
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Scraping...
                </>
              ) : (
                <>
                  <Play className="w-4 h-4 mr-2" />
                  Start Scraping
                </>
              )}
            </Button>
          </form>
        </CardContent>
      </Card>

      {/* Error Display */}
      {error && (
        <Card className="border-red-200">
          <CardContent className="pt-6">
            <div className="flex items-center gap-2 text-red-600">
              <AlertCircle className="w-5 h-5" />
              <span className="font-medium">Error</span>
            </div>
            <p className="text-sm text-red-600 mt-2">{error}</p>
          </CardContent>
        </Card>
      )}

      {/* Results Display */}
      {result && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="flex items-center gap-2">
                <Eye className="w-5 h-5" />
                Scraping Results
              </CardTitle>
              <Button onClick={downloadResult} variant="outline" size="sm">
                <Download className="w-4 h-4 mr-2" />
                Download JSON
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center gap-2">
                <Badge variant={result.success ? "default" : "destructive"}>
                  {result.success ? 'Success' : 'Failed'}
                </Badge>
                <span className="text-sm text-gray-600">{result.message}</span>
              </div>
              
              <div className="bg-gray-50 dark:bg-gray-900 rounded-lg p-4">
                <pre className="text-sm overflow-auto max-h-96">
                  {JSON.stringify(result.data, null, 2)}
                </pre>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
