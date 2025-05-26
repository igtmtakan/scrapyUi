const puppeteer = require('puppeteer');
const logger = require('../utils/logger');

class BrowserPool {
  constructor() {
    this.browsers = [];
    this.maxInstances = parseInt(process.env.MAX_BROWSER_INSTANCES) || 5;
    this.idleTimeout = parseInt(process.env.BROWSER_IDLE_TIMEOUT) || 300000; // 5 minutes
    this.isInitialized = false;
  }

  async initialize() {
    if (this.isInitialized) return;
    
    logger.info('Initializing browser pool...');
    
    try {
      // Create initial browser instance
      const browser = await this.createBrowser();
      this.browsers.push({
        instance: browser,
        inUse: false,
        lastUsed: Date.now(),
        id: this.generateId()
      });
      
      this.isInitialized = true;
      logger.info(`Browser pool initialized with ${this.browsers.length} instances`);
      
      // Start cleanup interval
      this.startCleanupInterval();
    } catch (error) {
      logger.error('Failed to initialize browser pool:', error);
      throw error;
    }
  }

  async createBrowser() {
    const args = [
      '--no-sandbox',
      '--disable-setuid-sandbox',
      '--disable-dev-shm-usage',
      '--disable-accelerated-2d-canvas',
      '--no-first-run',
      '--no-zygote',
      '--disable-gpu',
      '--disable-background-timer-throttling',
      '--disable-backgrounding-occluded-windows',
      '--disable-renderer-backgrounding'
    ];

    if (process.env.NODE_ENV === 'production') {
      args.push('--single-process');
    }

    return await puppeteer.launch({
      headless: process.env.PUPPETEER_HEADLESS !== 'false',
      args,
      defaultViewport: {
        width: parseInt(process.env.PUPPETEER_VIEWPORT_WIDTH) || 1920,
        height: parseInt(process.env.PUPPETEER_VIEWPORT_HEIGHT) || 1080
      },
      timeout: parseInt(process.env.PUPPETEER_TIMEOUT) || 30000
    });
  }

  async getBrowser() {
    if (!this.isInitialized) {
      await this.initialize();
    }

    // Find available browser
    let browserInfo = this.browsers.find(b => !b.inUse);

    // If no available browser and under limit, create new one
    if (!browserInfo && this.browsers.length < this.maxInstances) {
      try {
        const browser = await this.createBrowser();
        browserInfo = {
          instance: browser,
          inUse: false,
          lastUsed: Date.now(),
          id: this.generateId()
        };
        this.browsers.push(browserInfo);
        logger.info(`Created new browser instance. Total: ${this.browsers.length}`);
      } catch (error) {
        logger.error('Failed to create new browser:', error);
        throw error;
      }
    }

    // If still no available browser, wait for one
    if (!browserInfo) {
      logger.warn('All browsers in use, waiting for available instance...');
      browserInfo = await this.waitForAvailableBrowser();
    }

    // Mark as in use
    browserInfo.inUse = true;
    browserInfo.lastUsed = Date.now();

    return {
      browser: browserInfo.instance,
      release: () => this.releaseBrowser(browserInfo.id)
    };
  }

  async waitForAvailableBrowser(timeout = 30000) {
    const startTime = Date.now();
    
    while (Date.now() - startTime < timeout) {
      const available = this.browsers.find(b => !b.inUse);
      if (available) {
        return available;
      }
      await new Promise(resolve => setTimeout(resolve, 100));
    }
    
    throw new Error('Timeout waiting for available browser');
  }

  releaseBrowser(browserId) {
    const browserInfo = this.browsers.find(b => b.id === browserId);
    if (browserInfo) {
      browserInfo.inUse = false;
      browserInfo.lastUsed = Date.now();
      logger.debug(`Released browser ${browserId}`);
    }
  }

  startCleanupInterval() {
    setInterval(async () => {
      await this.cleanupIdleBrowsers();
    }, 60000); // Check every minute
  }

  async cleanupIdleBrowsers() {
    const now = Date.now();
    const browsersToRemove = [];

    for (let i = this.browsers.length - 1; i >= 0; i--) {
      const browserInfo = this.browsers[i];
      
      // Keep at least one browser
      if (this.browsers.length <= 1) break;
      
      // Remove idle browsers
      if (!browserInfo.inUse && (now - browserInfo.lastUsed) > this.idleTimeout) {
        browsersToRemove.push(i);
      }
    }

    for (const index of browsersToRemove) {
      const browserInfo = this.browsers[index];
      try {
        await browserInfo.instance.close();
        this.browsers.splice(index, 1);
        logger.info(`Cleaned up idle browser ${browserInfo.id}. Remaining: ${this.browsers.length}`);
      } catch (error) {
        logger.error(`Error closing browser ${browserInfo.id}:`, error);
      }
    }
  }

  async cleanup() {
    logger.info('Cleaning up browser pool...');
    
    for (const browserInfo of this.browsers) {
      try {
        await browserInfo.instance.close();
      } catch (error) {
        logger.error(`Error closing browser ${browserInfo.id}:`, error);
      }
    }
    
    this.browsers = [];
    this.isInitialized = false;
    logger.info('Browser pool cleanup completed');
  }

  generateId() {
    return Math.random().toString(36).substr(2, 9);
  }

  getStats() {
    return {
      total: this.browsers.length,
      inUse: this.browsers.filter(b => b.inUse).length,
      available: this.browsers.filter(b => !b.inUse).length,
      maxInstances: this.maxInstances
    };
  }
}

module.exports = BrowserPool;
