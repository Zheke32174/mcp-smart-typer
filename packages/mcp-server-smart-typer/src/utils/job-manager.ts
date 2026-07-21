/**
 * Job Manager Utility
 * Handles async job ID generation and tracking
 */

import { randomUUID } from 'crypto';

const activeJobs = new Map<string, JobInfo>();

interface JobInfo {
  id: string;
  startTime: Date;
  operation: string;
  status: 'pending' | 'completed' | 'failed';
  metadata?: Record<string, any>;
}

/**
 * Generate a unique async job ID
 */
export function generateAsyncJobId(): string {
  return `job_${Date.now()}_${randomUUID().slice(0, 8)}`;
}

/**
 * Register a new job
 */
export function registerJob(id: string, operation: string, metadata?: Record<string, any>): void {
  activeJobs.set(id, {
    id,
    startTime: new Date(),
    operation,
    status: 'pending',
    metadata,
  });
}

/**
 * Update job status
 */
export function updateJobStatus(
  id: string,
  status: 'completed' | 'failed',
  metadata?: Record<string, any>
): void {
  const job = activeJobs.get(id);
  if (job) {
    job.status = status;
    if (metadata) {
      job.metadata = { ...job.metadata, ...metadata };
    }
  }
}

/**
 * Get job information
 */
export function getJobInfo(id: string): JobInfo | undefined {
  return activeJobs.get(id);
}

/**
 * Remove completed or failed jobs older than specified minutes
 */
export function cleanupOldJobs(olderThanMinutes: number = 60): number {
  const cutoffTime = new Date(Date.now() - olderThanMinutes * 60 * 1000);
  let cleanedCount = 0;

  for (const [id, job] of activeJobs.entries()) {
    if (job.status !== 'pending' && job.startTime < cutoffTime) {
      activeJobs.delete(id);
      cleanedCount++;
    }
  }

  return cleanedCount;
}

/**
 * Get all active jobs
 */
export function getActiveJobs(): JobInfo[] {
  return Array.from(activeJobs.values()).filter(job => job.status === 'pending');
}

/**
 * Get job statistics
 */
export function getJobStats(): {
  total: number;
  pending: number;
  completed: number;
  failed: number;
} {
  const jobs = Array.from(activeJobs.values());
  return {
    total: jobs.length,
    pending: jobs.filter(j => j.status === 'pending').length,
    completed: jobs.filter(j => j.status === 'completed').length,
    failed: jobs.filter(j => j.status === 'failed').length,
  };
}
