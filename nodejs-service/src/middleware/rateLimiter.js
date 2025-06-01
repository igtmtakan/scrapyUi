const { RateLimiterMemory } = require('rate-limiter-flexible');
const logger = require('../utils/logger');

// Create rate limiter instance
const rateLimiter = new RateLimiterMemory({
  keyGenerator: (req) => req.ip,
  points: parseInt(process.env.RATE_LIMIT_MAX_REQUESTS) || 100, // Number of requests
  duration: parseInt(process.env.RATE_LIMIT_WINDOW_MS) / 1000 || 900, // Per 15 minutes (900 seconds)
  blockDuration: 60, // Block for 60 seconds if limit exceeded
});

// Different limits for different endpoints (テスト用に緩和)
const heavyOperationLimiter = new RateLimiterMemory({
  keyGenerator: (req) => req.ip,
  points: 100, // 100 requests (テスト用に増加)
  duration: 300, // Per 5 minutes (短縮)
  blockDuration: 60, // Block for 1 minute (短縮)
});

const rateLimiterMiddleware = async (req, res, next) => {
  try {
    // Use heavy operation limiter for resource-intensive endpoints
    const isHeavyOperation = req.path.includes('/pdf/') || 
                            req.path.includes('/screenshot/') ||
                            req.path.includes('/scraping/');
    
    const limiter = isHeavyOperation ? heavyOperationLimiter : rateLimiter;
    
    await limiter.consume(req.ip);
    
    // Add rate limit headers
    const resRateLimiter = await limiter.get(req.ip);
    const remainingPoints = resRateLimiter ? limiter.points - resRateLimiter.hitCount : limiter.points;
    const msBeforeNext = resRateLimiter ? Math.round(resRateLimiter.msBeforeNext) || 1 : 0;
    
    res.set({
      'X-RateLimit-Limit': limiter.points,
      'X-RateLimit-Remaining': Math.max(0, remainingPoints),
      'X-RateLimit-Reset': new Date(Date.now() + msBeforeNext).toISOString(),
    });
    
    next();
  } catch (rejRes) {
    // Rate limit exceeded
    const secs = Math.round(rejRes.msBeforeNext / 1000) || 1;
    
    logger.warn(`Rate limit exceeded for IP: ${req.ip}`, {
      path: req.path,
      method: req.method,
      retryAfter: secs
    });
    
    res.set({
      'Retry-After': secs,
      'X-RateLimit-Limit': rejRes.totalHits,
      'X-RateLimit-Remaining': 0,
      'X-RateLimit-Reset': new Date(Date.now() + rejRes.msBeforeNext).toISOString(),
    });
    
    res.status(429).json({
      error: 'Too Many Requests',
      message: `Rate limit exceeded. Try again in ${secs} seconds.`,
      retryAfter: secs,
      code: 'RATE_LIMIT_EXCEEDED'
    });
  }
};

module.exports = rateLimiterMiddleware;
