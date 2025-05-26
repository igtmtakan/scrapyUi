const logger = require('../utils/logger');

class MetricsCollector {
  constructor() {
    this.metrics = {
      requests: {
        total: 0,
        successful: 0,
        failed: 0,
        byEndpoint: {},
        byStatusCode: {},
        responseTimeSum: 0,
        responseTimeCount: 0
      },
      browser: {
        totalCreated: 0,
        totalClosed: 0,
        currentActive: 0,
        peakUsage: 0,
        totalUsageTime: 0,
        errors: 0
      },
      puppeteer: {
        screenshots: { total: 0, successful: 0, failed: 0, totalSize: 0 },
        pdfs: { total: 0, successful: 0, failed: 0, totalSize: 0 },
        scraping: { total: 0, successful: 0, failed: 0, totalPages: 0 },
        totalExecutionTime: 0
      },
      workflows: {
        total: 0,
        successful: 0,
        failed: 0,
        totalSteps: 0,
        totalExecutionTime: 0,
        averageStepsPerWorkflow: 0
      },
      system: {
        startTime: Date.now(),
        lastHealthCheck: null,
        memoryPeakUsage: 0,
        cpuUsageHistory: []
      }
    };

    this.intervals = [];
    this.startPeriodicCollection();
  }

  // Request metrics
  recordRequest(method, endpoint, statusCode, responseTime) {
    this.metrics.requests.total++;

    if (statusCode >= 200 && statusCode < 400) {
      this.metrics.requests.successful++;
    } else {
      this.metrics.requests.failed++;
    }

    // By endpoint
    const endpointKey = `${method} ${endpoint}`;
    if (!this.metrics.requests.byEndpoint[endpointKey]) {
      this.metrics.requests.byEndpoint[endpointKey] = { count: 0, totalTime: 0 };
    }
    this.metrics.requests.byEndpoint[endpointKey].count++;
    this.metrics.requests.byEndpoint[endpointKey].totalTime += responseTime;

    // By status code
    if (!this.metrics.requests.byStatusCode[statusCode]) {
      this.metrics.requests.byStatusCode[statusCode] = 0;
    }
    this.metrics.requests.byStatusCode[statusCode]++;

    // Response time
    this.metrics.requests.responseTimeSum += responseTime;
    this.metrics.requests.responseTimeCount++;

    logger.debug('Request metrics recorded', {
      method,
      endpoint,
      statusCode,
      responseTime,
      totalRequests: this.metrics.requests.total
    });
  }

  // Browser metrics
  recordBrowserCreated() {
    this.metrics.browser.totalCreated++;
    this.metrics.browser.currentActive++;

    if (this.metrics.browser.currentActive > this.metrics.browser.peakUsage) {
      this.metrics.browser.peakUsage = this.metrics.browser.currentActive;
    }

    logger.debug('Browser created', {
      currentActive: this.metrics.browser.currentActive,
      totalCreated: this.metrics.browser.totalCreated
    });
  }

  recordBrowserClosed(usageTime = 0) {
    this.metrics.browser.totalClosed++;
    this.metrics.browser.currentActive = Math.max(0, this.metrics.browser.currentActive - 1);
    this.metrics.browser.totalUsageTime += usageTime;

    logger.debug('Browser closed', {
      currentActive: this.metrics.browser.currentActive,
      usageTime
    });
  }

  recordBrowserError() {
    this.metrics.browser.errors++;
    logger.warn('Browser error recorded', {
      totalErrors: this.metrics.browser.errors
    });
  }

  // Puppeteer operation metrics
  recordScreenshot(success, size = 0, executionTime = 0) {
    this.metrics.puppeteer.screenshots.total++;
    if (success) {
      this.metrics.puppeteer.screenshots.successful++;
      this.metrics.puppeteer.screenshots.totalSize += size;
    } else {
      this.metrics.puppeteer.screenshots.failed++;
    }
    this.metrics.puppeteer.totalExecutionTime += executionTime;

    logger.debug('Screenshot metrics recorded', {
      success,
      size,
      executionTime,
      total: this.metrics.puppeteer.screenshots.total
    });
  }

  recordPDF(success, size = 0, executionTime = 0) {
    this.metrics.puppeteer.pdfs.total++;
    if (success) {
      this.metrics.puppeteer.pdfs.successful++;
      this.metrics.puppeteer.pdfs.totalSize += size;
    } else {
      this.metrics.puppeteer.pdfs.failed++;
    }
    this.metrics.puppeteer.totalExecutionTime += executionTime;

    logger.debug('PDF metrics recorded', {
      success,
      size,
      executionTime,
      total: this.metrics.puppeteer.pdfs.total
    });
  }

  recordScraping(success, pages = 1, executionTime = 0) {
    this.metrics.puppeteer.scraping.total++;
    if (success) {
      this.metrics.puppeteer.scraping.successful++;
      this.metrics.puppeteer.scraping.totalPages += pages;
    } else {
      this.metrics.puppeteer.scraping.failed++;
    }
    this.metrics.puppeteer.totalExecutionTime += executionTime;

    logger.debug('Scraping metrics recorded', {
      success,
      pages,
      executionTime,
      total: this.metrics.puppeteer.scraping.total
    });
  }

  recordWorkflow(success, steps = 0, executionTime = 0) {
    this.metrics.workflows.total++;
    this.metrics.workflows.totalSteps += steps;
    this.metrics.workflows.totalExecutionTime += executionTime;

    if (success) {
      this.metrics.workflows.successful++;
    } else {
      this.metrics.workflows.failed++;
    }

    // Update average steps per workflow
    this.metrics.workflows.averageStepsPerWorkflow =
      this.metrics.workflows.total > 0
        ? Math.round(this.metrics.workflows.totalSteps / this.metrics.workflows.total)
        : 0;

    logger.debug('Workflow metrics recorded', {
      success,
      steps,
      executionTime,
      total: this.metrics.workflows.total
    });
  }

  // System metrics collection
  collectSystemMetrics() {
    const memUsage = process.memoryUsage();

    // Track peak memory usage
    if (memUsage.heapUsed > this.metrics.system.memoryPeakUsage) {
      this.metrics.system.memoryPeakUsage = memUsage.heapUsed;
    }

    // CPU usage (simplified)
    const cpuUsage = process.cpuUsage();
    this.metrics.system.cpuUsageHistory.push({
      timestamp: Date.now(),
      user: cpuUsage.user,
      system: cpuUsage.system
    });

    // Keep only last 100 entries
    if (this.metrics.system.cpuUsageHistory.length > 100) {
      this.metrics.system.cpuUsageHistory = this.metrics.system.cpuUsageHistory.slice(-100);
    }

    this.metrics.system.lastHealthCheck = Date.now();
  }

  // Get computed metrics
  getMetrics() {
    const now = Date.now();
    const uptime = now - this.metrics.system.startTime;

    return {
      ...this.metrics,
      computed: {
        uptime,
        uptimeFormatted: this.formatUptime(uptime),
        averageResponseTime: this.metrics.requests.responseTimeCount > 0
          ? Math.round(this.metrics.requests.responseTimeSum / this.metrics.requests.responseTimeCount)
          : 0,
        successRate: this.metrics.requests.total > 0
          ? Math.round((this.metrics.requests.successful / this.metrics.requests.total) * 100)
          : 100,
        browserUtilization: this.metrics.browser.totalCreated > 0
          ? Math.round((this.metrics.browser.totalUsageTime / (uptime * this.metrics.browser.peakUsage)) * 100)
          : 0,
        puppeteerSuccessRate: {
          screenshots: this.metrics.puppeteer.screenshots.total > 0
            ? Math.round((this.metrics.puppeteer.screenshots.successful / this.metrics.puppeteer.screenshots.total) * 100)
            : 100,
          pdfs: this.metrics.puppeteer.pdfs.total > 0
            ? Math.round((this.metrics.puppeteer.pdfs.successful / this.metrics.puppeteer.pdfs.total) * 100)
            : 100,
          scraping: this.metrics.puppeteer.scraping.total > 0
            ? Math.round((this.metrics.puppeteer.scraping.successful / this.metrics.puppeteer.scraping.total) * 100)
            : 100
        },
        averageExecutionTime: this.getTotalPuppeteerOperations() > 0
          ? Math.round(this.metrics.puppeteer.totalExecutionTime / this.getTotalPuppeteerOperations())
          : 0
      }
    };
  }

  getTotalPuppeteerOperations() {
    return this.metrics.puppeteer.screenshots.total +
           this.metrics.puppeteer.pdfs.total +
           this.metrics.puppeteer.scraping.total;
  }

  formatUptime(ms) {
    const seconds = Math.floor(ms / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);

    if (days > 0) {
      return `${days}d ${hours % 24}h ${minutes % 60}m`;
    } else if (hours > 0) {
      return `${hours}h ${minutes % 60}m ${seconds % 60}s`;
    } else if (minutes > 0) {
      return `${minutes}m ${seconds % 60}s`;
    } else {
      return `${seconds}s`;
    }
  }

  // Periodic collection
  startPeriodicCollection() {
    // Collect system metrics every 30 seconds
    const systemMetricsInterval = setInterval(() => {
      this.collectSystemMetrics();
    }, 30000);

    // Log summary every 5 minutes
    const summaryInterval = setInterval(() => {
      this.logSummary();
    }, 300000);

    this.intervals.push(systemMetricsInterval, summaryInterval);
  }

  logSummary() {
    const metrics = this.getMetrics();

    logger.info('Metrics Summary', {
      uptime: metrics.computed.uptimeFormatted,
      totalRequests: metrics.requests.total,
      successRate: `${metrics.computed.successRate}%`,
      averageResponseTime: `${metrics.computed.averageResponseTime}ms`,
      activeBrowsers: metrics.browser.currentActive,
      peakBrowsers: metrics.browser.peakUsage,
      totalPuppeteerOps: this.getTotalPuppeteerOperations(),
      memoryUsage: `${Math.round(process.memoryUsage().heapUsed / 1024 / 1024)}MB`
    });
  }

  // Reset metrics
  reset() {
    const startTime = this.metrics.system.startTime;
    this.metrics = {
      requests: {
        total: 0,
        successful: 0,
        failed: 0,
        byEndpoint: {},
        byStatusCode: {},
        responseTimeSum: 0,
        responseTimeCount: 0
      },
      browser: {
        totalCreated: 0,
        totalClosed: 0,
        currentActive: 0,
        peakUsage: 0,
        totalUsageTime: 0,
        errors: 0
      },
      puppeteer: {
        screenshots: { total: 0, successful: 0, failed: 0, totalSize: 0 },
        pdfs: { total: 0, successful: 0, failed: 0, totalSize: 0 },
        scraping: { total: 0, successful: 0, failed: 0, totalPages: 0 },
        totalExecutionTime: 0
      },
      system: {
        startTime,
        lastHealthCheck: null,
        memoryPeakUsage: 0,
        cpuUsageHistory: []
      }
    };

    logger.info('Metrics reset');
  }

  // Cleanup
  cleanup() {
    this.intervals.forEach(interval => clearInterval(interval));
    this.intervals = [];
    logger.info('Metrics collector cleanup completed');
  }
}

module.exports = MetricsCollector;
