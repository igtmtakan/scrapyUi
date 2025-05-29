const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const morgan = require('morgan');
const compression = require('compression');
const dotenv = require('dotenv');
const path = require('path');

// Load environment variables
dotenv.config();

// Import routes
const scrapingRoutes = require('./routes/scraping');
const pdfRoutes = require('./routes/pdf');
const screenshotRoutes = require('./routes/screenshot');
const healthRoutes = require('./routes/health');
const metricsRoutes = require('./routes/metrics');
const workflowRoutes = require('./routes/workflow');
const schedulerRoutes = require('./routes/scheduler');
const commandRoutes = require('./routes/command');

// Import middleware
const errorHandler = require('./middleware/errorHandler');
const rateLimiter = require('./middleware/rateLimiter');
const apiKeyAuth = require('./middleware/apiKeyAuth');
const logger = require('./utils/logger');

// Import services
const BrowserPool = require('./services/BrowserPool');
const MetricsCollector = require('./services/MetricsCollector');
const WorkflowEngine = require('./services/WorkflowEngine');
const Scheduler = require('./services/Scheduler');

const app = express();
const PORT = process.env.PORT || 3001;
const HOST = process.env.HOST || '0.0.0.0';

// Initialize services
const browserPool = new BrowserPool();
const metricsCollector = new MetricsCollector();
const workflowEngine = new WorkflowEngine(browserPool, metricsCollector);
const scheduler = new Scheduler(workflowEngine, metricsCollector);

// Middleware setup
app.use(helmet({
  contentSecurityPolicy: false, // Disable for API service
  crossOriginEmbedderPolicy: false
}));

// CORS設定を最初に配置（プリフライトリクエストを適切に処理）
app.use(cors({
  origin: function (origin, callback) {
    // 開発環境では全てのオリジンを許可
    logger.info(`CORS request from origin: ${origin || 'null'}`);
    callback(null, true);
  },
  credentials: false,
  methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
  allowedHeaders: ['Content-Type', 'Authorization', 'x-api-key'],
  optionsSuccessStatus: 200 // プリフライトリクエストの成功ステータス
}));

// プリフライトリクエストを明示的に処理
app.options('*', cors());

app.use(compression());

app.use(morgan('combined', {
  stream: {
    write: (message) => logger.info(message.trim())
  }
}));

app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true, limit: '10mb' }));

// Rate limiting
app.use(rateLimiter);

// API key authentication for protected routes
app.use('/api', apiKeyAuth);

// Request logging middleware
app.use((req, res, next) => {
  logger.info(`Incoming request: ${req.method} ${req.url} from ${req.ip}`);
  logger.info(`Headers: ${JSON.stringify(req.headers, null, 2)}`);
  next();
});

// Make services available to routes
app.use((req, res, next) => {
  req.browserPool = browserPool;
  req.metricsCollector = metricsCollector;
  req.workflowEngine = workflowEngine;
  req.scheduler = scheduler;
  next();
});

// Metrics collection middleware
app.use((req, res, next) => {
  const start = Date.now();

  res.on('finish', () => {
    const duration = Date.now() - start;
    const endpoint = req.route ? req.route.path : req.path;
    metricsCollector.recordRequest(req.method, endpoint, res.statusCode, duration);
  });

  next();
});

// Routes
app.use('/api/health', healthRoutes);
app.use('/api/metrics', metricsRoutes);
app.use('/api/workflows', workflowRoutes);
app.use('/api/scheduler', schedulerRoutes);
app.use('/api/scraping', scrapingRoutes);
app.use('/api/pdf', pdfRoutes);
app.use('/api/screenshot', screenshotRoutes);
app.use('/api/command', commandRoutes);

// Root endpoint
app.get('/', (req, res) => {
  res.json({
    service: 'ScrapyUI Node.js Service',
    version: '1.0.0',
    status: 'running',
    endpoints: {
      health: '/api/health',
      scraping: '/api/scraping',
      pdf: '/api/pdf',
      screenshot: '/api/screenshot',
      command: '/api/command'
    },
    documentation: '/api/docs'
  });
});

// API documentation endpoint
app.get('/api/docs', (req, res) => {
  res.json({
    title: 'ScrapyUI Node.js Service API',
    version: '1.0.0',
    description: 'Puppeteer-based microservice for web scraping and automation',
    endpoints: {
      'GET /api/health': 'Service health check',
      'POST /api/scraping/spa': 'Scrape Single Page Applications',
      'POST /api/scraping/dynamic': 'Scrape dynamic content',
      'POST /api/pdf/generate': 'Generate PDF from HTML/URL',
      'POST /api/screenshot/capture': 'Capture page screenshots',
      'GET /api/screenshot/full-page': 'Full page screenshot',
      'POST /api/command/exec': 'Execute shell commands',
      'POST /api/command/spawn': 'Spawn processes with streaming output',
      'POST /api/command/sync': 'Execute commands synchronously',
      'GET /api/command/allowed': 'Get list of allowed commands'
    }
  });
});

// Error handling middleware
app.use(errorHandler);

// 404 handler
app.use('*', (req, res) => {
  res.status(404).json({
    error: 'Not Found',
    message: `Route ${req.originalUrl} not found`,
    availableEndpoints: [
      '/api/health',
      '/api/scraping',
      '/api/pdf',
      '/api/screenshot',
      '/api/command'
    ]
  });
});

// Graceful shutdown
process.on('SIGTERM', async () => {
  logger.info('SIGTERM received, shutting down gracefully');
  await browserPool.cleanup();
  process.exit(0);
});

process.on('SIGINT', async () => {
  logger.info('SIGINT received, shutting down gracefully');
  await browserPool.cleanup();
  process.exit(0);
});

// Start server
const server = app.listen(PORT, HOST, () => {
  logger.info(`🚀 ScrapyUI Node.js Service running on http://${HOST}:${PORT}`);
  logger.info(`📚 API Documentation: http://${HOST}:${PORT}/api/docs`);
  logger.info(`🏥 Health Check: http://${HOST}:${PORT}/api/health`);
});

// Handle server errors
server.on('error', (error) => {
  logger.error('Server error:', error);
  process.exit(1);
});

module.exports = app;
