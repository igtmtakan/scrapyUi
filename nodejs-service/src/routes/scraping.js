const express = require('express');
const Joi = require('joi');
const router = express.Router();
const logger = require('../utils/logger');

// Validation schemas
const spaScrapingSchema = Joi.object({
  url: Joi.string().uri().required(),
  waitFor: Joi.alternatives().try(
    Joi.string(), // CSS selector
    Joi.number().min(0).max(30000) // milliseconds
  ).optional(),
  viewport: Joi.object({
    width: Joi.number().min(320).max(3840).default(1920),
    height: Joi.number().min(240).max(2160).default(1080)
  }).optional(),
  userAgent: Joi.string().optional(),
  timeout: Joi.number().min(1000).max(60000).default(30000),
  extractData: Joi.object({
    selectors: Joi.object().pattern(Joi.string(), Joi.string()).optional(),
    javascript: Joi.string().optional()
  }).optional(),
  screenshot: Joi.boolean().default(false),
  fullPage: Joi.boolean().default(false)
});

const dynamicContentSchema = Joi.object({
  url: Joi.string().uri().required(),
  actions: Joi.array().items(
    Joi.object({
      type: Joi.string().valid('click', 'type', 'wait', 'scroll', 'hover').required(),
      selector: Joi.string().when('type', {
        is: Joi.string().valid('click', 'type', 'hover'),
        then: Joi.required(),
        otherwise: Joi.optional()
      }),
      value: Joi.string().when('type', {
        is: 'type',
        then: Joi.required(),
        otherwise: Joi.optional()
      }),
      delay: Joi.number().min(0).max(10000).when('type', {
        is: 'wait',
        then: Joi.required(),
        otherwise: Joi.optional()
      })
    })
  ).optional(),
  extractAfter: Joi.object({
    selectors: Joi.object().pattern(Joi.string(), Joi.string()).optional(),
    javascript: Joi.string().optional()
  }).optional(),
  timeout: Joi.number().min(1000).max(60000).default(30000)
});

// SPA Scraping endpoint
router.post('/spa', async (req, res, next) => {
  try {
    logger.info('SPA scraping request body:', JSON.stringify(req.body, null, 2));

    const { error, value } = spaScrapingSchema.validate(req.body);
    if (error) {
      logger.error('SPA scraping validation error:', error.details.map(d => d.message));
      return res.status(400).json({
        error: 'Validation Error',
        details: error.details.map(d => d.message)
      });
    }

    const { url, waitFor, viewport, userAgent, timeout, extractData, screenshot, fullPage } = value;
    const browserPool = req.browserPool;

    logger.info(`Starting SPA scraping for: ${url}`);

    const { browser, release } = await browserPool.getBrowser();
    let page;

    try {
      page = await browser.newPage();

      // Set viewport
      if (viewport) {
        await page.setViewport(viewport);
      }

      // Set user agent
      if (userAgent) {
        await page.setUserAgent(userAgent);
      } else if (process.env.PUPPETEER_USER_AGENT) {
        await page.setUserAgent(process.env.PUPPETEER_USER_AGENT);
      }

      // Navigate to URL
      await page.goto(url, {
        waitUntil: 'networkidle2',
        timeout
      });

      // Wait for specific condition
      if (waitFor) {
        if (typeof waitFor === 'string') {
          await page.waitForSelector(waitFor, { timeout: 10000 });
        } else {
          await page.waitForTimeout(waitFor);
        }
      } else {
        // Default wait for page to be fully loaded and rendered
        await page.waitForTimeout(3000);
      }

      const scrapingData = {
        url,
        timestamp: new Date().toISOString(),
        pageInfo: {
          title: await page.title(),
          url: page.url(),
          viewport: page.viewport()
        }
      };

      // Extract data
      if (extractData) {
        logger.info(`Data extraction requested:`, JSON.stringify(extractData, null, 2));

        if (extractData.selectors) {
          logger.info(`Processing ${Object.keys(extractData.selectors).length} selectors`);
          const extractedData = {};
          for (const [key, selector] of Object.entries(extractData.selectors)) {
            try {
              logger.info(`Extracting data for key "${key}" with selector "${selector}"`);
              const elements = await page.$$(selector);
              logger.info(`Found ${elements.length} elements for selector "${selector}"`);

              if (elements.length === 1) {
                extractedData[key] = await page.$eval(selector, el => el.textContent?.trim());
              } else if (elements.length > 1) {
                extractedData[key] = await page.$$eval(selector, els =>
                  els.map(el => el.textContent?.trim())
                );
              } else {
                extractedData[key] = null;
              }
              logger.info(`Extracted data for "${key}":`, extractedData[key]);
            } catch (err) {
              logger.warn(`Failed to extract data for selector ${selector}:`, err.message);
              extractedData[key] = null;
            }
          }
          scrapingData.extractedData = extractedData;
          logger.info(`Final extracted data:`, extractedData);
        }

        if (extractData.javascript) {
          logger.info(`Executing custom JavaScript:`, extractData.javascript);
          try {
            // Wrap the JavaScript code in a function if it contains return statement
            let jsCode = extractData.javascript.trim();
            if (jsCode.includes('return ') && !jsCode.startsWith('(') && !jsCode.startsWith('function')) {
              jsCode = `(() => { ${jsCode} })()`;
            }
            scrapingData.customData = await page.evaluate(jsCode);
            logger.info(`Custom JavaScript result:`, scrapingData.customData);
          } catch (err) {
            logger.warn('Failed to execute custom JavaScript:', err.message);
            scrapingData.customData = null;
          }
        }
      } else {
        logger.info('No data extraction requested');
      }

      // Take screenshot if requested
      if (screenshot) {
        const screenshotBuffer = await page.screenshot({
          fullPage,
          type: 'png'
        });
        scrapingData.screenshot = screenshotBuffer.toString('base64');
      }

      await page.close();
      release();

      const result = {
        success: true,
        message: 'SPA scraping completed successfully',
        timestamp: new Date().toISOString(),
        data: scrapingData
      };

      logger.info(`SPA scraping completed successfully for: ${url}`);
      res.json(result);

    } catch (error) {
      if (page) await page.close();
      release();
      throw error;
    }

  } catch (error) {
    logger.error('SPA scraping failed:', error);
    next(error);
  }
});

// Dynamic content scraping with actions
router.post('/dynamic', async (req, res, next) => {
  try {
    const { error, value } = dynamicContentSchema.validate(req.body);
    if (error) {
      return res.status(400).json({
        error: 'Validation Error',
        details: error.details.map(d => d.message)
      });
    }

    const { url, actions, extractAfter, timeout } = value;
    const browserPool = req.browserPool;

    logger.info(`Starting dynamic content scraping for: ${url}`);

    const { browser, release } = await browserPool.getBrowser();
    let page;

    try {
      page = await browser.newPage();

      await page.goto(url, {
        waitUntil: 'networkidle2',
        timeout
      });

      // Execute actions
      if (actions && actions.length > 0) {
        for (const action of actions) {
          switch (action.type) {
            case 'click':
              await page.click(action.selector);
              break;
            case 'type':
              await page.type(action.selector, action.value);
              break;
            case 'wait':
              await page.waitForTimeout(action.delay);
              break;
            case 'scroll':
              await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
              break;
            case 'hover':
              await page.hover(action.selector);
              break;
          }

          // Small delay between actions
          await page.waitForTimeout(500);
        }
      }

      const result = {
        url,
        timestamp: new Date().toISOString(),
        success: true,
        actionsExecuted: actions?.length || 0
      };

      // Extract data after actions
      if (extractAfter) {
        if (extractAfter.selectors) {
          const extractedData = {};
          for (const [key, selector] of Object.entries(extractAfter.selectors)) {
            try {
              const elements = await page.$$(selector);
              if (elements.length === 1) {
                extractedData[key] = await page.$eval(selector, el => el.textContent?.trim());
              } else if (elements.length > 1) {
                extractedData[key] = await page.$$eval(selector, els =>
                  els.map(el => el.textContent?.trim())
                );
              } else {
                extractedData[key] = null;
              }
            } catch (err) {
              logger.warn(`Failed to extract data for selector ${selector}:`, err.message);
              extractedData[key] = null;
            }
          }
          result.data = extractedData;
        }

        if (extractAfter.javascript) {
          try {
            result.customData = await page.evaluate(extractAfter.javascript);
          } catch (err) {
            logger.warn('Failed to execute custom JavaScript:', err.message);
            result.customData = null;
          }
        }
      }

      result.pageInfo = {
        title: await page.title(),
        url: page.url()
      };

      await page.close();
      release();

      logger.info(`Dynamic content scraping completed successfully for: ${url}`);
      res.json(result);

    } catch (error) {
      if (page) await page.close();
      release();
      throw error;
    }

  } catch (error) {
    logger.error('Dynamic content scraping failed:', error);
    next(error);
  }
});

module.exports = router;
