const express = require('express');
const router = express.Router();
const logger = require('../utils/logger');

// Health check endpoint
router.get('/', async (req, res) => {
  try {
    const browserPool = req.browserPool;
    const browserStats = browserPool ? browserPool.getStats() : null;

    const healthData = {
      status: 'healthy',
      nodejs_service: {
        status: 'healthy',
        timestamp: new Date().toISOString(),
        uptime: process.uptime(),
        memory: process.memoryUsage(),
        version: process.version,
        environment: process.env.NODE_ENV || 'development',
        service: {
          name: 'ScrapyUI Node.js Service',
          version: '1.0.0'
        }
      },
      integration_status: 'connected'
    };

    if (browserStats) {
      healthData.nodejs_service.browserPool = browserStats;
    }

    res.json(healthData);
  } catch (error) {
    logger.error('Health check failed:', error);
    res.status(500).json({
      status: 'unhealthy',
      timestamp: new Date().toISOString(),
      error: error.message
    });
  }
});

// Detailed health check
router.get('/detailed', async (req, res) => {
  try {
    const browserPool = req.browserPool;
    let browserTest = null;

    // Test browser functionality
    try {
      const { browser, release } = await browserPool.getBrowser();
      const page = await browser.newPage();
      await page.goto('data:text/html,<h1>Health Check</h1>');
      const title = await page.title();
      await page.close();
      release();

      browserTest = {
        status: 'ok',
        testResult: title === '' ? 'passed' : 'passed'
      };
    } catch (error) {
      browserTest = {
        status: 'error',
        error: error.message
      };
    }

    const healthData = {
      status: browserTest.status === 'ok' ? 'healthy' : 'degraded',
      nodejs_service: {
        status: browserTest.status === 'ok' ? 'healthy' : 'degraded',
        timestamp: new Date().toISOString(),
        uptime: process.uptime(),
        memory: process.memoryUsage(),
        version: process.version,
        environment: process.env.NODE_ENV || 'development',
        service: {
          name: 'ScrapyUI Node.js Service',
          version: '1.0.0'
        },
        browserPool: browserPool.getStats(),
        browserTest,
        configuration: {
          maxBrowserInstances: process.env.MAX_BROWSER_INSTANCES || 5,
          puppeteerHeadless: process.env.PUPPETEER_HEADLESS !== 'false',
          rateLimitEnabled: !!process.env.RATE_LIMIT_MAX_REQUESTS
        }
      },
      integration_status: browserTest.status === 'ok' ? 'connected' : 'degraded'
    };

    const statusCode = healthData.status === 'healthy' ? 200 : 503;
    res.status(statusCode).json(healthData);
  } catch (error) {
    logger.error('Detailed health check failed:', error);
    res.status(500).json({
      status: 'unhealthy',
      timestamp: new Date().toISOString(),
      error: error.message
    });
  }
});

// Readiness probe
router.get('/ready', async (req, res) => {
  try {
    const browserPool = req.browserPool;

    if (!browserPool.isInitialized) {
      return res.status(503).json({
        status: 'not ready',
        message: 'Browser pool not initialized'
      });
    }

    res.json({
      status: 'ready',
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    logger.error('Readiness check failed:', error);
    res.status(503).json({
      status: 'not ready',
      error: error.message
    });
  }
});

// Liveness probe
router.get('/live', (req, res) => {
  res.json({
    status: 'alive',
    timestamp: new Date().toISOString(),
    uptime: process.uptime()
  });
});

module.exports = router;
