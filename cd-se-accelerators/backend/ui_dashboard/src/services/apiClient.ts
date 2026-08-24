import axios, { AxiosError, AxiosResponse, InternalAxiosRequestConfig } from 'axios';

const BASE_URL = import.meta.env.VITE_API_BASE_URL
  ?? (typeof window !== 'undefined' && window.location.hostname
      ? `${window.location.protocol}//${window.location.hostname}:8005/api/v1`
      : 'http://localhost:8005/api/v1');

export const apiClient = axios.create({
  baseURL: BASE_URL,
  timeout: 30_000,
  headers: {
    'Content-Type': 'application/json',
    Accept: 'application/json',
  },
});

// ─── Request interceptor ──────────────────────────────────────────────────────

apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    // Attach auth token when available
    const token = localStorage.getItem('ba_token');
    if (token && config.headers) {
      config.headers['Authorization'] = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error),
);

// ─── Response interceptor ─────────────────────────────────────────────────────

apiClient.interceptors.response.use(
  (response: AxiosResponse) => response,
  (error: AxiosError) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('ba_token');
    }
    return Promise.reject(error);
  },
);

// ─── Generic fetch helpers ────────────────────────────────────────────────────

export async function get<T>(url: string, params?: Record<string, unknown>): Promise<T> {
  const response = await apiClient.get<T>(url, { params });
  return response.data;
}

export async function post<T>(url: string, body?: unknown): Promise<T> {
  const response = await apiClient.post<T>(url, body);
  return response.data;
}

export async function patch<T>(url: string, body?: unknown): Promise<T> {
  const response = await apiClient.patch<T>(url, body);
  return response.data;
}

export async function del<T>(url: string): Promise<T> {
  const response = await apiClient.delete<T>(url);
  return response.data;
}
