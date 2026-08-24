import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import fs from 'fs';
import path from 'path';

function workspaceApiPlugin() {
  return {
    name: 'workspace-api-plugin',
    configureServer(server: any) {
      server.middlewares.use((req: any, res: any, next: any) => {
        const url = new URL(req.url, `http://${req.headers.host}`);
        const pathname = url.pathname;

        // Base workspace directory path
        const workspaceDir = path.resolve(__dirname, '../workspace');

        if (pathname.startsWith('/stories') || pathname.startsWith('/api/v1/stories')) {
          res.setHeader('Content-Type', 'application/json');
          res.setHeader('Access-Control-Allow-Origin', '*');
          res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
          res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

          if (req.method === 'OPTIONS') {
            res.statusCode = 204;
            res.end();
            return;
          }

          // GET /stories
          if ((pathname === '/stories' || pathname === '/stories/' || pathname === '/api/v1/stories' || pathname === '/api/v1/stories/') && req.method === 'GET') {
            try {
              const stories = scanWorkspaceStories(workspaceDir);
              res.end(JSON.stringify(stories));
              return;
            } catch (err: any) {
              res.statusCode = 500;
              res.end(JSON.stringify({ error: err.message }));
              return;
            }
          }

          // GET /stories/:story_id/file?path=...
          if (pathname.includes('/file') && req.method === 'GET') {
            const filePathParam = url.searchParams.get('path');
            const parts = pathname.split('/').filter(Boolean);
            let storyId = parts[1];
            if (parts[0] === 'api' && parts[1] === 'v1') storyId = parts[3];

            if (!filePathParam) {
              res.statusCode = 400;
              res.end(JSON.stringify({ error: 'Missing path query parameter' }));
              return;
            }

            const content = getFileContent(workspaceDir, storyId, filePathParam);
            if (content !== null) {
              res.end(JSON.stringify({
                story_id: storyId,
                path: filePathParam,
                filename: path.basename(filePathParam),
                content
              }));
            } else {
              res.statusCode = 404;
              res.end(JSON.stringify({ error: `File ${filePathParam} not found for story ${storyId}` }));
            }
            return;
          }

          // GET /stories/:story_id/frontend/files
          if (pathname.endsWith('/frontend/files') && req.method === 'GET') {
            const parts = pathname.split('/').filter(Boolean);
            let storyId = parts[1];
            if (parts[0] === 'api' && parts[1] === 'v1') storyId = parts[3];

            const story = findStory(workspaceDir, storyId);
            if (story) {
              res.end(JSON.stringify({
                story_id: storyId,
                folder_path: story.frontend_folder_path,
                files: story.frontend_files
              }));
            } else {
              res.statusCode = 404;
              res.end(JSON.stringify({ error: `Story ${storyId} not found` }));
            }
            return;
          }

          // GET /stories/:story_id/backend/files
          if (pathname.endsWith('/backend/files') && req.method === 'GET') {
            const parts = pathname.split('/').filter(Boolean);
            let storyId = parts[1];
            if (parts[0] === 'api' && parts[1] === 'v1') storyId = parts[3];

            const story = findStory(workspaceDir, storyId);
            if (story) {
              res.end(JSON.stringify({
                story_id: storyId,
                folder_path: story.backend_folder_path,
                files: story.backend_files
              }));
            } else {
              res.statusCode = 404;
              res.end(JSON.stringify({ error: `Story ${storyId} not found` }));
            }
            return;
          }

          // POST /stories/:story_id/approve
          if (pathname.endsWith('/approve') && req.method === 'POST') {
            const parts = pathname.split('/').filter(Boolean);
            let storyId = parts[1];
            if (parts[0] === 'api' && parts[1] === 'v1') storyId = parts[3];

            updateStoryStatus(workspaceDir, storyId, 'Approved');
            res.end(JSON.stringify({
              success: true,
              message: `User Story ${storyId} approved successfully.`,
              story_id: storyId,
              status: 'Approved'
            }));
            return;
          }

          // POST /stories/:story_id/regenerate
          if (pathname.endsWith('/regenerate') && req.method === 'POST') {
            const parts = pathname.split('/').filter(Boolean);
            let storyId = parts[1];
            if (parts[0] === 'api' && parts[1] === 'v1') storyId = parts[3];

            res.end(JSON.stringify({
              success: true,
              message: `Regeneration triggered successfully for ${storyId}.`,
              story_id: storyId,
              status: 'Implementation'
            }));
            return;
          }

          // GET /stories/:story_id
          const parts = pathname.split('/').filter(Boolean);
          if ((parts.length === 2 && parts[0] === 'stories') || (parts.length === 4 && parts[0] === 'api')) {
            const storyId = parts[parts.length - 1];
            const story = findStory(workspaceDir, storyId);
            if (story) {
              res.end(JSON.stringify(story));
            } else {
              res.statusCode = 404;
              res.end(JSON.stringify({ error: `Story ${storyId} not found` }));
            }
            return;
          }
        }

        next();
      });
    }
  };
}

function findStory(workspaceDir: string, storyId: string) {
  const stories = scanWorkspaceStories(workspaceDir);
  return stories.find(s => s.id.toLowerCase() === storyId.toLowerCase());
}

function scanWorkspaceStories(workspaceDir: string): any[] {
  if (!fs.existsSync(workspaceDir)) return [];

  const storiesMap = new Map<string, any>();

  // Read workspace_manifest.json if available
  let manifestStories: any = {};
  const manifests = findFilesByName(workspaceDir, 'workspace_manifest.json');
  manifests.forEach(mpath => {
    try {
      const data = JSON.parse(fs.readFileSync(mpath, 'utf-8'));
      if (Array.isArray(data.stories)) {
        data.stories.forEach((st: any) => {
          const key = st.story_key || st.id || st.story_id;
          if (key) manifestStories[key] = st;
        });
      }
    } catch (e) {}
  });

  // Find all story folders
  const candidateDirs = findStoryDirs(workspaceDir);

  candidateDirs.forEach(sdir => {
    const sId = path.basename(sdir);
    if (!sId.toLowerCase().startsWith('us')) return;

    let title = `User Story ${sId}`;
    let description = `As a user, I want features for ${sId} so that I can achieve my goals.`;
    let status = 'Implementation';
    let epicKey = 'Authentication';
    let projectName = 'Employee Management System';

    if (manifestStories[sId]) {
      const mst = manifestStories[sId];
      title = mst.title || title;
      description = mst.description || mst.goal || description;
      epicKey = mst.epic_key || epicKey;
    }

    const storyJsonPath = path.join(sdir, 'story.json');
    if (fs.existsSync(storyJsonPath)) {
      try {
        const sdata = JSON.parse(fs.readFileSync(storyJsonPath, 'utf-8'));
        title = sdata.title || sdata.story_title || title;
        description = sdata.description || description;
        status = sdata.status || status;
        epicKey = sdata.epic || sdata.epic_key || epicKey;
      } catch (e) {}
    }

    const summaryJsonPath = path.join(sdir, 'StoryExecutionSummary.json');
    if (fs.existsSync(summaryJsonPath)) {
      try {
        const sumData = JSON.parse(fs.readFileSync(summaryJsonPath, 'utf-8'));
        epicKey = sumData.epic_key || epicKey;
        if (sumData.status === 'completed') status = 'Approved';
      } catch (e) {}
    }

    // Discover frontend files
    const frontendDir = path.join(sdir, 'frontend');
    const frontendFiles: string[] = [];
    if (fs.existsSync(frontendDir)) {
      getAllRelativeFiles(frontendDir, sdir, frontendFiles);
    }

    // Discover backend files
    const backendDir = path.join(sdir, 'backend');
    const backendFiles: string[] = [];
    if (fs.existsSync(backendDir)) {
      getAllRelativeFiles(backendDir, sdir, backendFiles);
    }

    const primaryFe = frontendFiles[0] || 'src/pages/auth/login.tsx';
    const primaryBe = backendFiles[0] || 'backend/api/auth.py';

    storiesMap.set(sId, {
      id: sId,
      story_id: sId,
      title,
      description,
      status,
      epic: epicKey,
      project: projectName,
      folder_path: sdir,
      frontend_file_path: primaryFe,
      backend_file_path: primaryBe,
      frontend_folder_path: `frontend/${path.dirname(primaryFe)}`.replace(/\/$/, ''),
      backend_folder_path: `backend/${path.dirname(primaryBe)}`.replace(/\/$/, ''),
      frontend_files: frontendFiles,
      backend_files: backendFiles
    });
  });

  return Array.from(storiesMap.values());
}

function findStoryDirs(dir: string): string[] {
  let results: string[] = [];
  if (!fs.existsSync(dir)) return results;

  const items = fs.readdirSync(dir, { withFileTypes: true });
  for (const item of items) {
    if (item.isDirectory()) {
      const fullPath = path.join(dir, item.name);
      if (item.name.toLowerCase().startsWith('us') || fs.existsSync(path.join(fullPath, 'story.json'))) {
        results.push(fullPath);
      }
      results = results.concat(findStoryDirs(fullPath));
    }
  }
  return results;
}

function findFilesByName(dir: string, filename: string): string[] {
  let results: string[] = [];
  if (!fs.existsSync(dir)) return results;
  const items = fs.readdirSync(dir, { withFileTypes: true });
  for (const item of items) {
    const fullPath = path.join(dir, item.name);
    if (item.isDirectory()) {
      results = results.concat(findFilesByName(fullPath, filename));
    } else if (item.name === filename) {
      results.push(fullPath);
    }
  }
  return results;
}

function getAllRelativeFiles(dir: string, baseDir: string, fileList: string[]) {
  if (!fs.existsSync(dir)) return;
  const items = fs.readdirSync(dir, { withFileTypes: true });
  for (const item of items) {
    const fullPath = path.join(dir, item.name);
    if (item.isDirectory()) {
      getAllRelativeFiles(fullPath, baseDir, fileList);
    } else if (item.isFile() && !item.name.startsWith('.')) {
      const relPath = path.relative(baseDir, fullPath).replace(/\\/g, '/');
      fileList.push(relPath);
    }
  }
}

function getFileContent(workspaceDir: string, storyId: string, filePath: string): string | null {
  const storyDirs = findStoryDirs(workspaceDir);
  const storyDir = storyDirs.find(d => path.basename(d).toLowerCase() === storyId.toLowerCase());

  let targetPath = storyDir ? path.join(storyDir, filePath) : path.join(workspaceDir, filePath);

  if (!fs.existsSync(targetPath) || !fs.statSync(targetPath).isFile()) {
    targetPath = path.join(workspaceDir, filePath);
  }

  if (fs.existsSync(targetPath) && fs.statSync(targetPath).isFile()) {
    return fs.readFileSync(targetPath, 'utf-8');
  }
  return null;
}

function updateStoryStatus(workspaceDir: string, storyId: string, status: string) {
  const storyDirs = findStoryDirs(workspaceDir);
  const storyDir = storyDirs.find(d => path.basename(d).toLowerCase() === storyId.toLowerCase());
  if (storyDir) {
    const storyJson = path.join(storyDir, 'story.json');
    let data: any = {};
    if (fs.existsSync(storyJson)) {
      try { data = JSON.parse(fs.readFileSync(storyJson, 'utf-8')); } catch (e) {}
    }
    data.status = status;
    fs.writeFileSync(storyJson, JSON.stringify(data, null, 2), 'utf-8');
  }
}

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react(), workspaceApiPlugin()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        secure: false,
      }
    }
  }
});
