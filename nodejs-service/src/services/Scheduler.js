const cron = require('node-cron');
const logger = require('../utils/logger');
const { v4: uuidv4 } = require('uuid');

class Scheduler {
  constructor(workflowEngine, metricsCollector) {
    this.workflowEngine = workflowEngine;
    this.metricsCollector = metricsCollector;
    this.scheduledJobs = new Map();
    this.jobHistory = [];
    this.isRunning = false;
  }

  // Start the scheduler
  start() {
    if (this.isRunning) {
      logger.warn('Scheduler is already running');
      return;
    }

    this.isRunning = true;
    logger.info('Scheduler started');

    // Start existing scheduled jobs
    for (const [jobId, job] of this.scheduledJobs) {
      if (job.enabled && !job.task) {
        this.startJob(jobId);
      }
    }
  }

  // Stop the scheduler
  stop() {
    if (!this.isRunning) {
      logger.warn('Scheduler is not running');
      return;
    }

    this.isRunning = false;
    
    // Stop all running jobs
    for (const [jobId, job] of this.scheduledJobs) {
      if (job.task) {
        job.task.stop();
        job.task = null;
      }
    }

    logger.info('Scheduler stopped');
  }

  // Create a scheduled job
  createScheduledJob(definition) {
    const jobId = uuidv4();
    const job = {
      id: jobId,
      name: definition.name || `Job-${jobId.slice(0, 8)}`,
      description: definition.description || '',
      workflowId: definition.workflowId,
      schedule: definition.schedule, // cron expression
      variables: definition.variables || {},
      enabled: definition.enabled !== false,
      timezone: definition.timezone || 'UTC',
      retryOnFailure: definition.retryOnFailure || false,
      maxRetries: definition.maxRetries || 3,
      notifyOnFailure: definition.notifyOnFailure || false,
      created: new Date().toISOString(),
      lastModified: new Date().toISOString(),
      lastRun: null,
      nextRun: null,
      runCount: 0,
      successCount: 0,
      failureCount: 0,
      task: null
    };

    // Validate cron expression
    if (!cron.validate(job.schedule)) {
      throw new Error(`Invalid cron expression: ${job.schedule}`);
    }

    // Validate workflow exists
    const workflow = this.workflowEngine.getWorkflow(job.workflowId);
    if (!workflow) {
      throw new Error(`Workflow not found: ${job.workflowId}`);
    }

    this.scheduledJobs.set(jobId, job);
    
    // Start the job if scheduler is running and job is enabled
    if (this.isRunning && job.enabled) {
      this.startJob(jobId);
    }

    logger.info(`Scheduled job created: ${job.name}`, {
      jobId,
      workflowId: job.workflowId,
      schedule: job.schedule
    });

    return job;
  }

  // Start a specific job
  startJob(jobId) {
    const job = this.scheduledJobs.get(jobId);
    if (!job) {
      throw new Error(`Job not found: ${jobId}`);
    }

    if (job.task) {
      logger.warn(`Job already running: ${job.name}`, { jobId });
      return;
    }

    try {
      job.task = cron.schedule(job.schedule, async () => {
        await this.executeJob(jobId);
      }, {
        scheduled: false,
        timezone: job.timezone
      });

      job.task.start();
      job.nextRun = this.getNextRunTime(job.schedule, job.timezone);

      logger.info(`Job started: ${job.name}`, {
        jobId,
        schedule: job.schedule,
        nextRun: job.nextRun
      });

    } catch (error) {
      logger.error(`Failed to start job: ${job.name}`, {
        jobId,
        error: error.message
      });
      throw error;
    }
  }

  // Stop a specific job
  stopJob(jobId) {
    const job = this.scheduledJobs.get(jobId);
    if (!job) {
      throw new Error(`Job not found: ${jobId}`);
    }

    if (job.task) {
      job.task.stop();
      job.task = null;
      job.nextRun = null;

      logger.info(`Job stopped: ${job.name}`, { jobId });
    }
  }

  // Execute a job
  async executeJob(jobId, manualExecution = false) {
    const job = this.scheduledJobs.get(jobId);
    if (!job) {
      throw new Error(`Job not found: ${jobId}`);
    }

    const executionId = uuidv4();
    const execution = {
      id: executionId,
      jobId,
      jobName: job.name,
      workflowId: job.workflowId,
      startTime: new Date().toISOString(),
      endTime: null,
      status: 'running',
      manual: manualExecution,
      retryAttempt: 0,
      error: null,
      workflowExecution: null
    };

    logger.info(`Executing job: ${job.name}`, {
      jobId,
      executionId,
      manual: manualExecution
    });

    try {
      job.runCount++;
      job.lastRun = execution.startTime;
      
      // Update next run time
      if (!manualExecution && job.task) {
        job.nextRun = this.getNextRunTime(job.schedule, job.timezone);
      }

      // Execute the workflow
      const workflowExecution = await this.workflowEngine.executeWorkflow(
        job.workflowId,
        job.variables
      );

      execution.workflowExecution = workflowExecution;
      execution.status = workflowExecution.status === 'completed' ? 'success' : 'failed';
      execution.endTime = new Date().toISOString();

      if (execution.status === 'success') {
        job.successCount++;
        logger.info(`Job completed successfully: ${job.name}`, {
          jobId,
          executionId,
          duration: `${Date.parse(execution.endTime) - Date.parse(execution.startTime)}ms`
        });
      } else {
        job.failureCount++;
        execution.error = workflowExecution.errors?.[0]?.error || 'Workflow execution failed';
        
        logger.error(`Job failed: ${job.name}`, {
          jobId,
          executionId,
          error: execution.error
        });

        // Handle retry logic
        if (job.retryOnFailure && execution.retryAttempt < job.maxRetries) {
          logger.info(`Retrying job: ${job.name}`, {
            jobId,
            retryAttempt: execution.retryAttempt + 1,
            maxRetries: job.maxRetries
          });

          // Schedule retry after 1 minute
          setTimeout(() => {
            this.retryJob(jobId, execution.retryAttempt + 1);
          }, 60000);
        }
      }

    } catch (error) {
      execution.status = 'error';
      execution.error = error.message;
      execution.endTime = new Date().toISOString();
      job.failureCount++;

      logger.error(`Job execution error: ${job.name}`, {
        jobId,
        executionId,
        error: error.message
      });
    }

    // Add to history
    this.jobHistory.push(execution);
    
    // Keep only last 1000 executions
    if (this.jobHistory.length > 1000) {
      this.jobHistory = this.jobHistory.slice(-1000);
    }

    return execution;
  }

  // Retry a failed job
  async retryJob(jobId, retryAttempt) {
    const job = this.scheduledJobs.get(jobId);
    if (!job) {
      logger.error(`Cannot retry, job not found: ${jobId}`);
      return;
    }

    if (retryAttempt > job.maxRetries) {
      logger.warn(`Max retries exceeded for job: ${job.name}`, { jobId, retryAttempt });
      return;
    }

    try {
      const execution = await this.executeJob(jobId, true);
      execution.retryAttempt = retryAttempt;
      
      if (execution.status !== 'success' && retryAttempt < job.maxRetries) {
        // Schedule next retry with exponential backoff
        const delay = Math.min(300000, 60000 * Math.pow(2, retryAttempt)); // Max 5 minutes
        setTimeout(() => {
          this.retryJob(jobId, retryAttempt + 1);
        }, delay);
      }

    } catch (error) {
      logger.error(`Retry failed for job: ${job.name}`, {
        jobId,
        retryAttempt,
        error: error.message
      });
    }
  }

  // Get next run time for a cron expression
  getNextRunTime(cronExpression, timezone = 'UTC') {
    try {
      const task = cron.schedule(cronExpression, () => {}, {
        scheduled: false,
        timezone
      });
      
      // This is a simplified approach - in production, use a proper cron parser
      const now = new Date();
      const nextRun = new Date(now.getTime() + 60000); // Approximate next minute
      return nextRun.toISOString();
    } catch (error) {
      logger.warn(`Failed to calculate next run time: ${error.message}`);
      return null;
    }
  }

  // Job management methods
  getJob(jobId) {
    return this.scheduledJobs.get(jobId);
  }

  getAllJobs() {
    return Array.from(this.scheduledJobs.values());
  }

  updateJob(jobId, updates) {
    const job = this.scheduledJobs.get(jobId);
    if (!job) {
      throw new Error(`Job not found: ${jobId}`);
    }

    // Stop current job if running
    if (job.task) {
      this.stopJob(jobId);
    }

    // Update job properties
    const updatedJob = {
      ...job,
      ...updates,
      id: jobId,
      lastModified: new Date().toISOString()
    };

    // Validate cron expression if changed
    if (updates.schedule && !cron.validate(updates.schedule)) {
      throw new Error(`Invalid cron expression: ${updates.schedule}`);
    }

    // Validate workflow if changed
    if (updates.workflowId) {
      const workflow = this.workflowEngine.getWorkflow(updates.workflowId);
      if (!workflow) {
        throw new Error(`Workflow not found: ${updates.workflowId}`);
      }
    }

    this.scheduledJobs.set(jobId, updatedJob);

    // Restart job if enabled and scheduler is running
    if (this.isRunning && updatedJob.enabled) {
      this.startJob(jobId);
    }

    logger.info(`Job updated: ${updatedJob.name}`, { jobId });
    return updatedJob;
  }

  deleteJob(jobId) {
    const job = this.scheduledJobs.get(jobId);
    if (!job) {
      throw new Error(`Job not found: ${jobId}`);
    }

    // Stop job if running
    if (job.task) {
      this.stopJob(jobId);
    }

    const deleted = this.scheduledJobs.delete(jobId);
    if (deleted) {
      logger.info(`Job deleted: ${job.name}`, { jobId });
    }

    return deleted;
  }

  // Execute job manually
  async executeJobManually(jobId) {
    return await this.executeJob(jobId, true);
  }

  // Get job execution history
  getJobHistory(jobId = null, limit = 50) {
    let history = this.jobHistory;
    
    if (jobId) {
      history = history.filter(execution => execution.jobId === jobId);
    }
    
    return history.slice(-limit);
  }

  // Get scheduler statistics
  getSchedulerStats() {
    const jobs = Array.from(this.scheduledJobs.values());
    const runningJobs = jobs.filter(job => job.task !== null);
    const enabledJobs = jobs.filter(job => job.enabled);
    
    const totalExecutions = this.jobHistory.length;
    const successfulExecutions = this.jobHistory.filter(e => e.status === 'success').length;
    const failedExecutions = this.jobHistory.filter(e => e.status === 'failed').length;

    return {
      isRunning: this.isRunning,
      totalJobs: jobs.length,
      enabledJobs: enabledJobs.length,
      runningJobs: runningJobs.length,
      totalExecutions,
      successfulExecutions,
      failedExecutions,
      successRate: totalExecutions > 0 ? Math.round((successfulExecutions / totalExecutions) * 100) : 100,
      upcomingJobs: runningJobs.filter(job => job.nextRun).length
    };
  }
}

module.exports = Scheduler;
