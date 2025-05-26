const express = require('express');
const Joi = require('joi');
const router = express.Router();
const logger = require('../utils/logger');

// Validation schema for screenshot capture
const screenshotSchema = Joi.object({
  url: Joi.string().uri().required(),
  options: Joi.object({
    fullPage: Joi.boolean().default(false),
    type: Joi.string().valid('png', 'jpeg').default('png'),
    quality: Joi.number().min(0).max(100).when('type', {
      is: 'jpeg',
      then: Joi.number().default(80),
      otherwise: Joi.forbidden()
    }),
    clip: Joi.object({
      x: Joi.number().min(0).required(),
      y: Joi.number().min(0).required(),
      width: Joi.number().min(1).required(),
      height: Joi.number().min(1).required()
    }).optional(),
    omitBackground: Joi.boolean().default(false)
  }).optional(),
  viewport: Joi.object({
    width: Joi.number().min(320).max(3840).default(1920),
    height: Joi.number().min(240).max(2160).default(1080),
    deviceScaleFactor: Joi.number().min(0.1).max(3).default(1)
  }).optional(),
  waitFor: Joi.alternatives().try(
    Joi.string(), // CSS selector
    Joi.number().min(0).max(30000) // milliseconds
  ).optional(),
  timeout: Joi.number().min(1000).max(60000).default(30000)
});

// Capture screenshot
router.post('/capture', async (req, res, next) => {
  try {
    const { error, value } = screenshotSchema.validate(req.body);
    if (error) {
      return res.status(400).json({
        error: 'Validation Error',
        details: error.details.map(d => d.message)
      });
    }

    const { url, options = {}, viewport, waitFor, timeout } = value;
    const browserPool = req.browserPool;

    logger.info(`Starting screenshot capture for: ${url}`);

    const { browser, release } = await browserPool.getBrowser();
    let page;

    try {
      page = await browser.newPage();

      // Set viewport
      if (viewport) {
        await page.setViewport(viewport);
      }

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
      }

      // Capture screenshot
      const screenshotBuffer = await page.screenshot({
        fullPage: options.fullPage,
        type: options.type,
        quality: options.quality,
        clip: options.clip,
        omitBackground: options.omitBackground
      });

      await page.close();
      release();

      // Set response headers
      const mimeType = options.type === 'jpeg' ? 'image/jpeg' : 'image/png';
      res.setHeader('Content-Type', mimeType);
      res.setHeader('Content-Disposition', `attachment; filename="screenshot.${options.type}"`);
      res.setHeader('Content-Length', screenshotBuffer.length);

      logger.info(`Screenshot capture completed successfully for: ${url}`);
      res.send(screenshotBuffer);

    } catch (error) {
      if (page) await page.close();
      release();
      throw error;
    }

  } catch (error) {
    logger.error('Screenshot capture failed:', error);
    next(error);
  }
});

// Capture screenshot and return as base64
router.post('/capture-base64', async (req, res, next) => {
  try {
    const { error, value } = screenshotSchema.validate(req.body);
    if (error) {
      return res.status(400).json({
        error: 'Validation Error',
        details: error.details.map(d => d.message)
      });
    }

    const { url, options = {}, viewport, waitFor, timeout } = value;
    const browserPool = req.browserPool;

    logger.info(`Starting screenshot capture (base64) for: ${url}`);

    const { browser, release } = await browserPool.getBrowser();
    let page;

    try {
      page = await browser.newPage();

      // Set viewport
      if (viewport) {
        await page.setViewport(viewport);
      }

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
      }

      // Capture screenshot
      const screenshotBuffer = await page.screenshot({
        fullPage: options.fullPage,
        type: options.type,
        quality: options.quality,
        clip: options.clip,
        omitBackground: options.omitBackground
      });

      await page.close();
      release();

      const result = {
        success: true,
        timestamp: new Date().toISOString(),
        url,
        screenshot: screenshotBuffer.toString('base64'),
        size: screenshotBuffer.length,
        options: options,
        viewport: viewport || { width: 1920, height: 1080 }
      };

      logger.info(`Screenshot capture (base64) completed successfully for: ${url}`);
      res.json(result);

    } catch (error) {
      if (page) await page.close();
      release();
      throw error;
    }

  } catch (error) {
    logger.error('Screenshot capture (base64) failed:', error);
    next(error);
  }
});

// Full page screenshot endpoint
router.get('/full-page', async (req, res, next) => {
  try {
    const url = req.query.url;
    if (!url) {
      return res.status(400).json({
        error: 'Missing URL parameter'
      });
    }

    const browserPool = req.browserPool;
    logger.info(`Starting full page screenshot for: ${url}`);

    const { browser, release } = await browserPool.getBrowser();
    let page;

    try {
      page = await browser.newPage();

      await page.goto(url, {
        waitUntil: 'networkidle2',
        timeout: 30000
      });

      // Capture full page screenshot
      const screenshotBuffer = await page.screenshot({
        fullPage: true,
        type: 'png'
      });

      await page.close();
      release();

      // Set response headers
      res.setHeader('Content-Type', 'image/png');
      res.setHeader('Content-Disposition', 'attachment; filename="fullpage-screenshot.png"');
      res.setHeader('Content-Length', screenshotBuffer.length);

      logger.info(`Full page screenshot completed successfully for: ${url}`);
      res.send(screenshotBuffer);

    } catch (error) {
      if (page) await page.close();
      release();
      throw error;
    }

  } catch (error) {
    logger.error('Full page screenshot failed:', error);
    next(error);
  }
});

module.exports = router;
