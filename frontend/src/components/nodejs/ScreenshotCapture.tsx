'use client';

import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { 
  Camera, 
  Play, 
  Loader2, 
  Download, 
  Settings,
  AlertCircle,
  Eye,
  Monitor
} from 'lucide-react';
import { nodejsService, ScreenshotRequest, NodeJSResponse } from '@/services/nodejsService';

interface ScreenshotCaptureProps {
  className?: string;
}

export default function ScreenshotCapture({ className }: ScreenshotCaptureProps) {
  const [formData, setFormData] = useState<ScreenshotRequest>({
    url: '',
    options: {
      fullPage: false,
      type: 'png',
      quality: 80,
      omitBackground: false
    },
    viewport: {
      width: 1920,
      height: 1080,
      deviceScaleFactor: 1
    }
  });

  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<NodeJSResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);

  const handleInputChange = (field: string, value: any) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleOptionChange = (field: string, value: any) => {
    setFormData(prev => ({
      ...prev,
      options: {
        ...prev.options,
        [field]: value
      }
    }));
  };

  const handleViewportChange = (field: string, value: any) => {
    setFormData(prev => ({
      ...prev,
      viewport: {
        ...prev.viewport,
        [field]: value
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
      setPreviewUrl(null);

      const response = await nodejsService.captureScreenshot(formData);
      setResult(response);

      // Create preview URL
      if (response.data?.screenshot) {
        const mimeType = formData.options?.type === 'jpeg' ? 'image/jpeg' : 'image/png';
        const dataUrl = `data:${mimeType};base64,${response.data.screenshot}`;
        setPreviewUrl(dataUrl);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to capture screenshot');
    } finally {
      setLoading(false);
    }
  };

  const downloadScreenshot = () => {
    if (!result?.data?.screenshot) return;
    
    try {
      const byteCharacters = atob(result.data.screenshot);
      const byteNumbers = new Array(byteCharacters.length);
      for (let i = 0; i < byteCharacters.length; i++) {
        byteNumbers[i] = byteCharacters.charCodeAt(i);
      }
      const byteArray = new Uint8Array(byteNumbers);
      const mimeType = formData.options?.type === 'jpeg' ? 'image/jpeg' : 'image/png';
      const blob = new Blob([byteArray], { type: mimeType });
      
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `screenshot-${new Date().toISOString().split('T')[0]}.${formData.options?.type || 'png'}`;
      link.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      setError('Failed to download screenshot');
    }
  };

  return (
    <div className={`space-y-6 ${className}`}>
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Camera className="w-5 h-5" />
            Screenshot Capture
          </CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* URL Input */}
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

            {/* Screenshot Options */}
            <div className="space-y-4">
              <Label className="flex items-center gap-2">
                <Settings className="w-4 h-4" />
                Screenshot Options
              </Label>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="type">Image Format</Label>
                  <Select
                    value={formData.options?.type}
                    onValueChange={(value) => handleOptionChange('type', value)}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="png">PNG</SelectItem>
                      <SelectItem value="jpeg">JPEG</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                {formData.options?.type === 'jpeg' && (
                  <div>
                    <Label htmlFor="quality">JPEG Quality</Label>
                    <Input
                      id="quality"
                      type="number"
                      min="1"
                      max="100"
                      value={formData.options?.quality}
                      onChange={(e) => handleOptionChange('quality', parseInt(e.target.value))}
                    />
                  </div>
                )}
              </div>

              {/* Viewport Settings */}
              <div>
                <Label className="flex items-center gap-2">
                  <Monitor className="w-4 h-4" />
                  Viewport Settings
                </Label>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-2">
                  <div>
                    <Label htmlFor="width" className="text-xs">Width</Label>
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
                    <Label htmlFor="height" className="text-xs">Height</Label>
                    <Input
                      id="height"
                      type="number"
                      min="240"
                      max="2160"
                      value={formData.viewport?.height}
                      onChange={(e) => handleViewportChange('height', parseInt(e.target.value))}
                    />
                  </div>
                  <div>
                    <Label htmlFor="deviceScaleFactor" className="text-xs">Scale Factor</Label>
                    <Input
                      id="deviceScaleFactor"
                      type="number"
                      min="0.1"
                      max="3"
                      step="0.1"
                      value={formData.viewport?.deviceScaleFactor}
                      onChange={(e) => handleViewportChange('deviceScaleFactor', parseFloat(e.target.value))}
                    />
                  </div>
                </div>
              </div>

              {/* Switches */}
              <div className="space-y-3">
                <div className="flex items-center space-x-2">
                  <Switch
                    id="fullPage"
                    checked={formData.options?.fullPage}
                    onCheckedChange={(checked) => handleOptionChange('fullPage', checked)}
                  />
                  <Label htmlFor="fullPage">Full Page Screenshot</Label>
                </div>

                <div className="flex items-center space-x-2">
                  <Switch
                    id="omitBackground"
                    checked={formData.options?.omitBackground}
                    onCheckedChange={(checked) => handleOptionChange('omitBackground', checked)}
                  />
                  <Label htmlFor="omitBackground">Transparent Background</Label>
                </div>
              </div>
            </div>

            {/* Submit Button */}
            <Button type="submit" disabled={loading} className="w-full">
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Capturing Screenshot...
                </>
              ) : (
                <>
                  <Play className="w-4 h-4 mr-2" />
                  Capture Screenshot
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
                Screenshot Results
              </CardTitle>
              {result.data?.screenshot && (
                <Button onClick={downloadScreenshot} variant="outline" size="sm">
                  <Download className="w-4 h-4 mr-2" />
                  Download Image
                </Button>
              )}
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
              
              {result.data && (
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="font-medium">URL:</span>
                    <span className="ml-2 text-gray-600 break-all">{result.data.url}</span>
                  </div>
                  <div>
                    <span className="font-medium">Size:</span>
                    <span className="ml-2 text-gray-600">
                      {result.data.size ? `${(result.data.size / 1024).toFixed(2)} KB` : 'Unknown'}
                    </span>
                  </div>
                </div>
              )}

              {/* Screenshot Preview */}
              {previewUrl && (
                <div className="mt-4">
                  <Label className="text-sm font-medium">Preview:</Label>
                  <div className="mt-2 border rounded-lg overflow-hidden">
                    <img
                      src={previewUrl}
                      alt="Screenshot preview"
                      className="w-full max-h-96 object-contain bg-gray-50"
                    />
                  </div>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
