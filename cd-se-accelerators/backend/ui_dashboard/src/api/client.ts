export const API_BASE = (import.meta.env && import.meta.env.VITE_API_BASE_URL)
  ? import.meta.env.VITE_API_BASE_URL
  : typeof window !== 'undefined' && window.location.hostname
  ? `${window.location.protocol}//${window.location.hostname}:8005`
  : 'http://localhost:8005';


export async function safeFetch<T>(
  url: string,
  options: RequestInit = {}
): Promise<T> {
  const headers = {
    'Content-Type': 'application/json',
    Accept: 'application/json',
    ...(options.headers || {}),
  };

  const response = await fetch(url, { ...options, headers });
  
  if (!response.ok) {
    let errMsg = `Request failed with status ${response.status}`;
    try {
      const errorData = await response.json();
      errMsg = errorData?.detail || errorData?.message || errMsg;
    } catch {
      // ignore
    }
    throw new Error(errMsg);
  }

  const contentType = response.headers.get('content-type') || '';
  if (contentType.includes('application/json')) {
    return await response.json();
  }
  return (await response.text()) as unknown as T;
}
