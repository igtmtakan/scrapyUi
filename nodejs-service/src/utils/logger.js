const fs = require('fs');
const path = require('path');

class Logger {
  constructor() {
    this.logLevel = process.env.LOG_LEVEL || 'info';
    this.logFile = process.env.LOG_FILE || 'logs/app.log';
    this.levels = {
      error: 0,
      warn: 1,
      info: 2,
      debug: 3
    };

    // Ensure log directory exists
    this.ensureLogDirectory();
  }

  ensureLogDirectory() {
    const logDir = path.dirname(this.logFile);
    if (!fs.existsSync(logDir)) {
      fs.mkdirSync(logDir, { recursive: true });
    }
  }

  shouldLog(level) {
    return this.levels[level] <= this.levels[this.logLevel];
  }

  formatMessage(level, message, meta = {}) {
    const timestamp = new Date().toISOString();
    const metaStr = Object.keys(meta).length > 0 ? ` ${JSON.stringify(meta)}` : '';
    return `[${timestamp}] [${level.toUpperCase()}] ${message}${metaStr}`;
  }

  writeToFile(formattedMessage) {
    try {
      fs.appendFileSync(this.logFile, formattedMessage + '\n');
    } catch (error) {
      console.error('Failed to write to log file:', error);
    }
  }

  log(level, message, meta = {}) {
    if (!this.shouldLog(level)) return;

    const formattedMessage = this.formatMessage(level, message, meta);

    // Console output with colors
    const colors = {
      error: '\x1b[31m', // Red
      warn: '\x1b[33m',  // Yellow
      info: '\x1b[36m',  // Cyan
      debug: '\x1b[90m'  // Gray
    };

    const reset = '\x1b[0m';
    const coloredMessage = `${colors[level] || ''}${formattedMessage}${reset}`;

    console.log(coloredMessage);

    // File output
    this.writeToFile(formattedMessage);
  }

  error(message, meta = {}) {
    this.log('error', message, meta);
  }

  warn(message, meta = {}) {
    this.log('warn', message, meta);
  }

  info(message, meta = {}) {
    this.log('info', message, meta);
  }

  debug(message, meta = {}) {
    this.log('debug', message, meta);
  }

  // Express middleware for request logging
  middleware() {
    return (req, res, next) => {
      const start = Date.now();
      const requestId = Math.random().toString(36).substr(2, 9);
      req.requestId = requestId;

      // Request start log
      this.info(`[${requestId}] ${req.method} ${req.originalUrl} - START`, {
        ip: req.ip,
        userAgent: req.get('User-Agent'),
        contentLength: req.get('Content-Length'),
        referer: req.get('Referer')
      });

      res.on('finish', () => {
        const duration = Date.now() - start;
        const message = `[${requestId}] ${req.method} ${req.originalUrl} ${res.statusCode} ${duration}ms - END`;

        const logData = {
          ip: req.ip,
          userAgent: req.get('User-Agent'),
          duration,
          requestId,
          responseSize: res.get('Content-Length'),
          statusCode: res.statusCode
        };

        if (res.statusCode >= 500) {
          this.error(message, logData);
        } else if (res.statusCode >= 400) {
          this.warn(message, { ...logData, body: req.body });
        } else {
          this.info(message, logData);
        }
      });

      next();
    };
  }

  // Performance monitoring
  logPerformance(operation, duration, metadata = {}) {
    const level = duration > 5000 ? 'warn' : duration > 1000 ? 'info' : 'debug';
    this.log(level, `Performance: ${operation} took ${duration}ms`, {
      operation,
      duration,
      ...metadata
    });
  }

  // Browser pool monitoring
  logBrowserPool(stats, action = 'status') {
    this.info(`Browser Pool ${action}`, {
      total: stats.total,
      inUse: stats.inUse,
      available: stats.available,
      maxInstances: stats.maxInstances,
      utilizationPercent: stats.total > 0 ? Math.round((stats.inUse / stats.total) * 100) : 0
    });
  }

  // Error tracking with stack traces
  logError(error, context = {}) {
    this.error(error.message, {
      stack: error.stack,
      name: error.name,
      ...context
    });
  }

  // Security events
  logSecurity(event, details = {}) {
    this.warn(`Security Event: ${event}`, {
      event,
      timestamp: new Date().toISOString(),
      ...details
    });
  }
}

module.exports = new Logger();
