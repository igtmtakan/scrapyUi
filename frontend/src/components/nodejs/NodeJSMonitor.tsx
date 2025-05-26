'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { 
  Activity, 
  Server, 
  Globe, 
  RefreshCw, 
  AlertCircle, 
  CheckCircle, 
  Clock,
  MemoryStick,
  Cpu,
  Monitor
} from 'lucide-react';
import { nodejsService, NodeJSHealthResponse } from '@/services/nodejsService';

interface NodeJSMonitorProps {
  className?: string;
}

export default function NodeJSMonitor({ className }: NodeJSMonitorProps) {
  const [health, setHealth] = useState<NodeJSHealthResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);

  const fetchHealth = async () => {
    try {
      setLoading(true);
      setError(null);
      const healthData = await nodejsService.checkHealth();
      setHealth(healthData);
      setLastUpdate(new Date());
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch health data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHealth();
    
    // Auto-refresh every 30 seconds
    const interval = setInterval(fetchHealth, 30000);
    return () => clearInterval(interval);
  }, []);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy':
        return 'text-green-600 bg-green-100';
      case 'connected':
        return 'text-green-600 bg-green-100';
      default:
        return 'text-red-600 bg-red-100';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy':
      case 'connected':
        return <CheckCircle className="w-4 h-4" />;
      default:
        return <AlertCircle className="w-4 h-4" />;
    }
  };

  if (loading && !health) {
    return (
      <Card className={className}>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Server className="w-5 h-5" />
            Node.js Service Monitor
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center py-8">
            <RefreshCw className="w-6 h-6 animate-spin" />
            <span className="ml-2">Loading service status...</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className={className}>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Server className="w-5 h-5" />
            Node.js Service Monitor
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-red-600">
              <AlertCircle className="w-5 h-5" />
              <span>Service Unavailable</span>
            </div>
            <Button onClick={fetchHealth} variant="outline" size="sm">
              <RefreshCw className="w-4 h-4 mr-2" />
              Retry
            </Button>
          </div>
          <p className="text-sm text-gray-600 mt-2">{error}</p>
        </CardContent>
      </Card>
    );
  }

  if (!health) return null;

  const { nodejs_service, integration_status } = health;
  const browserPoolStatus = nodejsService.getBrowserPoolStatus(nodejs_service.browserPool);

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Service Status Overview */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <Server className="w-5 h-5" />
              Node.js Service Monitor
            </CardTitle>
            <Button onClick={fetchHealth} variant="outline" size="sm" disabled={loading}>
              <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
              Refresh
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Service Status */}
            <div className="flex items-center justify-between p-4 border rounded-lg">
              <div>
                <p className="text-sm font-medium text-gray-600">Service Status</p>
                <div className="flex items-center gap-2 mt-1">
                  {getStatusIcon(nodejs_service.status)}
                  <Badge className={getStatusColor(nodejs_service.status)}>
                    {nodejs_service.status}
                  </Badge>
                </div>
              </div>
              <Activity className="w-8 h-8 text-gray-400" />
            </div>

            {/* Integration Status */}
            <div className="flex items-center justify-between p-4 border rounded-lg">
              <div>
                <p className="text-sm font-medium text-gray-600">Integration</p>
                <div className="flex items-center gap-2 mt-1">
                  {getStatusIcon(integration_status)}
                  <Badge className={getStatusColor(integration_status)}>
                    {integration_status}
                  </Badge>
                </div>
              </div>
              <Globe className="w-8 h-8 text-gray-400" />
            </div>

            {/* Browser Pool */}
            <div className="flex items-center justify-between p-4 border rounded-lg">
              <div>
                <p className="text-sm font-medium text-gray-600">Browser Pool</p>
                <div className="flex items-center gap-2 mt-1">
                  <Badge className={browserPoolStatus.color}>
                    {nodejs_service.browserPool.available}/{nodejs_service.browserPool.maxInstances}
                  </Badge>
                  <span className="text-xs text-gray-500">available</span>
                </div>
              </div>
              <Monitor className="w-8 h-8 text-gray-400" />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Detailed Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* System Information */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Cpu className="w-5 h-5" />
              System Information
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex justify-between items-center">
              <span className="text-sm font-medium">Service Version</span>
              <Badge variant="outline">{nodejs_service.service.version}</Badge>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm font-medium">Node.js Version</span>
              <Badge variant="outline">{nodejs_service.version}</Badge>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm font-medium">Environment</span>
              <Badge variant="outline">{nodejs_service.environment}</Badge>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm font-medium">Uptime</span>
              <div className="flex items-center gap-2">
                <Clock className="w-4 h-4 text-gray-400" />
                <span className="text-sm">{nodejsService.formatUptime(nodejs_service.uptime)}</span>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Memory Usage */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <MemoryStick className="w-5 h-5" />
              Memory Usage
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex justify-between items-center">
              <span className="text-sm font-medium">RSS</span>
              <span className="text-sm">{nodejsService.formatMemoryUsage(nodejs_service.memory.rss)}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm font-medium">Heap Total</span>
              <span className="text-sm">{nodejsService.formatMemoryUsage(nodejs_service.memory.heapTotal)}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm font-medium">Heap Used</span>
              <span className="text-sm">{nodejsService.formatMemoryUsage(nodejs_service.memory.heapUsed)}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm font-medium">External</span>
              <span className="text-sm">{nodejsService.formatMemoryUsage(nodejs_service.memory.external)}</span>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Last Update */}
      {lastUpdate && (
        <div className="text-center text-sm text-gray-500">
          Last updated: {lastUpdate.toLocaleTimeString()}
        </div>
      )}
    </div>
  );
}
