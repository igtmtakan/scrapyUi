// Node.jsサービス用の独自HTTPクライアント（apiClientは使用しない）

export interface NodeJSHealthResponse {
  status: string;
  nodejs_service: {
    status?: string;
    timestamp?: string;
    uptime?: number;
    memory?: {
      rss?: number;
      heapTotal?: number;
      heapUsed?: number;
      external?: number;
      arrayBuffers?: number;
    };
    version?: string;
    environment?: string;
    service?: {
      name?: string;
      version?: string;
    };
    browserPool?: {
      total: number;
      inUse: number;
      available: number;
      maxInstances: number;
    };
  };
  integration_status?: string;
}

export interface SPAScrapingRequest {
  url: string;
  waitFor?: string;
  timeout?: number;
  extractData?: {
    selectors?: Record<string, string>;
    javascript?: string;
  };
  screenshot?: boolean;
  viewport?: {
    width: number;
    height: number;
  };
}

export interface DynamicScrapingRequest {
  url: string;
  actions?: Array<{
    type: 'click' | 'type' | 'wait' | 'scroll' | 'hover';
    selector?: string;
    value?: string;
    delay?: number;
  }>;
  extractAfter?: {
    selectors?: Record<string, string>;
    javascript?: string;
  };
  timeout?: number;
}

export interface PDFGenerationRequest {
  url?: string;
  html?: string;
  options?: {
    format?: 'A4' | 'A3' | 'A2' | 'A1' | 'A0' | 'Legal' | 'Letter' | 'Tabloid';
    landscape?: boolean;
    margin?: {
      top?: string;
      right?: string;
      bottom?: string;
      left?: string;
    };
    printBackground?: boolean;
    scale?: number;
    displayHeaderFooter?: boolean;
    headerTemplate?: string;
    footerTemplate?: string;
  };
}

export interface ScreenshotRequest {
  url: string;
  options?: {
    fullPage?: boolean;
    type?: 'png' | 'jpeg';
    quality?: number;
    clip?: {
      x: number;
      y: number;
      width: number;
      height: number;
    };
    omitBackground?: boolean;
  };
  viewport?: {
    width: number;
    height: number;
    deviceScaleFactor?: number;
  };
}

export interface NodeJSResponse<T = any> {
  success: boolean;
  message: string;
  data?: T;
  nodejs_response?: any;
  user_id?: string;
}

// Workflow interfaces
export interface WorkflowStep {
  name: string;
  type: 'navigate' | 'scrape' | 'screenshot' | 'pdf' | 'interact' | 'wait' | 'script';
  url?: string;
  selectors?: Record<string, string>;
  javascript?: string;
  actions?: Array<{
    type: 'click' | 'type' | 'select' | 'hover';
    selector: string;
    value?: string;
    delay?: number;
  }>;
  timeout?: number;
  outputVariable?: string;
}

export interface WorkflowCreateRequest {
  name: string;
  description?: string;
  steps: WorkflowStep[];
  timeout?: number;
  retryAttempts?: number;
  continueOnError?: boolean;
  parallel?: boolean;
}

export interface WorkflowExecuteRequest {
  variables?: Record<string, any>;
}

class NodeJSService {
  private baseUrl = process.env.NEXT_PUBLIC_NODEJS_SERVICE_URL || 'http://localhost:3001/api';

  async checkHealth(): Promise<NodeJSHealthResponse> {
    const response = await fetch(`${this.baseUrl}/health`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return response.json();
  }

  async testConnection(data?: any): Promise<NodeJSResponse> {
    const response = await fetch(`${this.baseUrl}/test`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        message: 'Test from frontend',
        timestamp: new Date().toISOString(),
        data
      }),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return response.json();
  }

  async scrapeSPA(request: SPAScrapingRequest): Promise<NodeJSResponse> {
    const response = await apiClient.post<NodeJSResponse>(`${this.baseUrl}/scraping/spa`, request);
    return response.data;
  }

  async scrapeDynamicContent(request: DynamicScrapingRequest): Promise<NodeJSResponse> {
    const response = await apiClient.post<NodeJSResponse>(`${this.baseUrl}/scraping/dynamic`, request);
    return response.data;
  }

  async generatePDF(request: PDFGenerationRequest): Promise<NodeJSResponse> {
    const response = await apiClient.post<NodeJSResponse>(`${this.baseUrl}/pdf/generate`, request);
    return response.data;
  }

  async captureScreenshot(request: ScreenshotRequest): Promise<NodeJSResponse> {
    const response = await apiClient.post<NodeJSResponse>(`${this.baseUrl}/screenshot/capture`, request);
    return response.data;
  }

  // Workflow methods
  async getWorkflows(): Promise<NodeJSResponse> {
    const response = await apiClient.get<NodeJSResponse>(`${this.baseUrl}/workflows`);
    return response.data;
  }

  async createWorkflow(request: WorkflowCreateRequest): Promise<NodeJSResponse> {
    const response = await apiClient.post<NodeJSResponse>(`${this.baseUrl}/workflows`, request);
    return response.data;
  }

  async getWorkflow(workflowId: string): Promise<NodeJSResponse> {
    const response = await apiClient.get<NodeJSResponse>(`${this.baseUrl}/workflows/${workflowId}`);
    return response.data;
  }

  async executeWorkflow(workflowId: string, request: WorkflowExecuteRequest): Promise<NodeJSResponse> {
    const response = await apiClient.post<NodeJSResponse>(`${this.baseUrl}/workflows/${workflowId}/execute`, request);
    return response.data;
  }

  async deleteWorkflow(workflowId: string): Promise<NodeJSResponse> {
    const response = await apiClient.delete<NodeJSResponse>(`${this.baseUrl}/workflows/${workflowId}`);
    return response.data;
  }

  async getWorkflowExecutions(workflowId: string): Promise<NodeJSResponse> {
    const response = await apiClient.get<NodeJSResponse>(`${this.baseUrl}/workflows/${workflowId}/executions`);
    return response.data;
  }

  async getWorkflowTemplates(): Promise<NodeJSResponse> {
    const response = await apiClient.get<NodeJSResponse>(`${this.baseUrl}/workflows/templates/list`);
    return response.data;
  }

  // Utility methods
  formatMemoryUsage(bytes: number): string {
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    if (bytes === 0) return '0 Bytes';
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
  }

  formatUptime(seconds: number): string {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);

    if (hours > 0) {
      return `${hours}h ${minutes}m ${secs}s`;
    } else if (minutes > 0) {
      return `${minutes}m ${secs}s`;
    } else {
      return `${secs}s`;
    }
  }

  getBrowserPoolStatus(browserPool: NodeJSHealthResponse['nodejs_service']['browserPool']): {
    status: 'healthy' | 'warning' | 'critical';
    message: string;
    color: string;
  } {
    // browserPoolが未定義の場合のデフォルト処理
    if (!browserPool) {
      return {
        status: 'critical',
        message: 'Browser pool not available',
        color: 'text-red-600'
      };
    }

    const { total, inUse, available, maxInstances } = browserPool;
    const usagePercent = total > 0 ? (inUse / total) * 100 : 0;

    if (total === 0) {
      return {
        status: 'warning',
        message: 'No browser instances initialized',
        color: 'text-yellow-600'
      };
    }

    if (usagePercent > 80) {
      return {
        status: 'critical',
        message: 'High browser usage',
        color: 'text-red-600'
      };
    }

    if (usagePercent > 60) {
      return {
        status: 'warning',
        message: 'Moderate browser usage',
        color: 'text-yellow-600'
      };
    }

    return {
      status: 'healthy',
      message: 'Browser pool healthy',
      color: 'text-green-600'
    };
  }
}

export const nodejsService = new NodeJSService();
