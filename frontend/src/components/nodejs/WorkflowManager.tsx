'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Workflow,
  Play,
  Pause,
  Plus,
  Edit,
  Trash2,
  Clock,
  CheckCircle,
  XCircle,
  AlertCircle,
  Calendar,
  Activity
} from 'lucide-react';
import { nodejsService } from '@/services/nodejsService';

interface WorkflowStep {
  name: string;
  type: 'navigate' | 'scrape' | 'screenshot' | 'pdf' | 'interact' | 'wait' | 'script';
  [key: string]: any;
}

interface WorkflowDefinition {
  id: string;
  name: string;
  description: string;
  steps: WorkflowStep[];
  config: {
    timeout: number;
    retryAttempts: number;
    continueOnError: boolean;
    parallel: boolean;
  };
  created: string;
  lastModified: string;
  status: string;
}

interface ScheduledJob {
  id: string;
  name: string;
  description: string;
  workflowId: string;
  schedule: string;
  enabled: boolean;
  lastRun: string | null;
  nextRun: string | null;
  runCount: number;
  successCount: number;
  failureCount: number;
}

interface WorkflowManagerProps {
  className?: string;
}

export default function WorkflowManager({ className }: WorkflowManagerProps) {
  const [workflows, setWorkflows] = useState<WorkflowDefinition[]>([]);
  const [scheduledJobs, setScheduledJobs] = useState<ScheduledJob[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState('workflows');

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Fetch workflows
      const workflowsData = await nodejsService.getWorkflows();

      // Fetch scheduled jobs (placeholder - will implement when scheduler endpoints are added)
      // const jobsData = await nodejsService.getScheduledJobs();

      if (workflowsData.success) {
        setWorkflows(workflowsData.data?.data?.workflows || []);
      }

      // Placeholder for scheduled jobs
      setScheduledJobs([]);

    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch data');
    } finally {
      setLoading(false);
    }
  };

  const executeWorkflow = async (workflowId: string) => {
    try {
      const data = await nodejsService.executeWorkflow(workflowId, { variables: {} });

      if (data.success) {
        alert('Workflow executed successfully!');
        fetchData();
      } else {
        alert(`Workflow execution failed: ${data.message}`);
      }
    } catch (err) {
      alert(`Error executing workflow: ${err}`);
    }
  };

  const deleteWorkflow = async (workflowId: string) => {
    if (!confirm('Are you sure you want to delete this workflow?')) return;

    try {
      const data = await nodejsService.deleteWorkflow(workflowId);

      if (data.success) {
        fetchData();
      } else {
        alert(`Failed to delete workflow: ${data.message}`);
      }
    } catch (err) {
      alert(`Error deleting workflow: ${err}`);
    }
  };

  const toggleJob = async (jobId: string, action: 'start' | 'stop') => {
    try {
      const response = await fetch(`/api/nodejs/scheduler/jobs/${jobId}/${action}`, {
        method: 'POST'
      });

      const data = await response.json();

      if (data.success) {
        fetchData();
      } else {
        alert(`Failed to ${action} job: ${data.error}`);
      }
    } catch (err) {
      alert(`Error ${action}ing job: ${err}`);
    }
  };

  const executeJob = async (jobId: string) => {
    try {
      const response = await fetch(`/api/nodejs/scheduler/jobs/${jobId}/execute`, {
        method: 'POST'
      });

      const data = await response.json();

      if (data.success) {
        alert('Job executed successfully!');
        fetchData();
      } else {
        alert(`Job execution failed: ${data.error}`);
      }
    } catch (err) {
      alert(`Error executing job: ${err}`);
    }
  };

  const getStepTypeIcon = (type: string) => {
    switch (type) {
      case 'navigate': return '🌐';
      case 'scrape': return '📊';
      case 'screenshot': return '📸';
      case 'pdf': return '📄';
      case 'interact': return '🖱️';
      case 'wait': return '⏳';
      case 'script': return '💻';
      default: return '❓';
    }
  };

  const getSuccessRate = (job: ScheduledJob) => {
    if (job.runCount === 0) return 100;
    return Math.round((job.successCount / job.runCount) * 100);
  };

  if (loading) {
    return (
      <Card className={className}>
        <CardContent className="flex items-center justify-center py-8">
          <Activity className="w-6 h-6 animate-spin mr-2" />
          <span>Loading workflows...</span>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className={className}>
        <CardContent className="flex items-center justify-center py-8">
          <AlertCircle className="w-6 h-6 text-red-500 mr-2" />
          <span className="text-red-600">{error}</span>
          <Button onClick={fetchData} variant="outline" size="sm" className="ml-4">
            Retry
          </Button>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className={`space-y-6 ${className}`}>
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Workflow className="w-5 h-5" />
            Workflow Manager
          </CardTitle>
        </CardHeader>
        <CardContent>
          <Tabs value={activeTab} onValueChange={setActiveTab}>
            <TabsList className="grid w-full grid-cols-2">
              <TabsTrigger value="workflows">Workflows ({workflows.length})</TabsTrigger>
              <TabsTrigger value="scheduled">Scheduled Jobs ({scheduledJobs.length})</TabsTrigger>
            </TabsList>

            <TabsContent value="workflows" className="space-y-4">
              <div className="flex justify-between items-center">
                <h3 className="text-lg font-semibold">Available Workflows</h3>
                <Button size="sm">
                  <Plus className="w-4 h-4 mr-2" />
                  Create Workflow
                </Button>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {workflows.map((workflow) => (
                  <Card key={workflow.id} className="hover:shadow-lg transition-shadow">
                    <CardHeader className="pb-3">
                      <div className="flex items-start justify-between">
                        <div>
                          <h4 className="font-semibold text-sm">{workflow.name}</h4>
                          <p className="text-xs text-gray-600 mt-1">{workflow.description}</p>
                        </div>
                        <Badge variant="outline" className="text-xs">
                          {workflow.steps.length} steps
                        </Badge>
                      </div>
                    </CardHeader>
                    <CardContent className="pt-0">
                      <div className="space-y-3">
                        <div className="flex flex-wrap gap-1">
                          {workflow.steps.slice(0, 3).map((step, index) => (
                            <span key={index} className="text-xs bg-gray-100 px-2 py-1 rounded">
                              {getStepTypeIcon(step.type)} {step.type}
                            </span>
                          ))}
                          {workflow.steps.length > 3 && (
                            <span className="text-xs text-gray-500">
                              +{workflow.steps.length - 3} more
                            </span>
                          )}
                        </div>

                        <div className="flex gap-2">
                          <Button
                            size="sm"
                            onClick={() => executeWorkflow(workflow.id)}
                            className="flex-1"
                          >
                            <Play className="w-3 h-3 mr-1" />
                            Run
                          </Button>
                          <Button size="sm" variant="outline">
                            <Edit className="w-3 h-3" />
                          </Button>
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => deleteWorkflow(workflow.id)}
                          >
                            <Trash2 className="w-3 h-3" />
                          </Button>
                        </div>

                        <div className="text-xs text-gray-500">
                          Created: {new Date(workflow.created).toLocaleDateString()}
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>

              {workflows.length === 0 && (
                <div className="text-center py-8 text-gray-500">
                  <Workflow className="w-12 h-12 mx-auto mb-4 opacity-50" />
                  <p>No workflows created yet</p>
                  <Button size="sm" className="mt-2">
                    <Plus className="w-4 h-4 mr-2" />
                    Create Your First Workflow
                  </Button>
                </div>
              )}
            </TabsContent>

            <TabsContent value="scheduled" className="space-y-4">
              <div className="flex justify-between items-center">
                <h3 className="text-lg font-semibold">Scheduled Jobs</h3>
                <Button size="sm">
                  <Calendar className="w-4 h-4 mr-2" />
                  Schedule Job
                </Button>
              </div>

              <div className="space-y-4">
                {scheduledJobs.map((job) => (
                  <Card key={job.id}>
                    <CardContent className="p-4">
                      <div className="flex items-center justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-3">
                            <h4 className="font-semibold">{job.name}</h4>
                            <Badge variant={job.enabled ? "default" : "secondary"}>
                              {job.enabled ? 'Enabled' : 'Disabled'}
                            </Badge>
                            <Badge variant="outline" className="text-xs">
                              {job.schedule}
                            </Badge>
                          </div>
                          <p className="text-sm text-gray-600 mt-1">{job.description}</p>

                          <div className="flex items-center gap-4 mt-2 text-xs text-gray-500">
                            <span className="flex items-center gap-1">
                              <Clock className="w-3 h-3" />
                              Runs: {job.runCount}
                            </span>
                            <span className="flex items-center gap-1">
                              <CheckCircle className="w-3 h-3 text-green-500" />
                              Success: {job.successCount}
                            </span>
                            <span className="flex items-center gap-1">
                              <XCircle className="w-3 h-3 text-red-500" />
                              Failed: {job.failureCount}
                            </span>
                            <span>
                              Rate: {getSuccessRate(job)}%
                            </span>
                          </div>

                          {job.nextRun && (
                            <div className="text-xs text-blue-600 mt-1">
                              Next run: {new Date(job.nextRun).toLocaleString()}
                            </div>
                          )}
                        </div>

                        <div className="flex gap-2">
                          <Button
                            size="sm"
                            onClick={() => executeJob(job.id)}
                            variant="outline"
                          >
                            <Play className="w-3 h-3" />
                          </Button>
                          <Button
                            size="sm"
                            onClick={() => toggleJob(job.id, job.enabled ? 'stop' : 'start')}
                            variant="outline"
                          >
                            {job.enabled ? <Pause className="w-3 h-3" /> : <Play className="w-3 h-3" />}
                          </Button>
                          <Button size="sm" variant="outline">
                            <Edit className="w-3 h-3" />
                          </Button>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>

              {scheduledJobs.length === 0 && (
                <div className="text-center py-8 text-gray-500">
                  <Calendar className="w-12 h-12 mx-auto mb-4 opacity-50" />
                  <p>No scheduled jobs yet</p>
                  <Button size="sm" className="mt-2">
                    <Calendar className="w-4 h-4 mr-2" />
                    Schedule Your First Job
                  </Button>
                </div>
              )}
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>
    </div>
  );
}
