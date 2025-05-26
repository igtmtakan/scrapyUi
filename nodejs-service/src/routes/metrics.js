const express = require('express');
const router = express.Router();
const logger = require('../utils/logger');

// Get all metrics
router.get('/', (req, res) => {
  try {
    const metricsCollector = req.metricsCollector;
    const metrics = metricsCollector.getMetrics();
    
    res.json({
      success: true,
      timestamp: new Date().toISOString(),
      metrics
    });
  } catch (error) {
    logger.error('Failed to get metrics:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to retrieve metrics',
      message: error.message
    });
  }
});

// Get summary metrics
router.get('/summary', (req, res) => {
  try {
    const metricsCollector = req.metricsCollector;
    const metrics = metricsCollector.getMetrics();
    
    const summary = {
      service: {
        uptime: metrics.computed.uptimeFormatted,
        status: 'running',
        version: '1.0.0'
      },
      performance: {
        totalRequests: metrics.requests.total,
        successRate: `${metrics.computed.successRate}%`,
        averageResponseTime: `${metrics.computed.averageResponseTime}ms`,
        requestsPerMinute: Math.round(metrics.requests.total / (metrics.computed.uptime / 60000))
      },
      browser: {
        currentActive: metrics.browser.currentActive,
        peakUsage: metrics.browser.peakUsage,
        totalCreated: metrics.browser.totalCreated,
        errors: metrics.browser.errors
      },
      puppeteer: {
        totalOperations: metricsCollector.getTotalPuppeteerOperations(),
        successRates: metrics.computed.puppeteerSuccessRate,
        averageExecutionTime: `${metrics.computed.averageExecutionTime}ms`
      },
      system: {
        memoryUsage: process.memoryUsage(),
        cpuUsage: process.cpuUsage(),
        nodeVersion: process.version
      }
    };
    
    res.json({
      success: true,
      timestamp: new Date().toISOString(),
      summary
    });
  } catch (error) {
    logger.error('Failed to get metrics summary:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to retrieve metrics summary',
      message: error.message
    });
  }
});

// Get request metrics
router.get('/requests', (req, res) => {
  try {
    const metricsCollector = req.metricsCollector;
    const metrics = metricsCollector.getMetrics();
    
    res.json({
      success: true,
      timestamp: new Date().toISOString(),
      requests: {
        ...metrics.requests,
        averageResponseTime: metrics.computed.averageResponseTime,
        successRate: metrics.computed.successRate
      }
    });
  } catch (error) {
    logger.error('Failed to get request metrics:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to retrieve request metrics',
      message: error.message
    });
  }
});

// Get browser metrics
router.get('/browser', (req, res) => {
  try {
    const metricsCollector = req.metricsCollector;
    const browserPool = req.browserPool;
    const metrics = metricsCollector.getMetrics();
    
    res.json({
      success: true,
      timestamp: new Date().toISOString(),
      browser: {
        ...metrics.browser,
        currentStats: browserPool.getStats(),
        utilization: metrics.computed.browserUtilization
      }
    });
  } catch (error) {
    logger.error('Failed to get browser metrics:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to retrieve browser metrics',
      message: error.message
    });
  }
});

// Get Puppeteer operation metrics
router.get('/puppeteer', (req, res) => {
  try {
    const metricsCollector = req.metricsCollector;
    const metrics = metricsCollector.getMetrics();
    
    res.json({
      success: true,
      timestamp: new Date().toISOString(),
      puppeteer: {
        ...metrics.puppeteer,
        successRates: metrics.computed.puppeteerSuccessRate,
        averageExecutionTime: metrics.computed.averageExecutionTime,
        totalOperations: metricsCollector.getTotalPuppeteerOperations()
      }
    });
  } catch (error) {
    logger.error('Failed to get Puppeteer metrics:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to retrieve Puppeteer metrics',
      message: error.message
    });
  }
});

// Get system metrics
router.get('/system', (req, res) => {
  try {
    const metricsCollector = req.metricsCollector;
    const metrics = metricsCollector.getMetrics();
    
    const systemInfo = {
      ...metrics.system,
      current: {
        memory: process.memoryUsage(),
        cpu: process.cpuUsage(),
        uptime: process.uptime(),
        version: process.version,
        platform: process.platform,
        arch: process.arch
      },
      computed: {
        uptimeFormatted: metrics.computed.uptimeFormatted,
        memoryPeakUsageFormatted: `${Math.round(metrics.system.memoryPeakUsage / 1024 / 1024)}MB`
      }
    };
    
    res.json({
      success: true,
      timestamp: new Date().toISOString(),
      system: systemInfo
    });
  } catch (error) {
    logger.error('Failed to get system metrics:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to retrieve system metrics',
      message: error.message
    });
  }
});

// Reset metrics
router.post('/reset', (req, res) => {
  try {
    const metricsCollector = req.metricsCollector;
    metricsCollector.reset();
    
    logger.info('Metrics reset requested', {
      ip: req.ip,
      userAgent: req.get('User-Agent')
    });
    
    res.json({
      success: true,
      message: 'Metrics reset successfully',
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    logger.error('Failed to reset metrics:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to reset metrics',
      message: error.message
    });
  }
});

// Export metrics in Prometheus format
router.get('/prometheus', (req, res) => {
  try {
    const metricsCollector = req.metricsCollector;
    const metrics = metricsCollector.getMetrics();
    
    const prometheusMetrics = [
      `# HELP nodejs_service_requests_total Total number of requests`,
      `# TYPE nodejs_service_requests_total counter`,
      `nodejs_service_requests_total ${metrics.requests.total}`,
      ``,
      `# HELP nodejs_service_requests_successful_total Total number of successful requests`,
      `# TYPE nodejs_service_requests_successful_total counter`,
      `nodejs_service_requests_successful_total ${metrics.requests.successful}`,
      ``,
      `# HELP nodejs_service_requests_failed_total Total number of failed requests`,
      `# TYPE nodejs_service_requests_failed_total counter`,
      `nodejs_service_requests_failed_total ${metrics.requests.failed}`,
      ``,
      `# HELP nodejs_service_response_time_average Average response time in milliseconds`,
      `# TYPE nodejs_service_response_time_average gauge`,
      `nodejs_service_response_time_average ${metrics.computed.averageResponseTime}`,
      ``,
      `# HELP nodejs_service_browser_active Current number of active browsers`,
      `# TYPE nodejs_service_browser_active gauge`,
      `nodejs_service_browser_active ${metrics.browser.currentActive}`,
      ``,
      `# HELP nodejs_service_browser_peak Peak number of browsers used`,
      `# TYPE nodejs_service_browser_peak gauge`,
      `nodejs_service_browser_peak ${metrics.browser.peakUsage}`,
      ``,
      `# HELP nodejs_service_puppeteer_operations_total Total Puppeteer operations`,
      `# TYPE nodejs_service_puppeteer_operations_total counter`,
      `nodejs_service_puppeteer_operations_total ${metricsCollector.getTotalPuppeteerOperations()}`,
      ``,
      `# HELP nodejs_service_uptime_seconds Service uptime in seconds`,
      `# TYPE nodejs_service_uptime_seconds gauge`,
      `nodejs_service_uptime_seconds ${Math.floor(metrics.computed.uptime / 1000)}`,
      ``
    ].join('\n');
    
    res.set('Content-Type', 'text/plain');
    res.send(prometheusMetrics);
  } catch (error) {
    logger.error('Failed to export Prometheus metrics:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to export Prometheus metrics',
      message: error.message
    });
  }
});

module.exports = router;
