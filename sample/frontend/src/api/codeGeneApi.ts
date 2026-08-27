import { API_BASE } from './client';

/**
 * Code-Gene Agent API (Agent 0 — Visual Code Generator).
 * Backend route: POST /api/v1/code-gene/generate  (code_gene_routes.py)
 * Accepts: multipart/form-data with:
 *   - user_story (str) — the user story text
 *   - framework_type ('jsx' | 'tsx') — target framework
 *   - image (File) — wireframe screenshot
 * Returns: { frontend_code, backend_code, component_name, ... }
 */
export interface CodeGeneResult {
  component_name?: string;
  frontend_code?: string;
  backend_code?: string;
  framework_type?: string;
  generated_at?: string;
  error?: string;
  [key: string]: any;
}

export const codeGeneApi = {
  /**
   * Generate code from a user story + wireframe image.
   * Uses FormData because the backend expects a file upload (multipart/form-data).
   */
  generate: async (
    userStory: string,
    frameworkType: 'jsx' | 'tsx',
    imageFile: File
  ): Promise<CodeGeneResult> => {
    const formData = new FormData();
    formData.append('user_story', userStory);
    formData.append('framework_type', frameworkType);
    formData.append('image', imageFile, imageFile.name);

    const res = await fetch(`${API_BASE}/api/v1/code-gene/generate`, {
      method: 'POST',
      // DO NOT set Content-Type — browser sets it with correct multipart boundary
      body: formData,
    });

    if (!res.ok) {
      const err = await res.json().catch(() => null);
      throw new Error(
        err?.detail || err?.message || `Code-Gene generation failed (status ${res.status})`
      );
    }

    return res.json();
  },
};
