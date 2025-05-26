const express = require('express');
const Joi = require('joi');
const router = express.Router();
const logger = require('../utils/logger');

// Validation schema for PDF generation
const pdfSchema = Joi.object({
  url: Joi.string().uri().optional(),
  html: Joi.string().optional(),
  options: Joi.object({
    format: Joi.string().valid('A4', 'A3', 'A2', 'A1', 'A0', 'Legal', 'Letter', 'Tabloid').default('A4'),
    landscape: Joi.boolean().default(false),
    margin: Joi.object({
      top: Joi.string().default('1cm'),
      right: Joi.string().default('1cm'),
      bottom: Joi.string().default('1cm'),
      left: Joi.string().default('1cm')
    }).optional(),
    printBackground: Joi.boolean().default(true),
    scale: Joi.number().min(0.1).max(2).default(1),
    displayHeaderFooter: Joi.boolean().default(false),
    headerTemplate: Joi.string().optional(),
    footerTemplate: Joi.string().optional()
  }).optional(),
  waitFor: Joi.alternatives().try(
    Joi.string(), // CSS selector
    Joi.number().min(0).max(30000) // milliseconds
  ).optional(),
  timeout: Joi.number().min(1000).max(60000).default(30000)
}).or('url', 'html');

// Generate PDF from URL or HTML
router.post('/generate', async (req, res, next) => {
  try {
    const { error, value } = pdfSchema.validate(req.body);
    if (error) {
      return res.status(400).json({
        error: 'Validation Error',
        details: error.details.map(d => d.message)
      });
    }

    const { url, html, options = {}, waitFor, timeout } = value;
    const browserPool = req.browserPool;

    logger.info(`Starting PDF generation for: ${url || 'HTML content'}`);

    const { browser, release } = await browserPool.getBrowser();
    let page;

    try {
      page = await browser.newPage();

      if (url) {
        await page.goto(url, {
          waitUntil: 'networkidle2',
          timeout
        });
      } else {
        await page.setContent(html, {
          waitUntil: 'networkidle2',
          timeout
        });
      }

      // Wait for specific condition
      if (waitFor) {
        if (typeof waitFor === 'string') {
          await page.waitForSelector(waitFor, { timeout: 10000 });
        } else {
          await page.waitForTimeout(waitFor);
        }
      }

      // Generate PDF
      const pdfBuffer = await page.pdf({
        format: options.format,
        landscape: options.landscape,
        margin: options.margin,
        printBackground: options.printBackground,
        scale: options.scale,
        displayHeaderFooter: options.displayHeaderFooter,
        headerTemplate: options.headerTemplate,
        footerTemplate: options.footerTemplate
      });

      await page.close();
      release();

      // Set response headers
      res.setHeader('Content-Type', 'application/pdf');
      res.setHeader('Content-Disposition', 'attachment; filename="generated.pdf"');
      res.setHeader('Content-Length', pdfBuffer.length);

      logger.info(`PDF generation completed successfully`);
      res.send(pdfBuffer);

    } catch (error) {
      if (page) await page.close();
      release();
      throw error;
    }

  } catch (error) {
    logger.error('PDF generation failed:', error);
    next(error);
  }
});

// Generate PDF and return as base64
router.post('/generate-base64', async (req, res, next) => {
  try {
    const { error, value } = pdfSchema.validate(req.body);
    if (error) {
      return res.status(400).json({
        error: 'Validation Error',
        details: error.details.map(d => d.message)
      });
    }

    const { url, html, options = {}, waitFor, timeout } = value;
    const browserPool = req.browserPool;

    logger.info(`Starting PDF generation (base64) for: ${url || 'HTML content'}`);

    const { browser, release } = await browserPool.getBrowser();
    let page;

    try {
      page = await browser.newPage();

      if (url) {
        await page.goto(url, {
          waitUntil: 'networkidle2',
          timeout
        });
      } else {
        await page.setContent(html, {
          waitUntil: 'networkidle2',
          timeout
        });
      }

      // Wait for specific condition
      if (waitFor) {
        if (typeof waitFor === 'string') {
          await page.waitForSelector(waitFor, { timeout: 10000 });
        } else {
          await page.waitForTimeout(waitFor);
        }
      }

      // Generate PDF
      const pdfBuffer = await page.pdf({
        format: options.format,
        landscape: options.landscape,
        margin: options.margin,
        printBackground: options.printBackground,
        scale: options.scale,
        displayHeaderFooter: options.displayHeaderFooter,
        headerTemplate: options.headerTemplate,
        footerTemplate: options.footerTemplate
      });

      await page.close();
      release();

      const result = {
        success: true,
        timestamp: new Date().toISOString(),
        source: url || 'HTML content',
        pdf: pdfBuffer.toString('base64'),
        size: pdfBuffer.length,
        options: options
      };

      logger.info(`PDF generation (base64) completed successfully`);
      res.json(result);

    } catch (error) {
      if (page) await page.close();
      release();
      throw error;
    }

  } catch (error) {
    logger.error('PDF generation (base64) failed:', error);
    next(error);
  }
});

module.exports = router;
