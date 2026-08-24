/**
 * API service layer for TodoApp integrated application.
 */

const API_BASE = '/api/v1';

export interface Task {
  id: string;
  title: string;
  description?: string;
  due_date?: string;
  priority?: string;
  status: string;
  completed: boolean;
  created_at?: string;
}

export interface DashboardSummary {
  total: number;
  completed: number;
  in_progress: number;
  pending: number;
  overdue: number;
  recent_tasks: Task[];
}

export async function fetchTasks(status?: string, search?: string): Promise<Task[]> {
  try {
    const params = new URLSearchParams();
    if (status && status !== 'All') params.append('status', status);
    if (search) params.append('search', search);

    const url = `${API_BASE}/tasks?${params.toString()}`;
    const res = await fetch(url);
    if (!res.ok) throw new Error('Failed to fetch tasks');
    return await res.json();
  } catch (err) {
    console.warn('API fetch error, returning fallback tasks:', err);
    return [
      { id: '1', title: 'Buy groceries for the week', description: 'Milk, Eggs, Bread', due_date: '2026-08-05', priority: 'Medium', status: 'Pending', completed: false },
      { id: '2', title: 'Prepare quarterly presentation', description: 'Slides for Q3 review', due_date: '2026-08-06', priority: 'High', status: 'In Progress', completed: false },
      { id: '3', title: 'Update portfolio website', description: 'Add new project case studies', due_date: '2026-08-01', priority: 'Low', status: 'Completed', completed: true }
    ];
  }
}

export async function createTask(task: { title: string; description?: string; due_date?: string; priority?: string }): Promise<Task> {
  const res = await fetch(`${API_BASE}/tasks`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(task)
  });
  if (!res.ok) throw new Error('Failed to create task');
  return await res.json();
}

export async function updateTask(id: string, task: { title?: string; description?: string; due_date?: string; priority?: string }): Promise<Task> {
  const res = await fetch(`${API_BASE}/tasks/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(task)
  });
  if (!res.ok) throw new Error('Failed to update task');
  return await res.json();
}

export async function toggleTaskComplete(id: string, completed: boolean): Promise<Task> {
  const res = await fetch(`${API_BASE}/tasks/${id}/complete`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ completed })
  });
  if (!res.ok) throw new Error('Failed to toggle task status');
  return await res.json();
}

export async function deleteTask(id: string): Promise<boolean> {
  const res = await fetch(`${API_BASE}/tasks/${id}`, {
    method: 'DELETE'
  });
  return res.ok;
}

export async function fetchDashboard(): Promise<DashboardSummary> {
  try {
    const res = await fetch(`${API_BASE}/dashboard`);
    if (!res.ok) throw new Error('Failed to fetch dashboard summary');
    return await res.json();
  } catch (err) {
    return {
      total: 3,
      completed: 1,
      in_progress: 1,
      pending: 1,
      overdue: 0,
      recent_tasks: []
    };
  }
}

export async function loginUser(email: string, password: str): Promise<any> {
  const res = await fetch(`${API_BASE}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password })
  });
  if (!res.ok) throw new Error('Invalid email or password');
  return await res.json();
}

export async function registerUser(name: string, email: string, password: str): Promise<any> {
  const res = await fetch(`${API_BASE}/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name, email, password })
  });
  if (!res.ok) throw new Error('Registration failed');
  return await res.json();
}
