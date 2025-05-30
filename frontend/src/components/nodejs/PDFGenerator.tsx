'use client';

import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Switch } from '@/components/ui/switch';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import {
  FileText,
  Play,
  Loader2,
  Download,
  Settings,
  AlertCircle,
  Globe,
  Code
} from 'lucide-react';
import { nodejsService, PDFGenerationRequest, NodeJSResponse } from '@/services/nodejsService';

interface PDFGeneratorProps {
  className?: string;
}

export default function PDFGenerator({ className }: PDFGeneratorProps) {
  const [mode, setMode] = useState<'url' | 'html'>('url');
  const [formData, setFormData] = useState<PDFGenerationRequest>({
    url: '',
    html: '',
    options: {
      format: 'A4',
      landscape: false,
      margin: {
        top: '1cm',
        right: '1cm',
        bottom: '1cm',
        left: '1cm'
      },
      printBackground: true,
      scale: 1,
      displayHeaderFooter: false,
      headerTemplate: '',
      footerTemplate: ''
    }
  });

  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<NodeJSResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

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

  const handleMarginChange = (side: string, value: string) => {
    setFormData(prev => ({
      ...prev,
      options: {
        ...prev.options,
        margin: {
          ...prev.options?.margin,
          [side]: value
        }
      }
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (mode === 'url' && !formData.url) {
      setError('URL is required');
      return;
    }

    if (mode === 'html' && !formData.html) {
      setError('HTML content is required');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      setResult(null);

      const requestData: PDFGenerationRequest = {
        options: formData.options
      };

      if (mode === 'url' && formData.url) {
        requestData.url = formData.url;
      } else if (mode === 'html' && formData.html) {
        requestData.html = formData.html;
      }

      // デバッグ用ログ
      console.log('PDF Generation Request:', JSON.stringify(requestData, null, 2));

      const response = await nodejsService.generatePDF(requestData);
      setResult(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate PDF');
    } finally {
      setLoading(false);
    }
  };

  const downloadPDF = () => {
    // generate-base64エンドポイントのレスポンス構造に対応
    const pdfData = result?.data?.pdf || result?.pdf;
    if (!pdfData) return;

    try {
      const byteCharacters = atob(pdfData);
      const byteNumbers = new Array(byteCharacters.length);
      for (let i = 0; i < byteCharacters.length; i++) {
        byteNumbers[i] = byteCharacters.charCodeAt(i);
      }
      const byteArray = new Uint8Array(byteNumbers);
      const blob = new Blob([byteArray], { type: 'application/pdf' });

      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `generated-${new Date().toISOString().split('T')[0]}.pdf`;
      link.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      setError('Failed to download PDF');
    }
  };

  return (
    <div className={`space-y-6 ${className}`}>
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileText className="w-5 h-5" />
            PDF Generator
          </CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Mode Selection */}
            <div className="space-y-2">
              <Label>Source Type</Label>
              <div className="flex gap-2">
                <Button
                  type="button"
                  variant={mode === 'url' ? 'default' : 'outline'}
                  onClick={() => setMode('url')}
                  className="flex items-center gap-2"
                >
                  <Globe className="w-4 h-4" />
                  URL
                </Button>
                <Button
                  type="button"
                  variant={mode === 'html' ? 'default' : 'outline'}
                  onClick={() => setMode('html')}
                  className="flex items-center gap-2"
                >
                  <Code className="w-4 h-4" />
                  HTML
                </Button>
              </div>
            </div>

            {/* URL Input */}
            {mode === 'url' && (
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
            )}

            {/* HTML Input */}
            {mode === 'html' && (
              <div>
                <Label htmlFor="html">HTML Content *</Label>
                <Textarea
                  id="html"
                  placeholder="<html><body><h1>Hello World</h1></body></html>"
                  value={formData.html}
                  onChange={(e) => handleInputChange('html', e.target.value)}
                  rows={8}
                  required
                />
              </div>
            )}

            {/* PDF Options */}
            <div className="space-y-4">
              <Label className="flex items-center gap-2">
                <Settings className="w-4 h-4" />
                PDF Options
              </Label>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="format">Page Format</Label>
                  <Select
                    value={formData.options?.format}
                    onValueChange={(value) => handleOptionChange('format', value)}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="A4">A4</SelectItem>
                      <SelectItem value="A3">A3</SelectItem>
                      <SelectItem value="A2">A2</SelectItem>
                      <SelectItem value="A1">A1</SelectItem>
                      <SelectItem value="A0">A0</SelectItem>
                      <SelectItem value="Legal">Legal</SelectItem>
                      <SelectItem value="Letter">Letter</SelectItem>
                      <SelectItem value="Tabloid">Tabloid</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div>
                  <Label htmlFor="scale">Scale</Label>
                  <Input
                    id="scale"
                    type="number"
                    min="0.1"
                    max="2"
                    step="0.1"
                    value={formData.options?.scale}
                    onChange={(e) => handleOptionChange('scale', parseFloat(e.target.value))}
                  />
                </div>
              </div>

              {/* Submit Button */}
              <Button type="submit" disabled={loading} className="w-full">
                {loading ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Generating PDF...
                  </>
                ) : (
                  <>
                    <Play className="w-4 h-4 mr-2" />
                    Generate PDF
                  </>
                )}
              </Button>
            </div>
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
                <FileText className="w-5 h-5" />
                PDF Generation Results
              </CardTitle>
              {(result.data?.pdf || result.pdf) && (
                <Button onClick={downloadPDF} variant="outline" size="sm">
                  <Download className="w-4 h-4 mr-2" />
                  Download PDF
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

              {(result.data || result.source || result.size) && (
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="font-medium">Source:</span>
                    <span className="ml-2 text-gray-600">
                      {result.data?.source || result.source || 'HTML content'}
                    </span>
                  </div>
                  <div>
                    <span className="font-medium">Size:</span>
                    <span className="ml-2 text-gray-600">
                      {(result.data?.size || result.size) ?
                        `${((result.data?.size || result.size) / 1024).toFixed(2)} KB` :
                        'Unknown'}
                    </span>
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
