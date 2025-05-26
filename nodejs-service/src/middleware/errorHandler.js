const logger = require('../utils/logger');

const errorHandler = (err, req, res, next) => {
  logger.error('Error occurred:', {
    message: err.message,
    stack: err.stack,
    url: req.originalUrl,
    method: req.method,
    ip: req.ip,
    userAgent: req.get('User-Agent')
  });

  // Default error
  let error = {
    message: 'Internal Server Error',
    status: 500
  };

  // Puppeteer specific errors
  if (err.message.includes('Navigation timeout')) {
    error = {
      message: 'Page navigation timeout',
      status: 408,
      code: 'NAVIGATION_TIMEOUT'
    };
  } else if (err.message.includes('Protocol error')) {
    error = {
      message: 'Browser protocol error',
      status: 500,
      code: 'BROWSER_ERROR'
    };
  } else if (err.message.includes('Target closed')) {
    error = {
      message: 'Browser tab was closed unexpectedly',
      status: 500,
      code: 'TARGET_CLOSED'
    };
  }

  // Validation errors
  if (err.name === 'ValidationError') {
    error = {
      message: 'Validation failed',
      status: 400,
      code: 'VALIDATION_ERROR',
      details: err.details
    };
  }

  // Rate limit errors
  if (err.message.includes('Too Many Requests')) {
    error = {
      message: 'Rate limit exceeded',
      status: 429,
      code: 'RATE_LIMIT_EXCEEDED'
    };
  }

  // Authentication errors
  if (err.message.includes('Unauthorized')) {
    error = {
      message: 'Invalid API key',
      status: 401,
      code: 'UNAUTHORIZED'
    };
  }

  // Development vs Production error details
  const response = {
    error: error.message,
    status: error.status,
    code: error.code || 'INTERNAL_ERROR',
    timestamp: new Date().toISOString(),
    path: req.originalUrl
  };

  if (process.env.NODE_ENV === 'development') {
    response.stack = err.stack;
    response.details = error.details;
  }

  res.status(error.status).json(response);
};

module.exports = errorHandler;
