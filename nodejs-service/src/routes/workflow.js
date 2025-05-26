const express = require('express');
const Joi = require('joi');
const router = express.Router();
const logger = require('../utils/logger');

// Validation schemas
const workflowStepSchema = Joi.object({
  name: Joi.string().required(),
  type: Joi.string().valid('navigate', 'scrape', 'screenshot', 'pdf', 'interact', 'wait', 'script').required(),
  url: Joi.string().uri().when('type', { is: 'navigate', then: Joi.required() }),
  selectors: Joi.object().pattern(Joi.string(), Joi.string()).when('type', { is: 'scrape', then: Joi.optional() }),
  javascript: Joi.string().when('type', { is: Joi.string().valid('scrape', 'script'), then: Joi.optional() }),
  actions: Joi.array().items(Joi.object({
    type: Joi.string().valid('click', 'type', 'select', 'hover').required(),
    selector: Joi.string().required(),
    value: Joi.string().optional(),
    delay: Joi.number().optional()
  })).when('type', { is: 'interact', then: Joi.optional() }),
  viewport: Joi.object({
    width: Joi.number().min(320).max(3840),
    height: Joi.number().min(240).max(2160)
  }).optional(),
  timeout: Joi.number().min(1000).max(60000).optional(),
  outputVariable: Joi.string().optional(),
  fullPage: Joi.boolean().when('type', { is: 'screenshot', then: Joi.optional() }),
  format: Joi.string().when('type', { is: 'pdf', then: Joi.optional() }),
  options: Joi.object().optional()
});

const workflowSchema = Joi.object({
  name: Joi.string().required(),
  description: Joi.string().optional(),
  steps: Joi.array().items(workflowStepSchema).min(1).required(),
  timeout: Joi.number().min(10000).max(3600000).optional(),
  retryAttempts: Joi.number().min(0).max(5).optional(),
  continueOnError: Joi.boolean().optional(),
  parallel: Joi.boolean().optional()
});

const executeWorkflowSchema = Joi.object({
  variables: Joi.object().optional()
});

// Create a new workflow
router.post('/', async (req, res, next) => {
  try {
    const { error, value } = workflowSchema.validate(req.body);
    if (error) {
      return res.status(400).json({
        error: 'Validation Error',
        details: error.details.map(d => d.message)
      });
    }

    const workflowEngine = req.workflowEngine;
    const workflow = workflowEngine.createWorkflow(value);

    logger.info(`Workflow created: ${workflow.name}`, {
      workflowId: workflow.id,
      steps: workflow.steps.length,
      ip: req.ip
    });

    res.status(201).json({
      success: true,
      message: 'Workflow created successfully',
      workflow
    });

  } catch (error) {
    logger.error('Failed to create workflow:', error);
    next(error);
  }
});

// Get all workflows
router.get('/', (req, res, next) => {
  try {
    const workflowEngine = req.workflowEngine;
    const workflows = workflowEngine.getAllWorkflows();
    const stats = workflowEngine.getWorkflowStats();

    res.json({
      success: true,
      workflows,
      stats,
      total: workflows.length
    });

  } catch (error) {
    logger.error('Failed to get workflows:', error);
    next(error);
  }
});

// Get specific workflow
router.get('/:workflowId', (req, res, next) => {
  try {
    const { workflowId } = req.params;
    const workflowEngine = req.workflowEngine;
    const workflow = workflowEngine.getWorkflow(workflowId);

    if (!workflow) {
      return res.status(404).json({
        error: 'Workflow not found',
        workflowId
      });
    }

    res.json({
      success: true,
      workflow
    });

  } catch (error) {
    logger.error('Failed to get workflow:', error);
    next(error);
  }
});

// Execute workflow
router.post('/:workflowId/execute', async (req, res, next) => {
  try {
    const { workflowId } = req.params;
    const { error, value } = executeWorkflowSchema.validate(req.body);
    
    if (error) {
      return res.status(400).json({
        error: 'Validation Error',
        details: error.details.map(d => d.message)
      });
    }

    const workflowEngine = req.workflowEngine;
    const workflow = workflowEngine.getWorkflow(workflowId);

    if (!workflow) {
      return res.status(404).json({
        error: 'Workflow not found',
        workflowId
      });
    }

    logger.info(`Executing workflow: ${workflow.name}`, {
      workflowId,
      variables: Object.keys(value.variables || {}),
      ip: req.ip
    });

    const execution = await workflowEngine.executeWorkflow(workflowId, value.variables);

    res.json({
      success: true,
      message: 'Workflow executed successfully',
      execution
    });

  } catch (error) {
    logger.error('Failed to execute workflow:', error);
    next(error);
  }
});

// Get running workflows
router.get('/status/running', (req, res, next) => {
  try {
    const workflowEngine = req.workflowEngine;
    const runningWorkflows = workflowEngine.getRunningWorkflows();

    res.json({
      success: true,
      runningWorkflows,
      count: runningWorkflows.length
    });

  } catch (error) {
    logger.error('Failed to get running workflows:', error);
    next(error);
  }
});

// Get workflow execution history
router.get('/history/executions', (req, res, next) => {
  try {
    const limit = parseInt(req.query.limit) || 50;
    const workflowEngine = req.workflowEngine;
    const history = workflowEngine.getWorkflowHistory(limit);

    res.json({
      success: true,
      history,
      count: history.length
    });

  } catch (error) {
    logger.error('Failed to get workflow history:', error);
    next(error);
  }
});

// Get workflow statistics
router.get('/stats/summary', (req, res, next) => {
  try {
    const workflowEngine = req.workflowEngine;
    const stats = workflowEngine.getWorkflowStats();
    const runningCount = workflowEngine.getRunningWorkflows().length;
    const recentHistory = workflowEngine.getWorkflowHistory(10);

    res.json({
      success: true,
      stats: {
        ...stats,
        running: runningCount,
        recentExecutions: recentHistory.length,
        lastExecution: recentHistory.length > 0 ? recentHistory[recentHistory.length - 1] : null
      }
    });

  } catch (error) {
    logger.error('Failed to get workflow stats:', error);
    next(error);
  }
});

// Update workflow
router.put('/:workflowId', async (req, res, next) => {
  try {
    const { workflowId } = req.params;
    const { error, value } = workflowSchema.validate(req.body);
    
    if (error) {
      return res.status(400).json({
        error: 'Validation Error',
        details: error.details.map(d => d.message)
      });
    }

    const workflowEngine = req.workflowEngine;
    const existingWorkflow = workflowEngine.getWorkflow(workflowId);

    if (!existingWorkflow) {
      return res.status(404).json({
        error: 'Workflow not found',
        workflowId
      });
    }

    // Update workflow
    const updatedWorkflow = {
      ...existingWorkflow,
      ...value,
      id: workflowId,
      lastModified: new Date().toISOString()
    };

    workflowEngine.workflows.set(workflowId, updatedWorkflow);

    logger.info(`Workflow updated: ${updatedWorkflow.name}`, {
      workflowId,
      steps: updatedWorkflow.steps.length,
      ip: req.ip
    });

    res.json({
      success: true,
      message: 'Workflow updated successfully',
      workflow: updatedWorkflow
    });

  } catch (error) {
    logger.error('Failed to update workflow:', error);
    next(error);
  }
});

// Delete workflow
router.delete('/:workflowId', (req, res, next) => {
  try {
    const { workflowId } = req.params;
    const workflowEngine = req.workflowEngine;
    const workflow = workflowEngine.getWorkflow(workflowId);

    if (!workflow) {
      return res.status(404).json({
        error: 'Workflow not found',
        workflowId
      });
    }

    const deleted = workflowEngine.deleteWorkflow(workflowId);

    if (deleted) {
      logger.info(`Workflow deleted: ${workflow.name}`, {
        workflowId,
        ip: req.ip
      });

      res.json({
        success: true,
        message: 'Workflow deleted successfully',
        workflowId
      });
    } else {
      res.status(500).json({
        error: 'Failed to delete workflow',
        workflowId
      });
    }

  } catch (error) {
    logger.error('Failed to delete workflow:', error);
    next(error);
  }
});

// Workflow templates
router.get('/templates/list', (req, res) => {
  const templates = [
    {
      id: 'ecommerce-scraping',
      name: 'E-commerce Product Scraping',
      description: '商品情報を取得し、スクリーンショットとPDFを生成',
      steps: [
        {
          name: 'Navigate to Product Page',
          type: 'navigate',
          url: '{{productUrl}}',
          timeout: 30000
        },
        {
          name: 'Scrape Product Data',
          type: 'scrape',
          selectors: {
            title: 'h1',
            price: '.price',
            description: '.description',
            availability: '.availability'
          },
          outputVariable: 'productData'
        },
        {
          name: 'Take Screenshot',
          type: 'screenshot',
          fullPage: true,
          outputVariable: 'screenshot'
        },
        {
          name: 'Generate PDF Report',
          type: 'pdf',
          format: 'A4',
          outputVariable: 'pdfReport'
        }
      ]
    },
    {
      id: 'form-automation',
      name: 'Form Automation Workflow',
      description: 'フォーム入力とデータ送信の自動化',
      steps: [
        {
          name: 'Navigate to Form',
          type: 'navigate',
          url: '{{formUrl}}'
        },
        {
          name: 'Fill Form',
          type: 'interact',
          actions: [
            { type: 'type', selector: '#name', value: '{{userName}}' },
            { type: 'type', selector: '#email', value: '{{userEmail}}' },
            { type: 'select', selector: '#category', value: '{{category}}' },
            { type: 'click', selector: '#submit' }
          ]
        },
        {
          name: 'Wait for Confirmation',
          type: 'wait',
          selector: '.success-message',
          timeout: 10000
        },
        {
          name: 'Capture Result',
          type: 'screenshot',
          outputVariable: 'confirmationScreenshot'
        }
      ]
    },
    {
      id: 'multi-page-scraping',
      name: 'Multi-page Data Collection',
      description: '複数ページからのデータ収集',
      steps: [
        {
          name: 'Navigate to List Page',
          type: 'navigate',
          url: '{{listUrl}}'
        },
        {
          name: 'Scrape Item Links',
          type: 'scrape',
          selectors: {
            links: '.item-link'
          },
          outputVariable: 'itemLinks'
        },
        {
          name: 'Process Each Item',
          type: 'script',
          script: `
            const results = [];
            for (const link of context.variables.itemLinks) {
              await context.page.goto(link);
              const data = await context.page.evaluate(() => ({
                title: document.querySelector('h1')?.textContent,
                content: document.querySelector('.content')?.textContent
              }));
              results.push(data);
            }
            return results;
          `,
          outputVariable: 'allItemsData'
        }
      ]
    }
  ];

  res.json({
    success: true,
    templates,
    count: templates.length
  });
});

module.exports = router;
