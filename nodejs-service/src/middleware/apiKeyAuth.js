const logger = require('../utils/logger');

const apiKeyAuth = (req, res, next) => {
  // Skip auth for health check and root endpoints
  if (req.path === '/api/health' || req.path === '/api/docs' || req.path === '/') {
    return next();
  }

  const apiKeyHeader = process.env.API_KEY_HEADER || 'x-api-key';
  const expectedApiKey = process.env.API_KEY;
  
  // If no API key is configured, skip authentication
  if (!expectedApiKey) {
    logger.warn('No API key configured, skipping authentication');
    return next();
  }

  const providedApiKey = req.headers[apiKeyHeader];

  if (!providedApiKey) {
    logger.warn('API key missing', {
      ip: req.ip,
      path: req.path,
      method: req.method
    });
    
    return res.status(401).json({
      error: 'Unauthorized',
      message: `API key required in ${apiKeyHeader} header`,
      code: 'API_KEY_MISSING'
    });
  }

  if (providedApiKey !== expectedApiKey) {
    logger.warn('Invalid API key provided', {
      ip: req.ip,
      path: req.path,
      method: req.method,
      providedKey: providedApiKey.substring(0, 8) + '...' // Log only first 8 chars for security
    });
    
    return res.status(401).json({
      error: 'Unauthorized',
      message: 'Invalid API key',
      code: 'INVALID_API_KEY'
    });
  }

  // API key is valid
  logger.debug('API key authenticated successfully', {
    ip: req.ip,
    path: req.path,
    method: req.method
  });

  next();
};

module.exports = apiKeyAuth;
