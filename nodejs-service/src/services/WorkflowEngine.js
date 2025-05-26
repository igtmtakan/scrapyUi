const logger = require('../utils/logger');
const { v4: uuidv4 } = require('uuid');

class WorkflowEngine {
  constructor(browserPool, metricsCollector) {
    this.browserPool = browserPool;
    this.metricsCollector = metricsCollector;
    this.workflows = new Map();
    this.runningWorkflows = new Map();
    this.workflowHistory = [];
  }

  // Create a new workflow
  createWorkflow(definition) {
    const workflowId = uuidv4();
    const workflow = {
      id: workflowId,
      name: definition.name || `Workflow-${workflowId.slice(0, 8)}`,
      description: definition.description || '',
      steps: definition.steps || [],
      config: {
        timeout: definition.timeout || 300000, // 5 minutes default
        retryAttempts: definition.retryAttempts || 3,
        continueOnError: definition.continueOnError || false,
        parallel: definition.parallel || false
      },
      created: new Date().toISOString(),
      lastModified: new Date().toISOString(),
      status: 'created'
    };

    this.workflows.set(workflowId, workflow);
    logger.info(`Workflow created: ${workflow.name}`, { workflowId, steps: workflow.steps.length });
    
    return workflow;
  }

  // Execute a workflow
  async executeWorkflow(workflowId, variables = {}) {
    const workflow = this.workflows.get(workflowId);
    if (!workflow) {
      throw new Error(`Workflow not found: ${workflowId}`);
    }

    const executionId = uuidv4();
    const execution = {
      id: executionId,
      workflowId,
      status: 'running',
      startTime: new Date().toISOString(),
      endTime: null,
      variables,
      results: [],
      errors: [],
      currentStep: 0
    };

    this.runningWorkflows.set(executionId, execution);
    logger.info(`Starting workflow execution: ${workflow.name}`, { executionId, workflowId });

    try {
      const startTime = Date.now();
      
      if (workflow.config.parallel) {
        await this.executeStepsParallel(workflow, execution);
      } else {
        await this.executeStepsSequential(workflow, execution);
      }

      execution.status = 'completed';
      execution.endTime = new Date().toISOString();
      
      const duration = Date.now() - startTime;
      this.metricsCollector.recordWorkflow(true, workflow.steps.length, duration);
      
      logger.info(`Workflow completed: ${workflow.name}`, { 
        executionId, 
        duration: `${duration}ms`,
        steps: execution.results.length 
      });

    } catch (error) {
      execution.status = 'failed';
      execution.endTime = new Date().toISOString();
      execution.errors.push({
        step: execution.currentStep,
        error: error.message,
        timestamp: new Date().toISOString()
      });

      this.metricsCollector.recordWorkflow(false, workflow.steps.length, Date.now() - Date.parse(execution.startTime));
      
      logger.error(`Workflow failed: ${workflow.name}`, { 
        executionId, 
        error: error.message,
        step: execution.currentStep 
      });

      if (!workflow.config.continueOnError) {
        throw error;
      }
    } finally {
      this.runningWorkflows.delete(executionId);
      this.workflowHistory.push(execution);
      
      // Keep only last 100 executions
      if (this.workflowHistory.length > 100) {
        this.workflowHistory = this.workflowHistory.slice(-100);
      }
    }

    return execution;
  }

  // Execute steps sequentially
  async executeStepsSequential(workflow, execution) {
    for (let i = 0; i < workflow.steps.length; i++) {
      execution.currentStep = i;
      const step = workflow.steps[i];
      
      logger.debug(`Executing step ${i + 1}/${workflow.steps.length}: ${step.type}`, { 
        executionId: execution.id,
        stepName: step.name 
      });

      try {
        const result = await this.executeStep(step, execution.variables, execution.results);
        execution.results.push({
          step: i,
          stepName: step.name,
          type: step.type,
          result,
          timestamp: new Date().toISOString(),
          success: true
        });

        // Update variables with step results
        if (step.outputVariable && result) {
          execution.variables[step.outputVariable] = result;
        }

      } catch (error) {
        const stepError = {
          step: i,
          stepName: step.name,
          type: step.type,
          error: error.message,
          timestamp: new Date().toISOString(),
          success: false
        };

        execution.errors.push(stepError);
        execution.results.push(stepError);

        if (!workflow.config.continueOnError) {
          throw error;
        }

        logger.warn(`Step failed but continuing: ${step.name}`, { 
          executionId: execution.id,
          error: error.message 
        });
      }
    }
  }

  // Execute steps in parallel
  async executeStepsParallel(workflow, execution) {
    const stepPromises = workflow.steps.map(async (step, index) => {
      try {
        logger.debug(`Executing parallel step ${index + 1}: ${step.type}`, { 
          executionId: execution.id,
          stepName: step.name 
        });

        const result = await this.executeStep(step, execution.variables, []);
        return {
          step: index,
          stepName: step.name,
          type: step.type,
          result,
          timestamp: new Date().toISOString(),
          success: true
        };
      } catch (error) {
        const stepError = {
          step: index,
          stepName: step.name,
          type: step.type,
          error: error.message,
          timestamp: new Date().toISOString(),
          success: false
        };

        execution.errors.push(stepError);
        
        if (!workflow.config.continueOnError) {
          throw error;
        }

        return stepError;
      }
    });

    const results = await Promise.allSettled(stepPromises);
    execution.results = results.map(result => 
      result.status === 'fulfilled' ? result.value : result.reason
    );
  }

  // Execute individual step
  async executeStep(step, variables, previousResults) {
    const { browser, release } = await this.browserPool.getBrowser();
    let page;

    try {
      page = await browser.newPage();
      
      // Set viewport if specified
      if (step.viewport) {
        await page.setViewport(step.viewport);
      }

      // Set user agent if specified
      if (step.userAgent) {
        await page.setUserAgent(step.userAgent);
      }

      switch (step.type) {
        case 'navigate':
          return await this.executeNavigateStep(page, step, variables);
        
        case 'scrape':
          return await this.executeScrapeStep(page, step, variables);
        
        case 'screenshot':
          return await this.executeScreenshotStep(page, step, variables);
        
        case 'pdf':
          return await this.executePDFStep(page, step, variables);
        
        case 'interact':
          return await this.executeInteractStep(page, step, variables);
        
        case 'wait':
          return await this.executeWaitStep(page, step, variables);
        
        case 'script':
          return await this.executeScriptStep(page, step, variables, previousResults);
        
        default:
          throw new Error(`Unknown step type: ${step.type}`);
      }

    } finally {
      if (page) await page.close();
      release();
    }
  }

  // Step execution methods
  async executeNavigateStep(page, step, variables) {
    const url = this.interpolateVariables(step.url, variables);
    await page.goto(url, {
      waitUntil: step.waitUntil || 'networkidle2',
      timeout: step.timeout || 30000
    });
    
    return {
      url: page.url(),
      title: await page.title()
    };
  }

  async executeScrapeStep(page, step, variables) {
    const data = {};
    
    if (step.selectors) {
      for (const [key, selector] of Object.entries(step.selectors)) {
        try {
          const elements = await page.$$(selector);
          if (elements.length === 1) {
            data[key] = await page.$eval(selector, el => el.textContent?.trim());
          } else if (elements.length > 1) {
            data[key] = await page.$$eval(selector, els => 
              els.map(el => el.textContent?.trim())
            );
          } else {
            data[key] = null;
          }
        } catch (error) {
          logger.warn(`Failed to scrape selector ${selector}:`, error.message);
          data[key] = null;
        }
      }
    }

    if (step.javascript) {
      try {
        const jsResult = await page.evaluate(step.javascript);
        data.customData = jsResult;
      } catch (error) {
        logger.warn('Failed to execute custom JavaScript:', error.message);
        data.customData = null;
      }
    }

    return data;
  }

  async executeScreenshotStep(page, step, variables) {
    const screenshotOptions = {
      fullPage: step.fullPage || false,
      type: step.type || 'png',
      ...step.options
    };

    const screenshot = await page.screenshot(screenshotOptions);
    
    return {
      size: screenshot.length,
      type: screenshotOptions.type,
      screenshot: screenshot.toString('base64')
    };
  }

  async executePDFStep(page, step, variables) {
    const pdfOptions = {
      format: step.format || 'A4',
      landscape: step.landscape || false,
      printBackground: step.printBackground !== false,
      ...step.options
    };

    const pdf = await page.pdf(pdfOptions);
    
    return {
      size: pdf.length,
      format: pdfOptions.format,
      pdf: pdf.toString('base64')
    };
  }

  async executeInteractStep(page, step, variables) {
    const results = [];
    
    for (const action of step.actions || []) {
      try {
        switch (action.type) {
          case 'click':
            await page.click(action.selector);
            break;
          case 'type':
            const text = this.interpolateVariables(action.value, variables);
            await page.type(action.selector, text);
            break;
          case 'select':
            await page.select(action.selector, action.value);
            break;
          case 'hover':
            await page.hover(action.selector);
            break;
        }
        
        results.push({
          action: action.type,
          selector: action.selector,
          success: true
        });
        
        // Wait between actions
        if (action.delay) {
          await page.waitForTimeout(action.delay);
        }
        
      } catch (error) {
        results.push({
          action: action.type,
          selector: action.selector,
          success: false,
          error: error.message
        });
      }
    }
    
    return { actions: results };
  }

  async executeWaitStep(page, step, variables) {
    if (step.selector) {
      await page.waitForSelector(step.selector, {
        timeout: step.timeout || 10000
      });
      return { waited: 'selector', selector: step.selector };
    } else if (step.delay) {
      await page.waitForTimeout(step.delay);
      return { waited: 'timeout', delay: step.delay };
    } else {
      await page.waitForLoadState(step.loadState || 'networkidle');
      return { waited: 'loadState', loadState: step.loadState || 'networkidle' };
    }
  }

  async executeScriptStep(page, step, variables, previousResults) {
    const context = {
      variables,
      previousResults,
      page
    };
    
    // Execute custom JavaScript with context
    const result = await page.evaluate((script, ctx) => {
      const func = new Function('context', script);
      return func(ctx);
    }, step.script, context);
    
    return result;
  }

  // Utility methods
  interpolateVariables(text, variables) {
    if (typeof text !== 'string') return text;
    
    return text.replace(/\{\{(\w+)\}\}/g, (match, varName) => {
      return variables[varName] || match;
    });
  }

  // Workflow management
  getWorkflow(workflowId) {
    return this.workflows.get(workflowId);
  }

  getAllWorkflows() {
    return Array.from(this.workflows.values());
  }

  deleteWorkflow(workflowId) {
    const deleted = this.workflows.delete(workflowId);
    if (deleted) {
      logger.info(`Workflow deleted: ${workflowId}`);
    }
    return deleted;
  }

  getRunningWorkflows() {
    return Array.from(this.runningWorkflows.values());
  }

  getWorkflowHistory(limit = 50) {
    return this.workflowHistory.slice(-limit);
  }

  // Statistics
  getWorkflowStats() {
    const total = this.workflows.size;
    const running = this.runningWorkflows.size;
    const completed = this.workflowHistory.filter(w => w.status === 'completed').length;
    const failed = this.workflowHistory.filter(w => w.status === 'failed').length;
    
    return {
      total,
      running,
      completed,
      failed,
      successRate: total > 0 ? Math.round((completed / (completed + failed)) * 100) : 100
    };
  }
}

module.exports = WorkflowEngine;
