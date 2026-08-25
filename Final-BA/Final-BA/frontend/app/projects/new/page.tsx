'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { Button } from '@/components/common/Button';
import { useWorkspaceStore } from '@/store/workspaceStore';
import { 
  ArrowLeft, 
  ArrowRight, 
  CheckCircle2, 
  Upload, 
  FileText, 
  Check, 
  AlertTriangle,
  ChevronRight
} from 'lucide-react';
import { FaJira, FaConfluence, FaGoogleDrive, FaFileWord, FaMicrosoft } from 'react-icons/fa';
import { cn } from '@/lib/utils';
import { ThinkingIndicator, MOCK_PIPELINE_STAGES } from '@/components/common/ThinkingIndicator';
import { api } from '@/services/api';

export default function NewProjectPage() {
  const router = useRouter();
  const { createWorkspace } = useWorkspaceStore();
  
  // Section 1: Project Details
  const [projectName, setProjectName] = useState('');
  const [businessUnit, setBusinessUnit] = useState('');
  const [clientName, setClientName] = useState('');
  const [projectType, setProjectType] = useState('');
  const [description, setDescription] = useState('');

  // Section 2: Document Source & Setup
  const [activeSource, setActiveSource] = useState<string>('ado');
  const [validationMode, setValidationMode] = useState<'final' | 'every-step'>('every-step');
  const [connections, setConnections] = useState<Record<string, boolean>>({});
  const [isVerifying, setIsVerifying] = useState<Record<string, boolean>>({});
  const [verifyErrors, setVerifyErrors] = useState<Record<string, string | null>>({});
  const [isProcessing, setIsProcessing] = useState(false);
  const [createError, setCreateError] = useState<string | null>(null);

  // Quality parameters
  const [confidenceThreshold, setConfidenceThreshold] = useState(0.8);
  const [maxRetryAttempts, setMaxRetryAttempts] = useState(3);

  // File upload state
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const fileInputRef = React.useRef<HTMLInputElement>(null);

  // Azure DevOps fields
  const [adoOrg, setAdoOrg] = useState('');
  const [adoProject, setAdoProject] = useState('');
  const [adoPat, setAdoPat] = useState('');
  const [adoImportMethod, setAdoImportMethod] = useState<'work-item'>('work-item');
  const [adoWorkItemId, setAdoWorkItemId] = useState('');

  // Jira fields
  const [jiraIssueKey, setJiraIssueKey] = useState('PROJ-25');
  const [jiraIncludeComments, setJiraIncludeComments] = useState(false);

  // SharePoint fields
  const [sharepointUrl, setSharepointUrl] = useState('https://itclouddestinations.sharepoint.com');
  const [sharepointLibrary, setSharepointLibrary] = useState('BA Accelerator');
  const [sharepointFolderPath, setSharepointFolderPath] = useState('');
  const [sharepointFileName, setSharepointFileName] = useState('');
  const [sharepointTenantId, setSharepointTenantId] = useState('');
  const [sharepointClientId, setSharepointClientId] = useState('');
  const [sharepointClientSecret, setSharepointClientSecret] = useState('');
  const [sharepointFiles, setSharepointFiles] = useState<any[]>([]);
  const [selectedSharepointFileName, setSelectedSharepointFileName] = useState<string>('all');

  const markConnected = (srcId: string) => {
    setConnections(prev => ({ ...prev, [srcId]: true }));
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      markConnected(activeSource);
    }
  };

  const handleVerifySharepoint = async () => {
    if (!sharepointUrl.trim() || !sharepointLibrary.trim()) return;
    setIsVerifying(prev => ({ ...prev, sharepoint: true }));
    setVerifyErrors(prev => ({ ...prev, sharepoint: null }));
    try {
      const res = await api.connectSharePoint(
        sharepointUrl, sharepointLibrary, sharepointFolderPath, sharepointFileName,
        sharepointTenantId, sharepointClientId, sharepointClientSecret
      );
      const files = res.supported_files || [];
      setSharepointFiles(files);
      if (files.length === 1) {
        setSelectedSharepointFileName(files[0].name);
      } else {
        setSelectedSharepointFileName('all');
      }
      markConnected('sharepoint');
    } catch (err: any) {
      setVerifyErrors(prev => ({ ...prev, sharepoint: err.message || 'SharePoint verification failed. Please check Site URL and Document Library.' }));
      setConnections(prev => ({ ...prev, sharepoint: false }));
    } finally {
      setIsVerifying(prev => ({ ...prev, sharepoint: false }));
    }
  };

  const handleVerifyJira = async () => {
    if (!jiraIssueKey.trim()) return;
    setIsVerifying(prev => ({ ...prev, jira: true }));
    setVerifyErrors(prev => ({ ...prev, jira: null }));
    try {
      await api.fetchJira(jiraIssueKey, jiraIncludeComments);
      markConnected('jira');
    } catch (err: any) {
      setVerifyErrors(prev => ({ ...prev, jira: err.message || 'Verification failed. Please check your Jira configuration and issue key.' }));
      setConnections(prev => ({ ...prev, jira: false }));
    } finally {
      setIsVerifying(prev => ({ ...prev, jira: false }));
    }
  };

  const handleVerifyAdo = async () => {
    if (!adoOrg.trim() || !adoProject.trim() || !adoPat.trim() || !adoWorkItemId.trim()) return;
    setIsVerifying(prev => ({ ...prev, ado: true }));
    setVerifyErrors(prev => ({ ...prev, ado: null }));
    try {
      await api.fetchAdoWorkItem(adoOrg, adoProject, adoPat, adoWorkItemId);
      markConnected('ado');
    } catch (err: any) {
      setVerifyErrors(prev => ({ ...prev, ado: err.message || 'Verification failed. Please check your Azure DevOps configuration.' }));
      setConnections(prev => ({ ...prev, ado: false }));
    } finally {
      setIsVerifying(prev => ({ ...prev, ado: false }));
    }
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!projectName.trim()) return;
    
    const newId = projectName.toLowerCase().replace(/\s+/g, '-');
    setIsProcessing(true);
    setCreateError(null);

    try {
      if (activeSource === 'upload' && selectedFile) {
        const importRes = await api.importDocument(selectedFile);
        localStorage.setItem(`wf_file_path_${newId}`, importRes.file_path);
        localStorage.setItem(`workflow_started_${newId}`, 'false');
      } else if (activeSource === 'sharepoint') {
        const targetFile = (selectedSharepointFileName && selectedSharepointFileName !== 'all') ? selectedSharepointFileName : sharepointFileName;
        const res = await api.startWorkflowFromSharePoint(
          sharepointUrl, sharepointLibrary, sharepointFolderPath, targetFile,
          confidenceThreshold, maxRetryAttempts, newId, validationMode,
          sharepointTenantId, sharepointClientId, sharepointClientSecret
        );
        localStorage.setItem(`workflow_started_${newId}`, 'true');
        localStorage.setItem(`wf_id_${newId}`, res.workflow_id || newId);
      } else if (activeSource === 'ado') {
        const res = await api.startWorkflowFromAdo(adoOrg, adoProject, adoPat, adoWorkItemId, confidenceThreshold, maxRetryAttempts, newId, validationMode);
        localStorage.setItem(`workflow_started_${newId}`, 'true');
        localStorage.setItem(`wf_id_${newId}`, res.workflow_id || newId);
      } else if (activeSource === 'jira') {
        const res = await api.startWorkflowFromJira(jiraIssueKey, jiraIncludeComments, confidenceThreshold, maxRetryAttempts, newId, validationMode);
        localStorage.setItem(`workflow_started_${newId}`, 'true');
        localStorage.setItem(`wf_id_${newId}`, res.workflow_id || newId);
      } else {
        localStorage.setItem(`workflow_started_${newId}`, 'true');
        localStorage.setItem(`wf_id_${newId}`, newId);
      }
      
      localStorage.setItem(`wf_validation_mode_${newId}`, validationMode);
      createWorkspace(projectName, description || `Generated from ${activeSource}`);
      
      // Clear route redirection into pipeline verticals
      router.push(`/projects/${newId}/processing`);
    } catch (err: any) {
      console.error("Failed to start workflow:", err);
      const msg: string = err?.message || String(err);
      if (msg.toLowerCase().includes('failed to fetch') || msg.toLowerCase().includes('networkerror')) {
        setCreateError('Cannot reach the backend. Make sure the FastAPI server is running on port 8000.');
      } else {
        setCreateError(`Failed to start workflow: ${msg}`);
      }
      setIsProcessing(false);
    }
  };

  const handleProcessingComplete = () => {
    const newId = projectName.toLowerCase().replace(/\s+/g, '-');
    createWorkspace(projectName, description || 'Generated from PRD'); 
    router.push(`/projects/${newId}/requirements`);
  };

  const sources = [
    { 
      id: 'ado', 
      label: 'Azure DevOps', 
      desc: 'Import from Azure Boards, Work Items and Wikis.',
      icon: <FileText className="w-5 h-5 text-blue-600" />,
      enabled: true
    },
    { 
      id: 'upload', 
      label: 'Local File Upload', 
      desc: 'Upload PDF, DOC, DOCX, XLS and XLSX files directly.',
      icon: <FaFileWord className="w-5 h-5 text-blue-600" />,
      enabled: true
    },
    { 
      id: 'jira', 
      label: 'Jira Cloud', 
      desc: 'Import requirements directly from Jira Epics or Stories.',
      icon: <FaJira className="w-5 h-5 text-blue-500" />,
      enabled: true
    },
    { 
      id: 'sharepoint', 
      label: 'SharePoint', 
      desc: 'Connect to Microsoft SharePoint document libraries.',
      icon: <FaMicrosoft className="w-5 h-5 text-teal-600" />,
      enabled: true
    },
    { 
      id: 'gdrive', 
      label: 'Google Drive', 
      desc: 'Import documents using a Google Drive shared link.',
      icon: <FaGoogleDrive className="w-5 h-5 text-green-500" />,
      enabled: true
    },
    {
      id: 'voice',
      label: 'Voice Transcript',
      desc: 'Connect to Voice and speech-to-text transcripts.',
      icon: <FileText className="w-5 h-5 text-purple-600" />,
      enabled: true
    }
  ];

  return (
    <div className="flex-1 flex flex-col min-h-screen bg-[#f8f9fc] text-[#111827] font-sans antialiased overflow-y-auto">
      <div className="flex-1 p-6 md:p-10 max-w-6xl w-full mx-auto space-y-8">
        
        {/* Breadcrumb */}
        <div className="flex items-center gap-2 text-xs text-gray-500 font-semibold">
          <Link href="/projects" className="hover:text-[#ff5733] transition-colors">Projects</Link>
          <ChevronRight className="w-3.5 h-3.5 text-gray-400" />
          <span className="text-[#ff5733] font-bold">Create New Project</span>
        </div>

        {/* Page Title Header */}
        <div>
          <h1 className="text-3xl font-extrabold tracking-tight text-gray-900">Create New Project</h1>
          <p className="text-sm text-gray-500 mt-1">
            Initialize a new requirement analysis workspace
          </p>
        </div>

        <form onSubmit={handleCreate} className="space-y-8">
          
          {/* Section 1: Project Details */}
          <div className="bg-white rounded-2xl border border-orange-100 shadow-[0_4px_20px_-2px_rgba(255,87,51,0.06)] p-6 md:p-8 space-y-6">
            <h2 className="text-base font-bold text-gray-900 border-b border-gray-100 pb-3">
              Section 1: Project Details
            </h2>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Project Name */}
              <div className="space-y-1.5">
                <label className="text-xs font-bold text-gray-700 block">
                  Project Name <span className="text-red-500">*</span>
                </label>
                <input 
                  type="text" 
                  value={projectName}
                  onChange={(e) => setProjectName(e.target.value)}
                  placeholder="e.g. Clarity Dental V3"
                  className="w-full bg-gray-50/60 border border-gray-200 rounded-xl px-4 py-2.5 text-xs text-gray-900 focus:outline-none focus:ring-2 focus:ring-[#ff5733]"
                  required
                />
              </div>

              {/* Business Unit */}
              <div className="space-y-1.5">
                <label className="text-xs font-bold text-gray-700 block">
                  Business Unit <span className="text-red-500">*</span>
                </label>
                <select 
                  value={businessUnit}
                  onChange={(e) => setBusinessUnit(e.target.value)}
                  className="w-full bg-gray-50/60 border border-gray-200 rounded-xl px-4 py-2.5 text-xs text-gray-900 focus:outline-none focus:ring-2 focus:ring-[#ff5733]"
                  required
                >
                  <option value="">Select Business Unit</option>
                  <option value="Retail">Retail</option>
                  <option value="Medical">Medical</option>
                  <option value="Operations">Operations</option>
                  <option value="Product">Product</option>
                  <option value="Platform">Platform</option>
                  <option value="Consumer">Consumer</option>
                </select>
              </div>

              {/* Client Name */}
              <div className="space-y-1.5">
                <label className="text-xs font-bold text-gray-700 block">Client Name</label>
                <input 
                  type="text" 
                  value={clientName}
                  onChange={(e) => setClientName(e.target.value)}
                  placeholder="e.g. FastLane Logistics"
                  className="w-full bg-gray-50/60 border border-gray-200 rounded-xl px-4 py-2.5 text-xs text-gray-900 focus:outline-none focus:ring-2 focus:ring-[#ff5733]"
                />
              </div>

              {/* Project Type */}
              <div className="space-y-1.5">
                <label className="text-xs font-bold text-gray-700 block">Project Type</label>
                <select 
                  value={projectType}
                  onChange={(e) => setProjectType(e.target.value)}
                  className="w-full bg-gray-50/60 border border-gray-200 rounded-xl px-4 py-2.5 text-xs text-gray-900 focus:outline-none focus:ring-2 focus:ring-[#ff5733]"
                >
                  <option value="">Select Project Type</option>
                  <option value="Replatforming">Replatforming</option>
                  <option value="Greenfield App">Greenfield App</option>
                  <option value="API Integration">API Integration</option>
                  <option value="Workflow Automation">Workflow Automation</option>
                  <option value="Legacy Migration">Legacy Migration</option>
                </select>
              </div>
            </div>

            {/* Description */}
            <div className="space-y-1.5">
              <label className="text-xs font-bold text-gray-700 block">Description</label>
              <textarea 
                rows={3}
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Provide context about the requirements and desired stories..."
                className="w-full bg-gray-50/60 border border-gray-200 rounded-xl px-4 py-2.5 text-xs text-gray-900 focus:outline-none focus:ring-2 focus:ring-[#ff5733]"
              />
            </div>
          </div>

          {/* Section 2: Document Source */}
          <div className="bg-white rounded-2xl border border-orange-100 shadow-[0_4px_20px_-2px_rgba(255,87,51,0.06)] p-6 md:p-8 space-y-6">
            <h2 className="text-base font-bold text-gray-900 border-b border-gray-100 pb-3">
              Section 2: Document Source
            </h2>

            {/* Grid of source cards */}
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
              {sources.map(src => {
                const isActive = activeSource === src.id;
                const isConnected = connections[src.id];
                return (
                  <button
                    key={src.id}
                    type="button"
                    onClick={() => setActiveSource(src.id)}
                    className={cn(
                      "p-4 rounded-2xl border text-left flex flex-col justify-between transition-all duration-200 relative",
                      isActive 
                        ? "border-[#ff5733] bg-orange-50/30 ring-2 ring-[#ff5733]/20 shadow-sm" 
                        : "border-gray-200 bg-white hover:border-gray-300 hover:bg-gray-50"
                    )}
                  >
                    <div className="flex items-center justify-between w-full mb-3">
                      <div className="w-9 h-9 rounded-xl bg-gray-50 border border-gray-200 flex items-center justify-center">
                        {src.icon}
                      </div>
                      {isActive && <CheckCircle2 className="w-5 h-5 text-[#ff5733]" />}
                    </div>
                    <div>
                      <div className="font-bold text-xs text-gray-900">{src.label}</div>
                      <div className="text-[11px] text-gray-500 mt-1 line-clamp-2">{src.desc}</div>
                    </div>
                    {isConnected && (
                      <span className="mt-2 text-[9px] font-bold text-emerald-600 bg-emerald-50 border border-emerald-200 px-2 py-0.5 rounded w-fit">
                        CONNECTED
                      </span>
                    )}
                  </button>
                );
              })}
            </div>

            {/* Dynamic Details Panel for Selected Source */}
            <div className="p-6 bg-gray-50/80 border border-gray-200/80 rounded-2xl space-y-4">
              {activeSource === 'ado' && (
                <div className="space-y-4 max-w-xl">
                  <div className="flex items-center gap-2 font-bold text-sm text-gray-900">
                    <FileText className="w-4 h-4 text-blue-600" /> Azure DevOps Integration
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <input 
                      type="text" 
                      value={adoOrg} 
                      onChange={(e) => setAdoOrg(e.target.value)} 
                      placeholder="Organization" 
                      className="bg-white border border-gray-200 rounded-xl px-3 py-2 text-xs" 
                    />
                    <input 
                      type="text" 
                      value={adoProject} 
                      onChange={(e) => setAdoProject(e.target.value)} 
                      placeholder="Project Name" 
                      className="bg-white border border-gray-200 rounded-xl px-3 py-2 text-xs" 
                    />
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <input 
                      type="password" 
                      value={adoPat} 
                      onChange={(e) => setAdoPat(e.target.value)} 
                      placeholder="Personal Access Token (PAT)" 
                      className="bg-white border border-gray-200 rounded-xl px-3 py-2 text-xs" 
                    />
                    <input 
                      type="text" 
                      value={adoWorkItemId} 
                      onChange={(e) => setAdoWorkItemId(e.target.value)} 
                      placeholder="Work Item ID (e.g. 12345)" 
                      className="bg-white border border-gray-200 rounded-xl px-3 py-2 text-xs" 
                    />
                  </div>
                  <Button 
                    type="button" 
                    size="sm" 
                    onClick={handleVerifyAdo}
                    disabled={isVerifying['ado']}
                    className="bg-[#ff5733] hover:bg-[#e04826] text-white text-xs font-bold rounded-xl"
                  >
                    {isVerifying['ado'] ? 'Verifying...' : 'Verify Azure Connection'}
                  </Button>
                </div>
              )}

              {activeSource === 'upload' && (
                <div className="space-y-4 max-w-xl">
                  <div className="flex items-center gap-2 font-bold text-sm text-gray-900">
                    <Upload className="w-4 h-4 text-blue-600" /> Local Document Upload
                  </div>
                  <input 
                    type="file" 
                    ref={fileInputRef} 
                    onChange={handleFileChange} 
                    className="hidden" 
                    accept=".pdf,.docx,.txt,.xlsx" 
                  />
                  <div 
                    onClick={() => fileInputRef.current?.click()}
                    className="p-6 border-2 border-dashed border-gray-300 rounded-2xl bg-white text-center cursor-pointer hover:border-[#ff5733] transition-colors"
                  >
                    <Upload className="w-8 h-8 mx-auto text-gray-400 mb-2" />
                    <span className="text-xs font-semibold text-gray-800 block">
                      {selectedFile ? selectedFile.name : 'Click to select PRD or Specification file'}
                    </span>
                    <span className="text-[11px] text-gray-400">Supports PDF, DOCX, TXT, XLSX</span>
                  </div>
                </div>
              )}

              {activeSource === 'jira' && (
                <div className="space-y-4 max-w-xl">
                  <div className="flex items-center gap-2 font-bold text-sm text-gray-900">
                    <FaJira className="w-4 h-4 text-blue-500" /> Jira Issue Import
                  </div>
                  <input 
                    type="text" 
                    value={jiraIssueKey} 
                    onChange={(e) => setJiraIssueKey(e.target.value)} 
                    placeholder="Jira Issue Key (e.g. PROJ-25)" 
                    className="w-full bg-white border border-gray-200 rounded-xl px-3 py-2 text-xs" 
                  />
                  <Button 
                    type="button" 
                    size="sm" 
                    onClick={handleVerifyJira}
                    disabled={isVerifying['jira']}
                    className="bg-[#ff5733] hover:bg-[#e04826] text-white text-xs font-bold rounded-xl"
                  >
                    {isVerifying['jira'] ? 'Verifying...' : 'Verify Jira Issue'}
                  </Button>
                </div>
              )}
            </div>

          </div>

          {/* Section 3: Preferences & Quality Gates */}
          <div className="bg-white rounded-2xl border border-orange-100 shadow-[0_4px_20px_-2px_rgba(255,87,51,0.06)] p-6 md:p-8 space-y-6">
            <h2 className="text-base font-bold text-gray-900 border-b border-gray-100 pb-3">
              Section 3: Preferences & Quality Gates
            </h2>

            <div className="space-y-6 max-w-3xl">
              
              {/* Confidence Threshold Gate */}
              <div className="p-5 bg-gray-50/80 border border-gray-200/80 rounded-2xl space-y-3">
                <div className="flex justify-between items-center">
                  <label className="text-xs font-bold text-gray-900">Confidence Threshold Gate</label>
                  <span className="text-xs font-extrabold text-[#ff5733] bg-orange-50 border border-orange-200 px-2.5 py-0.5 rounded-full">
                    {Math.round(confidenceThreshold * 100)}%
                  </span>
                </div>
                <p className="text-[11px] text-gray-500 leading-relaxed">
                  Define the threshold score required for user story auto-validation. Scores below this will flag the story for manual BA review.
                </p>
                <input 
                  type="range" 
                  min="0.0" 
                  max="1.0" 
                  step="0.05" 
                  value={confidenceThreshold} 
                  onChange={e => setConfidenceThreshold(parseFloat(e.target.value))}
                  className="w-full h-1.5 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-[#ff5733]"
                />
              </div>

              {/* Max Auto-Retry Attempts */}
              <div className="p-5 bg-gray-50/80 border border-gray-200/80 rounded-2xl space-y-3">
                <label className="text-xs font-bold text-gray-900 block">Max Auto-Retry Attempts</label>
                <p className="text-[11px] text-gray-500 leading-relaxed">
                  The maximum number of times the generator agents will try to self-correct a failed user story before throwing an error.
                </p>
                <select 
                  value={maxRetryAttempts}
                  onChange={e => setMaxRetryAttempts(parseInt(e.target.value))}
                  className="bg-white border border-gray-200 rounded-xl px-3 py-2 text-xs font-semibold text-gray-900 focus:outline-none focus:ring-2 focus:ring-[#ff5733]"
                >
                  {[1, 2, 3, 4, 5].map(v => (
                    <option key={v} value={v}>{v} {v === 1 ? 'Attempt' : 'Attempts'}</option>
                  ))}
                </select>
              </div>

              {/* Validation Mode Selection */}
              <div className="space-y-3">
                <label className="text-xs font-bold text-gray-900 block">Validation Mode</label>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  
                  {/* Step-by-Step Approval */}
                  <label 
                    onClick={() => setValidationMode('every-step')}
                    className={cn(
                      "p-5 rounded-2xl border cursor-pointer transition-all duration-200 relative flex flex-col justify-between",
                      validationMode === 'every-step'
                        ? "border-[#ff5733] bg-orange-50/30 ring-2 ring-[#ff5733]/20 shadow-sm"
                        : "border-gray-200 bg-white hover:bg-gray-50"
                    )}
                  >
                    <div>
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-xs font-bold text-gray-900 flex items-center gap-2">
                          Step-by-Step Approval
                          <span className="bg-[#ff5733]/10 text-[#ff5733] text-[9px] font-extrabold px-2 py-0.5 rounded-full uppercase tracking-wider">
                            Recommended
                          </span>
                        </span>
                        <CheckCircle2 className={cn("w-4 h-4", validationMode === 'every-step' ? "text-[#ff5733]" : "text-gray-300")} />
                      </div>
                      <p className="text-[11px] text-gray-500 leading-relaxed">
                        Review and approve at each individual stage of the pipeline for maximum control.
                      </p>
                    </div>
                  </label>

                  {/* End-to-End Automatic */}
                  <label 
                    onClick={() => setValidationMode('final')}
                    className={cn(
                      "p-5 rounded-2xl border cursor-pointer transition-all duration-200 relative flex flex-col justify-between",
                      validationMode === 'final'
                        ? "border-[#ff5733] bg-orange-50/30 ring-2 ring-[#ff5733]/20 shadow-sm"
                        : "border-gray-200 bg-white hover:bg-gray-50"
                    )}
                  >
                    <div>
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-xs font-bold text-gray-900">
                          End-to-End Automatic
                        </span>
                        <CheckCircle2 className={cn("w-4 h-4", validationMode === 'final' ? "text-[#ff5733]" : "text-gray-300")} />
                      </div>
                      <p className="text-[11px] text-gray-500 leading-relaxed">
                        Generate complete epics & stories, then review all at once. The AI checks its own work.
                      </p>
                    </div>
                  </label>

                </div>
              </div>

            </div>
          </div>


          {/* Error Message */}
          {createError && (
            <div className="flex items-center gap-3 p-4 bg-red-50 border border-red-200 text-red-700 text-xs rounded-xl font-semibold">
              <AlertTriangle className="w-4 h-4 shrink-0" />
              <span>{createError}</span>
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex items-center justify-between pt-4">
            <Link href="/projects">
              <button type="button" className="px-5 py-2.5 text-xs font-bold text-gray-600 bg-white border border-gray-200 rounded-xl hover:bg-gray-50">
                Cancel
              </button>
            </Link>

            {isProcessing ? (
              <div className="w-full max-w-sm">
                <ThinkingIndicator 
                  stages={MOCK_PIPELINE_STAGES.intake} 
                  onComplete={handleProcessingComplete} 
                />
              </div>
            ) : (
              <button 
                type="submit" 
                className="flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-[#ff6b4a] to-[#ff5733] text-white text-xs font-extrabold rounded-xl shadow-[0_4px_16px_rgba(255,87,51,0.35)] hover:opacity-95 transition-opacity"
              >
                Process Document <ArrowRight className="w-4 h-4 stroke-[2.5]" />
              </button>
            )}
          </div>

        </form>
      </div>
    </div>
  );
}
