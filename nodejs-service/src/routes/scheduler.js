const express = require('express');
const Joi = require('joi');
const router = express.Router();
const logger = require('../utils/logger');

// Validation schemas
const scheduledJobSchema = Joi.object({
  name: Joi.string().required(),
  description: Joi.string().optional(),
  workflowId: Joi.string().required(),
  schedule: Joi.string().required(), // cron expression
  variables: Joi.object().optional(),
  enabled: Joi.boolean().optional(),
  timezone: Joi.string().optional(),
  retryOnFailure: Joi.boolean().optional(),
  maxRetries: Joi.number().min(0).max(10).optional(),
  notifyOnFailure: Joi.boolean().optional()
});

// Get scheduler status
router.get('/status', (req, res, next) => {
  try {
    const scheduler = req.scheduler;
    const stats = scheduler.getSchedulerStats();

    res.json({
      success: true,
      scheduler: {
        ...stats,
        timestamp: new Date().toISOString()
      }
    });

  } catch (error) {
    logger.error('Failed to get scheduler status:', error);
    next(error);
  }
});

// Start scheduler
router.post('/start', (req, res, next) => {
  try {
    const scheduler = req.scheduler;
    scheduler.start();

    logger.info('Scheduler started via API', { ip: req.ip });

    res.json({
      success: true,
      message: 'Scheduler started successfully'
    });

  } catch (error) {
    logger.error('Failed to start scheduler:', error);
    next(error);
  }
});

// Stop scheduler
router.post('/stop', (req, res, next) => {
  try {
    const scheduler = req.scheduler;
    scheduler.stop();

    logger.info('Scheduler stopped via API', { ip: req.ip });

    res.json({
      success: true,
      message: 'Scheduler stopped successfully'
    });

  } catch (error) {
    logger.error('Failed to stop scheduler:', error);
    next(error);
  }
});

// Create scheduled job
router.post('/jobs', async (req, res, next) => {
  try {
    const { error, value } = scheduledJobSchema.validate(req.body);
    if (error) {
      return res.status(400).json({
        error: 'Validation Error',
        details: error.details.map(d => d.message)
      });
    }

    const scheduler = req.scheduler;
    const job = scheduler.createScheduledJob(value);

    logger.info(`Scheduled job created: ${job.name}`, {
      jobId: job.id,
      workflowId: job.workflowId,
      schedule: job.schedule,
      ip: req.ip
    });

    res.status(201).json({
      success: true,
      message: 'Scheduled job created successfully',
      job
    });

  } catch (error) {
    logger.error('Failed to create scheduled job:', error);
    next(error);
  }
});

// Get all scheduled jobs
router.get('/jobs', (req, res, next) => {
  try {
    const scheduler = req.scheduler;
    const jobs = scheduler.getAllJobs();
    const stats = scheduler.getSchedulerStats();

    res.json({
      success: true,
      jobs,
      stats,
      total: jobs.length
    });

  } catch (error) {
    logger.error('Failed to get scheduled jobs:', error);
    next(error);
  }
});

// Get specific scheduled job
router.get('/jobs/:jobId', (req, res, next) => {
  try {
    const { jobId } = req.params;
    const scheduler = req.scheduler;
    const job = scheduler.getJob(jobId);

    if (!job) {
      return res.status(404).json({
        error: 'Scheduled job not found',
        jobId
      });
    }

    res.json({
      success: true,
      job
    });

  } catch (error) {
    logger.error('Failed to get scheduled job:', error);
    next(error);
  }
});

// Update scheduled job
router.put('/jobs/:jobId', async (req, res, next) => {
  try {
    const { jobId } = req.params;
    const { error, value } = scheduledJobSchema.validate(req.body);
    
    if (error) {
      return res.status(400).json({
        error: 'Validation Error',
        details: error.details.map(d => d.message)
      });
    }

    const scheduler = req.scheduler;
    const updatedJob = scheduler.updateJob(jobId, value);

    logger.info(`Scheduled job updated: ${updatedJob.name}`, {
      jobId,
      ip: req.ip
    });

    res.json({
      success: true,
      message: 'Scheduled job updated successfully',
      job: updatedJob
    });

  } catch (error) {
    logger.error('Failed to update scheduled job:', error);
    next(error);
  }
});

// Delete scheduled job
router.delete('/jobs/:jobId', (req, res, next) => {
  try {
    const { jobId } = req.params;
    const scheduler = req.scheduler;
    const job = scheduler.getJob(jobId);

    if (!job) {
      return res.status(404).json({
        error: 'Scheduled job not found',
        jobId
      });
    }

    const deleted = scheduler.deleteJob(jobId);

    if (deleted) {
      logger.info(`Scheduled job deleted: ${job.name}`, {
        jobId,
        ip: req.ip
      });

      res.json({
        success: true,
        message: 'Scheduled job deleted successfully',
        jobId
      });
    } else {
      res.status(500).json({
        error: 'Failed to delete scheduled job',
        jobId
      });
    }

  } catch (error) {
    logger.error('Failed to delete scheduled job:', error);
    next(error);
  }
});

// Execute job manually
router.post('/jobs/:jobId/execute', async (req, res, next) => {
  try {
    const { jobId } = req.params;
    const scheduler = req.scheduler;
    const job = scheduler.getJob(jobId);

    if (!job) {
      return res.status(404).json({
        error: 'Scheduled job not found',
        jobId
      });
    }

    logger.info(`Manual execution requested for job: ${job.name}`, {
      jobId,
      ip: req.ip
    });

    const execution = await scheduler.executeJobManually(jobId);

    res.json({
      success: true,
      message: 'Job executed manually',
      execution
    });

  } catch (error) {
    logger.error('Failed to execute job manually:', error);
    next(error);
  }
});

// Start specific job
router.post('/jobs/:jobId/start', (req, res, next) => {
  try {
    const { jobId } = req.params;
    const scheduler = req.scheduler;
    const job = scheduler.getJob(jobId);

    if (!job) {
      return res.status(404).json({
        error: 'Scheduled job not found',
        jobId
      });
    }

    scheduler.startJob(jobId);

    logger.info(`Job started: ${job.name}`, { jobId, ip: req.ip });

    res.json({
      success: true,
      message: 'Job started successfully',
      jobId
    });

  } catch (error) {
    logger.error('Failed to start job:', error);
    next(error);
  }
});

// Stop specific job
router.post('/jobs/:jobId/stop', (req, res, next) => {
  try {
    const { jobId } = req.params;
    const scheduler = req.scheduler;
    const job = scheduler.getJob(jobId);

    if (!job) {
      return res.status(404).json({
        error: 'Scheduled job not found',
        jobId
      });
    }

    scheduler.stopJob(jobId);

    logger.info(`Job stopped: ${job.name}`, { jobId, ip: req.ip });

    res.json({
      success: true,
      message: 'Job stopped successfully',
      jobId
    });

  } catch (error) {
    logger.error('Failed to stop job:', error);
    next(error);
  }
});

// Get job execution history
router.get('/jobs/:jobId/history', (req, res, next) => {
  try {
    const { jobId } = req.params;
    const limit = parseInt(req.query.limit) || 50;
    const scheduler = req.scheduler;
    
    const job = scheduler.getJob(jobId);
    if (!job) {
      return res.status(404).json({
        error: 'Scheduled job not found',
        jobId
      });
    }

    const history = scheduler.getJobHistory(jobId, limit);

    res.json({
      success: true,
      jobId,
      history,
      count: history.length
    });

  } catch (error) {
    logger.error('Failed to get job history:', error);
    next(error);
  }
});

// Get all execution history
router.get('/history', (req, res, next) => {
  try {
    const limit = parseInt(req.query.limit) || 100;
    const scheduler = req.scheduler;
    const history = scheduler.getJobHistory(null, limit);

    res.json({
      success: true,
      history,
      count: history.length
    });

  } catch (error) {
    logger.error('Failed to get execution history:', error);
    next(error);
  }
});

// Get scheduler statistics
router.get('/stats', (req, res, next) => {
  try {
    const scheduler = req.scheduler;
    const stats = scheduler.getSchedulerStats();
    const recentHistory = scheduler.getJobHistory(null, 10);

    res.json({
      success: true,
      stats: {
        ...stats,
        recentExecutions: recentHistory.length,
        lastExecution: recentHistory.length > 0 ? recentHistory[recentHistory.length - 1] : null
      }
    });

  } catch (error) {
    logger.error('Failed to get scheduler stats:', error);
    next(error);
  }
});

module.exports = router;
