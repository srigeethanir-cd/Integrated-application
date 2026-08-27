// Backend API Client — routes through Nginx proxy via relative paths by default
const getBaseUrl = (): string => {
  // If explicitly configured with an external API URL, use it
  if (process.env.NEXT_PUBLIC_API_URL && process.env.NEXT_PUBLIC_API_URL !== 'http://localhost:8000') {
    return process.env.NEXT_PUBLIC_API_URL.replace(/\/$/, '');
  }
  // In the browser, use relative path so requests go through Nginx at current origin
  if (typeof window !== 'undefined') {
    return '';
  }
  return '';
};

function buildUrl(path: string): string {
  const normalizedPath = path.startsWith('/') ? path : `/${path}`;
  const baseUrl = getBaseUrl();
  return `${baseUrl}${normalizedPath}`;
}

function getHeaders(isMultipart = false): HeadersInit {
  const headers: Record<string, string> = {};
  if (!isMultipart) {
    headers['Content-Type'] = 'application/json';
  }
  if (typeof window !== 'undefined') {
    const token = localStorage.getItem('auth_token');
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
  }
  return headers;
}

async function handleResponse(response: Response) {
  if (!response.ok) {
    let errorMsg = 'An error occurred';
    try {
      const errData = await response.json();
      errorMsg = errData.message || errData.detail || JSON.stringify(errData);
    } catch {
      errorMsg = response.statusText;
    }
    throw new Error(errorMsg);
  }
  return response.json();
}

async function performFetch(url: string, options: RequestInit): Promise<Response> {
  const targetUrl = buildUrl(url);
  try {
    return await fetch(targetUrl, options);
  } catch (err) {
    // If running in browser and relative path failed, rethrow
    if (typeof window !== 'undefined') {
      throw err;
    }
    // Server-side fallback: try localhost:8000 vs 127.0.0.1:8000
    const fallbackUrl = targetUrl.includes('localhost')
      ? targetUrl.replace('localhost', '127.0.0.1')
      : targetUrl.replace('127.0.0.1', 'localhost');
    try {
      return await fetch(fallbackUrl, options);
    } catch {
      throw err;
    }
  }
}

export const apiClient = {
  get: async (url: string, options?: RequestInit) => {
    const response = await performFetch(url, {
      method: 'GET',
      headers: getHeaders(),
      ...options,
    });
    return handleResponse(response);
  },

  post: async (url: string, data?: unknown, options?: RequestInit) => {
    const response = await performFetch(url, {
      method: 'POST',
      headers: getHeaders(),
      body: data !== undefined ? JSON.stringify(data) : undefined,
      ...options,
    });
    return handleResponse(response);
  },

  patch: async (url: string, data?: unknown, options?: RequestInit) => {
    const response = await performFetch(url, {
      method: 'PATCH',
      headers: getHeaders(),
      body: data !== undefined ? JSON.stringify(data) : undefined,
      ...options,
    });
    return handleResponse(response);
  },

  postMultipart: async (url: string, formData: FormData, options?: RequestInit) => {
    const response = await performFetch(url, {
      method: 'POST',
      headers: getHeaders(true),
      body: formData,
      ...options,
    });
    return handleResponse(response);
  }
};
