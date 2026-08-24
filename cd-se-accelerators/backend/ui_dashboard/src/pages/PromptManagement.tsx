import React, { useState, useEffect } from 'react';
import { API_BASE } from '../api/client';

interface PromptTemplate {
  id: string;
  prompt_code: string;
  prompt_name: string;
  description: string;
  agent_name: string;
  agent_version: string;
  llm_provider: string;
  model_name: string;
  prompt_template: string;
  prompt_version: string;
  status: string;
  is_active: boolean;
  updated_at: string;
}

interface PromptVersion {
  id: string;
  version_number: number;
  previous_version: string;
  prompt_snapshot: string;
  change_summary: string;
  changed_by: string;
  created_at: string;
}

interface PromptPerformance {
  prompt_template_id: string;
  total_runs: number;
  successful_runs: number;
  failed_runs: number;
  average_execution_time: number;
  average_tokens: number;
  average_cost: number;
}

export const PromptManagement: React.FC = () => {
  const [templates, setTemplates] = useState<PromptTemplate[]>([]);
  const [selectedTemplate, setSelectedTemplate] = useState<PromptTemplate | null>(null);
  const [versions, setVersions] = useState<PromptVersion[]>([]);
  const [performances, setPerformances] = useState<Record<string, PromptPerformance>>({});
  const [editingTemplate, setEditingTemplate] = useState<Partial<PromptTemplate> | null>(null);
  const [newTemplate, setNewTemplate] = useState<Partial<PromptTemplate> | null>(null);
  
  const [changeSummary, setChangeSummary] = useState('');
  const [rollbackVersion, setRollbackVersion] = useState<number | null>(null);

  // Fetch all templates and performance logs
  const fetchData = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/v1/prompt-templates`);
      const data = await res.json();
      if (data.success) {
        setTemplates(data.data);
      }

      const perfRes = await fetch(`${API_BASE}/api/v1/prompt-templates/performance`);
      const perfData = await perfRes.json();
      if (perfData.success) {
        const perfMap: Record<string, PromptPerformance> = {};
        perfData.data.forEach((p: PromptPerformance) => {
          perfMap[p.prompt_template_id] = p;
        });
        setPerformances(perfMap);
      }
    } catch (err) {
      console.error("Error fetching prompt templates", err);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  // Fetch version histories
  const fetchVersions = async (templateId: string) => {
    try {
      const res = await fetch(`${API_BASE}/api/v1/prompt-templates/${templateId}/versions`);
      const data = await res.json();
      if (data.success) {
        setVersions(data.data);
      }
    } catch (err) {
      console.error("Error fetching versions", err);
    }
  };

  const handleSelectTemplate = (t: PromptTemplate) => {
    setSelectedTemplate(t);
    fetchVersions(t.id);
  };

  const handleCreatePrompt = async () => {
    if (!newTemplate?.prompt_code || !newTemplate?.prompt_name || !newTemplate?.prompt_template) {
      alert("Please fill in all required fields.");
      return;
    }
    try {
      const res = await fetch(`${API_BASE}/api/v1/prompt-templates`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...newTemplate,
          agent_name: newTemplate.agent_name || "common",
          temperature: 0.2,
          max_tokens: 1024
        })
      });
      const data = await res.json();
      if (data.success) {
        setNewTemplate(null);
        fetchData();
      }
    } catch (err) {
      console.error("Error creating template", err);
    }
  };

  const handleUpdatePrompt = async () => {
    if (!selectedTemplate || !editingTemplate?.prompt_template) return;
    try {
      const res = await fetch(`${API_BASE}/api/v1/prompt-templates/${selectedTemplate.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          prompt_template: editingTemplate.prompt_template,
          prompt_name: editingTemplate.prompt_name || selectedTemplate.prompt_name,
          description: editingTemplate.description || selectedTemplate.description,
          change_summary: changeSummary || "Updated prompt template content",
          changed_by: "Admin"
        })
      });
      const data = await res.json();
      if (data.success) {
        setSelectedTemplate(data.data);
        setEditingTemplate(null);
        setChangeSummary('');
        fetchData();
        fetchVersions(selectedTemplate.id);
      }
    } catch (err) {
      console.error("Error updating template", err);
    }
  };

  const handleApprovePrompt = async (decision: 'Approved' | 'Rejected') => {
    if (!selectedTemplate) return;
    try {
      const res = await fetch(`${API_BASE}/api/v1/prompt-templates/${selectedTemplate.id}/approve`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          reviewer: "Governance Board",
          decision,
          comments: "Approved from governance page",
          approved_version: selectedTemplate.prompt_version
        })
      });
      const data = await res.json();
      if (data.success) {
        fetchData();
        alert(`Prompt template version ${selectedTemplate.prompt_version} marked as ${decision}`);
      }
    } catch (err) {
      console.error("Error approving template", err);
    }
  };

  const handleRollback = async () => {
    if (!selectedTemplate || !rollbackVersion) return;
    try {
      const res = await fetch(`${API_BASE}/api/v1/prompt-templates/${selectedTemplate.id}/rollback`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          target_version_number: rollbackVersion,
          changed_by: "Admin"
        })
      });
      const data = await res.json();
      if (data.success) {
        setRollbackVersion(null);
        fetchData();
        fetchVersions(selectedTemplate.id);
        alert(`Successfully rolled back to version ${data.data.rolled_back_to}`);
      }
    } catch (err) {
      console.error("Error rolling back template", err);
    }
  };

  return (
    <div className="p-6 max-w-7xl mx-auto text-gray-100 min-h-screen">
      <header className="mb-6 border-b border-gray-800 pb-4">
        <h1 className="text-2xl font-bold bg-gradient-to-r from-indigo-400 to-purple-400 bg-clip-text text-transparent">
          Prompt Template Management Dashboard
        </h1>
        <p className="text-sm text-gray-400">Store, version, audit, and roll back agent templates dynamically.</p>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        
        {/* Left Column: Prompts List */}
        <div className="lg:col-span-5 flex flex-col gap-4">
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-md font-bold text-white">Active Prompt Templates</h2>
              <button 
                onClick={() => setNewTemplate({})}
                className="px-3 py-1 text-xs font-semibold rounded bg-indigo-600 hover:bg-indigo-500 text-white transition-all"
              >
                + New Prompt
              </button>
            </div>

            <div className="flex flex-col gap-3 max-h-[500px] overflow-y-auto pr-1">
              {templates.map(t => {
                const perf = performances[t.id];
                const successRate = perf && perf.total_runs > 0 
                  ? ((perf.successful_runs / perf.total_runs) * 100).toFixed(1) + '%' 
                  : 'N/A';

                return (
                  <div 
                    key={t.id}
                    onClick={() => handleSelectTemplate(t)}
                    className={`p-3 border rounded-xl cursor-pointer transition-all ${
                      selectedTemplate?.id === t.id 
                        ? 'bg-indigo-950/20 border-indigo-500/50' 
                        : 'bg-black/20 border-gray-800 hover:border-gray-700'
                    }`}
                  >
                    <div className="flex items-start justify-between">
                      <div>
                        <span className="text-[10px] font-bold text-indigo-400 bg-indigo-950/40 px-2 py-0.5 rounded border border-indigo-900/30">
                          {t.prompt_code}
                        </span>
                        <h3 className="text-sm font-semibold text-white mt-2">{t.prompt_name}</h3>
                      </div>
                      <span className={`text-[10px] px-1.5 py-0.5 rounded font-bold ${
                        t.status === 'Approved' ? 'bg-green-950/40 border border-green-900 text-green-400' : 'bg-yellow-950/40 border border-yellow-900 text-yellow-400'
                      }`}>
                        {t.status}
                      </span>
                    </div>

                    <div className="grid grid-cols-3 gap-2 mt-3 pt-2 border-t border-gray-800/40 text-[10px] text-gray-400">
                      <div>Agent: <span className="text-white">{t.agent_name}</span></div>
                      <div>Ver: <span className="text-white">{t.prompt_version}</span></div>
                      <div>Success Rate: <span className="text-white">{successRate}</span></div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        {/* Right Column: Prompt Details & Action Workspace */}
        <div className="lg:col-span-7 flex flex-col gap-4">
          {newTemplate ? (
            <div className="bg-gray-900 border border-gray-800 rounded-xl p-5 flex flex-col gap-4">
              <h2 className="text-md font-bold text-white">Create New Prompt Template</h2>
              <div className="grid grid-cols-2 gap-4">
                <input 
                  type="text" 
                  placeholder="Prompt Code (e.g. agent2_db_gen)"
                  className="bg-black/40 border border-gray-800 rounded-lg p-2.5 text-xs text-white outline-none"
                  value={newTemplate.prompt_code || ''}
                  onChange={e => setNewTemplate({ ...newTemplate, prompt_code: e.target.value })}
                />
                <input 
                  type="text" 
                  placeholder="Prompt Name (e.g. Database DDL Generator)"
                  className="bg-black/40 border border-gray-800 rounded-lg p-2.5 text-xs text-white outline-none"
                  value={newTemplate.prompt_name || ''}
                  onChange={e => setNewTemplate({ ...newTemplate, prompt_name: e.target.value })}
                />
              </div>
              <textarea 
                placeholder="Raw Prompt Template content..."
                rows={10}
                className="bg-black/40 border border-gray-800 rounded-lg p-2.5 text-xs text-white font-mono outline-none"
                value={newTemplate.prompt_template || ''}
                onChange={e => setNewTemplate({ ...newTemplate, prompt_template: e.target.value })}
              />
              <div className="flex gap-3 justify-end">
                <button onClick={() => setNewTemplate(null)} className="px-4 py-2 text-xs rounded bg-white/5 hover:bg-white/10 text-white">
                  Cancel
                </button>
                <button onClick={handleCreatePrompt} className="px-4 py-2 text-xs rounded bg-indigo-600 hover:bg-indigo-500 text-white">
                  Create Template
                </button>
              </div>
            </div>
          ) : selectedTemplate ? (
            <div className="bg-gray-900 border border-gray-800 rounded-xl p-5 flex flex-col gap-4">
              <div className="flex items-center justify-between border-b border-gray-800 pb-3">
                <div>
                  <h2 className="text-md font-bold text-white">{selectedTemplate.prompt_name}</h2>
                  <p className="text-xs text-gray-400 mt-1">{selectedTemplate.description || 'No description provided'}</p>
                </div>
                <div className="flex gap-2">
                  <button 
                    onClick={() => handleApprovePrompt('Approved')}
                    className="px-3 py-1 text-xs font-semibold rounded bg-green-700/80 hover:bg-green-600 text-white transition-all"
                  >
                    Approve
                  </button>
                  <button 
                    onClick={() => setEditingTemplate(selectedTemplate)}
                    className="px-3 py-1 text-xs font-semibold rounded bg-indigo-600 hover:bg-indigo-500 text-white transition-all"
                  >
                    Edit Template
                  </button>
                </div>
              </div>

              {editingTemplate ? (
                <div className="flex flex-col gap-3">
                  <textarea 
                    rows={8}
                    className="w-full bg-black/40 border border-gray-800 rounded-lg p-3 text-xs text-white font-mono outline-none"
                    value={editingTemplate.prompt_template || ''}
                    onChange={e => setEditingTemplate({ ...editingTemplate, prompt_template: e.target.value })}
                  />
                  <input 
                    type="text" 
                    placeholder="Change summary (e.g. Added security constraint requirements)"
                    className="w-full bg-black/40 border border-gray-800 rounded-lg p-2.5 text-xs text-white outline-none"
                    value={changeSummary}
                    onChange={e => setChangeSummary(e.target.value)}
                  />
                  <div className="flex gap-2 justify-end">
                    <button onClick={() => setEditingTemplate(null)} className="px-3.5 py-1.5 text-xs rounded bg-white/5 hover:bg-white/10">
                      Cancel
                    </button>
                    <button onClick={handleUpdatePrompt} className="px-3.5 py-1.5 text-xs rounded bg-indigo-600 hover:bg-indigo-500 text-white">
                      Save Version
                    </button>
                  </div>
                </div>
              ) : (
                <div className="flex flex-col gap-4">
                  <div>
                    <h3 className="text-xs font-bold text-indigo-400 mb-2">Active Prompt Text</h3>
                    <pre className="bg-black/40 border border-gray-800 rounded-lg p-3 text-xs text-gray-300 font-mono overflow-x-auto whitespace-pre-wrap max-h-48 custom-scrollbar">
                      {selectedTemplate.prompt_template}
                    </pre>
                  </div>

                  <div>
                    <h3 className="text-xs font-bold text-indigo-400 mb-2">Version History snapshots</h3>
                    <div className="flex flex-col gap-2 max-h-36 overflow-y-auto pr-1">
                      {versions.map(v => (
                        <div key={v.id} className="flex items-center justify-between text-xs bg-black/20 p-2.5 border border-gray-800/80 rounded-lg">
                          <div>
                            <span className="font-bold text-white">Ver {v.version_number}.0</span>
                            <span className="text-gray-400 ml-2 italic">({v.change_summary})</span>
                          </div>
                          <button 
                            onClick={() => { setRollbackVersion(v.version_number); handleRollback(); }}
                            className="text-[10px] text-pink-400 hover:underline"
                          >
                            Rollback
                          </button>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="bg-gray-900 border border-gray-800 rounded-xl p-5 flex items-center justify-center min-h-[300px]">
              <p className="text-xs text-gray-500 italic">Select a template from list to review performance log, versions, and rollback capability.</p>
            </div>
          )}
        </div>

      </div>
    </div>
  );
};

export default PromptManagement;
