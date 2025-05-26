const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const morgan = require('morgan');
const compression = require('compression');
const dotenv = require('dotenv');

// Load environment variables
dotenv.config();

const app = express();
const PORT = process.env.PORT || 3001;
const HOST = process.env.HOST || '0.0.0.0';

// Middleware setup
app.use(helmet({
  contentSecurityPolicy: false,
  crossOriginEmbedderPolicy: false
}));

app.use(compression());

app.use(cors({
  origin: process.env.CORS_ORIGIN?.split(',') || ['http://localhost:3000', 'http://localhost:8000'],
  credentials: process.env.CORS_CREDENTIALS === 'true',
  methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
  allowedHeaders: ['Content-Type', 'Authorization', 'x-api-key']
}));

app.use(morgan('combined'));
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true, limit: '10mb' }));

// Root endpoint
app.get('/', (req, res) => {
  res.json({
    service: 'ScrapyUI Node.js Service',
    version: '1.0.0',
    status: 'running',
    mode: 'simple',
    message: 'Puppeteer integration will be added after basic setup is confirmed',
    endpoints: {
      health: '/api/health',
      docs: '/api/docs'
    }
  });
});

// Health check endpoint
app.get('/api/health', (req, res) => {
  res.json({
    status: 'healthy',
    timestamp: new Date().toISOString(),
    uptime: process.uptime(),
    memory: process.memoryUsage(),
    version: process.version,
    environment: process.env.NODE_ENV || 'development',
    service: {
      name: 'ScrapyUI Node.js Service',
      version: '1.0.0',
      mode: 'simple'
    }
  });
});

// API documentation endpoint
app.get('/api/docs', (req, res) => {
  res.json({
    title: 'ScrapyUI Node.js Service API',
    version: '1.0.0',
    description: 'Node.js microservice for ScrapyUI (Simple mode - Puppeteer integration pending)',
    status: 'Basic server running, Puppeteer features will be added next',
    plannedEndpoints: {
      'POST /api/scraping/spa': 'Scrape Single Page Applications (Coming soon)',
      'POST /api/scraping/dynamic': 'Scrape dynamic content (Coming soon)',
      'POST /api/pdf/generate': 'Generate PDF from HTML/URL (Coming soon)',
      'POST /api/screenshot/capture': 'Capture page screenshots (Coming soon)'
    },
    currentEndpoints: {
      'GET /': 'Service information',
      'GET /api/health': 'Health check',
      'GET /api/docs': 'This documentation'
    }
  });
});

// Test endpoint for integration
app.post('/api/test', (req, res) => {
  res.json({
    success: true,
    message: 'Node.js service is responding correctly',
    timestamp: new Date().toISOString(),
    receivedData: req.body,
    headers: req.headers
  });
});

// 404 handler
app.use('*', (req, res) => {
  res.status(404).json({
    error: 'Not Found',
    message: `Route ${req.originalUrl} not found`,
    availableEndpoints: [
      '/',
      '/api/health',
      '/api/docs',
      '/api/test'
    ]
  });
});

// Error handling middleware
app.use((err, req, res, next) => {
  console.error('Error occurred:', err);
  
  res.status(500).json({
    error: 'Internal Server Error',
    message: err.message,
    timestamp: new Date().toISOString()
  });
});

// Start server
const server = app.listen(PORT, HOST, () => {
  console.log(`🚀 ScrapyUI Node.js Service (Simple Mode) running on http://${HOST}:${PORT}`);
  console.log(`📚 API Documentation: http://${HOST}:${PORT}/api/docs`);
  console.log(`🏥 Health Check: http://${HOST}:${PORT}/api/health`);
  console.log(`⚡ Test Endpoint: http://${HOST}:${PORT}/api/test`);
  console.log(`📝 Next step: Install Puppeteer and enable full functionality`);
});

// Handle server errors
server.on('error', (error) => {
  console.error('Server error:', error);
  process.exit(1);
});

module.exports = app;
