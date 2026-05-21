import axios from "axios";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8001";

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 20000,
  headers: {
    "Content-Type": "application/json",
  },
});

export async function getDashboardStats() {
  const response = await apiClient.get("/dashboard/stats");
  return response.data.data;
}

export async function getEmails(params = {}) {
  const response = await apiClient.get("/emails", { params });
  return response.data.data;
}

export async function getSentimentTrend(params = {}) {
  const response = await apiClient.get("/analytics/sentiment-trend", {
    params,
  });
  return response.data.data;
}

export async function getCategoryBreakdown(params = {}) {
  const response = await apiClient.get("/analytics/category-breakdown", {
    params,
  });
  return response.data.data;
}

export async function runAgentDryRun(emailId) {
  const response = await apiClient.post(`/agent/dry-run/${emailId}`);
  return response.data.data;
}

export async function getEmailAudit(emailId) {
  const response = await apiClient.get(`/audit/email/${emailId}`);
  return response.data.data;
}

export async function getThreadAudit(threadId) {
  const response = await apiClient.get(`/audit/thread/${threadId}`);
  return response.data.data;
}

export async function getPendingActions(params = {}) {
  const response = await apiClient.get("/actions/pending", { params });
  return response.data.data;
}

export async function approveAction(actionId, approvedBy = "human_reviewer") {
  const response = await apiClient.post(`/actions/${actionId}/approve`, {
    approved_by: approvedBy,
  });
  return response.data.data;
}

export async function rejectAction(
  actionId,
  rejectedBy = "human_reviewer",
  reason = "Rejected during human review."
) {
  const response = await apiClient.post(`/actions/${actionId}/reject`, {
    rejected_by: rejectedBy,
    reason,
  });
  return response.data.data;
}