'use client';

import React, { useState, useMemo, useEffect, Suspense } from 'react';
import Link from 'next/link';
import { useRouter, useSearchParams } from 'next/navigation';
import { 
  Plus, Search, Bell, FileCheck, Layers, Clock, Folder, Filter, 
  ArrowUpRight, FileText, Sparkles, ChevronDown, BookOpen, GitBranch, 
  ListChecks, ShieldCheck, History, Download, Upload, Database, Cloud, 
  CheckCircle2, AlertTriangle, ArrowLeft, Sliders, RotateCw, Loader2, Trash2,
  BarChart3, Bot, Check, AlertOctagon, Send, Mic, XCircle, Globe
} from 'lucide-react';
import { useWorkspaceStore } from '@/store/workspaceStore';
import { api } from '@/services/api';

import RequirementsPage from '@/app/projects/[projectId]/requirements/page';
import EpicReviewPage from '@/app/projects/[projectId]/epics/page';
import StoryBoardPage from '@/app/projects/[projectId]/stories/page';
import FinalValidationPage from '@/app/projects/[projectId]/validation/page';
import VersioningPage from '@/app/projects/[projectId]/versioning/page';
import ExportPage from '@/app/projects/[projectId]/export/page';
import ProcessingPage from '@/app/projects/[projectId]/processing/page';

function DashboardContent() {
  const { workspaces, addWorkspace, removeWorkspace, updateWorkspaceTab } = useWorkspaceStore();
  const router = useRouter();
  const searchParams = useSearchParams();

  const [selectedProjectId, setSelectedProjectId] = useState<string>('');
  const [activeTab, setActiveTab] = useState<string>('Dashboard');

  // Sync state from query params if present on initial load
  useEffect(() => {
    const qTab = searchParams?.get('tab');
    const qProj = searchParams?.get('project');
    if (qProj) setSelectedProjectId(qProj);
    if (qTab) setActiveTab(qTab);
  }, [searchParams]);

  // Deleted Projects state (persisted locally so initial mock projects can also be deleted)
  const [deletedProjectIds, setDeletedProjectIds] = useState<string[]>([]);

  useEffect(() => {
    try {
      const stored = localStorage.getItem('ba_deleted_projects');
      if (stored) {
        setDeletedProjectIds(JSON.parse(stored));
      }
    } catch (e) {
      console.error(e);
    }
  }, []);

  const handleDeleteProject = (id: string, e?: React.MouseEvent) => {
    if (e) e.stopPropagation();
    if (typeof window !== 'undefined' && window.confirm('Are you sure you want to delete this project?')) {
      removeWorkspace(id);
      setDeletedProjectIds((prev) => {
        const next = [...prev, id];
        localStorage.setItem('ba_deleted_projects', JSON.stringify(next));
        return next;
      });
    }
  };

  // Dynamically calculate actual project stats from local mock storage
  const [projectStats, setProjectStats] = useState<Record<string, { docs: number, stories: number }>>({});

  useEffect(() => {
    let isMounted = true;
    
    // Process synchronously since we are just reading localStorage
    const stats: Record<string, { docs: number, stories: number }> = {};
    for (const w of workspaces) {
      let docs = 1; // Start with 1 for the PRD upload/final outcome document
      let stories = 0;
      
      try {
        const raw = localStorage.getItem(`wf_mock_state_${w.id}`);
        if (raw) {
          const parsed = JSON.parse(raw);
          // Account for both the standard .state wrapper, and legacy objects without it
          const stateObj = parsed.state || parsed || {};
          
          const sList = stateObj.user_stories || stateObj.stories || [];
          // Count any story that has a valid ID
          const valid = sList.filter((s: any) => s && (s.id || s.user_story_id));
          stories = valid.length;
        }
      } catch (err) {
        console.warn('Failed to parse stats for', w.id, err);
      }
      
      stats[w.id] = { docs, stories };
    }
    
    if (isMounted) {
      setProjectStats(stats);
    }
    
    return () => { isMounted = false; };
  }, [workspaces, activeTab]); // re-evaluate when tabs change or workspaces update

  // In-page New Project Mode State
  const [isCreatingNewProject, setIsCreatingNewProject] = useState(false);
  
  // New Project Form State
  const [projectName, setProjectName] = useState('');
  const [businessUnit, setBusinessUnit] = useState('Product');
  const [clientName, setClientName] = useState('');
  const [description, setDescription] = useState('');
  const [docSource, setDocSource] = useState('upload');
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [confidenceThreshold, setConfidenceThreshold] = useState(80);
  const [maxRetries, setMaxRetries] = useState(3);
  const [validationMode, setValidationMode] = useState('step-by-step');

  // Filter Bar State
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('All');
  const [businessUnitFilter, setBusinessUnitFilter] = useState('All');
  const [ownerFilter, setOwnerFilter] = useState('All');
  const [sortBy, setSortBy] = useState('Recently Updated');

  // AI Assistant Chat State
  const [chatMessages, setChatMessages] = useState<Array<{ sender: 'user' | 'assistant'; text: string; time: string }>>([
    {
      sender: 'assistant',
      text: 'Hello Sarah! I am your StoryForge AI Assistant. How can I help you refine requirements, check INVEST criteria, or format acceptance criteria today?',
      time: '10:00 AM',
    },
  ]);
  const [chatInput, setChatInput] = useState('');

  // Required Logical User Story Workflow Navigation Order
  const navTabs = [
    'Dashboard',
    'Projects',
    'Requirement Analysis',
    'Outline Review',
    'Story Board',
    'Validation Gate',
    'Document',
  ];

  // Initial Mock projects
  const initialProjects = [
    {
      id: 'test-after-initial',
      name: 'test-after the initial work',
      category: 'Product',
      client: 'Generated from upload',
      status: 'Active',
      docs: 6,
      storiesCount: 32,
      sprint: 'Sprint 10',
      owner: 'Sarah M.',
      updated: 'Aug 7, 2026, 3:33 PM',
      progress: 75,
      unit: 'Product',
    },
    {
      id: 'dry-run-demo',
      name: 'dry-run demo',
      category: 'Product',
      client: 'Generated from upload',
      status: 'Completed',
      docs: 6,
      storiesCount: 32,
      sprint: 'Sprint 10',
      owner: 'Sarah M.',
      updated: 'Jul 30, 2026, 12:25 PM',
      progress: 100,
      unit: 'Product',
    },
    {
      id: 'demo',
      name: 'demo',
      category: 'Product',
      client: 'Generated from upload',
      status: 'Active',
      docs: 6,
      storiesCount: 32,
      sprint: 'Sprint 10',
      owner: 'Sarah M.',
      updated: 'Jul 29, 2026, 3:32 PM',
      progress: 75,
      unit: 'Product',
    },
    {
      id: 'ui-fix',
      name: 'ui-fix',
      category: 'Product',
      client: 'Generated from upload',
      status: 'Active',
      docs: 6,
      storiesCount: 32,
      sprint: 'Sprint 10',
      owner: 'Sarah M.',
      updated: 'Jul 29, 2026, 1:44 PM',
      progress: 75,
      unit: 'Product',
    },
    {
      id: 'xbcxb',
      name: 'xbcxb',
      category: 'Product',
      client: 'Generated from upload',
      status: 'Active',
      docs: 6,
      storiesCount: 32,
      sprint: 'Sprint 10',
      owner: 'Sarah M.',
      updated: '03:16 pm',
      progress: 75,
      unit: 'Product',
    },
    {
      id: 'asd',
      name: 'asd',
      category: 'Product',
      client: 'Generated from upload',
      status: 'Active',
      docs: 6,
      storiesCount: 32,
      sprint: 'Sprint 10',
      owner: 'Sarah M.',
      updated: '03:03 pm',
      progress: 75,
      unit: 'Product',
    },
  ];

  // Combined projects list
  const allProjects = useMemo(() => {
    const storeItems = workspaces.map(w => ({
      id: w.id,
      name: w.name,
      category: 'Product',
      client: 'Generated from upload',
      status: w.status === 'completed' ? 'Completed' : 'Active',
      docs: projectStats[w.id]?.docs ?? 1,
      storiesCount: projectStats[w.id]?.stories ?? 0,
      sprint: 'Sprint 10',
      owner: 'Sarah M.',
      updated: w.updated_at || 'Aug 7, 2026, 4:30 PM',
      progress: w.status === 'completed' ? 100 : 75,
      unit: 'Product',
    }));

    const existingIds = new Set(storeItems.map(s => s.id));
    const nonDuplicateInitial = initialProjects.filter(p => !existingIds.has(p.id));

    return [...storeItems, ...nonDuplicateInitial].filter(p => !deletedProjectIds.includes(p.id));
  }, [workspaces, deletedProjectIds]);

  const filteredProjects = useMemo(() => {
    return allProjects.filter((project) => {
      if (searchQuery.trim() !== '') {
        const query = searchQuery.toLowerCase();
        const matchesName = project.name.toLowerCase().includes(query);
        const matchesClient = project.client.toLowerCase().includes(query);
        if (!matchesName && !matchesClient) return false;
      }
      if (statusFilter !== 'All' && project.status.toLowerCase() !== statusFilter.toLowerCase()) return false;
      if (businessUnitFilter !== 'All' && project.unit.toLowerCase() !== businessUnitFilter.toLowerCase()) return false;
      if (ownerFilter !== 'All' && project.owner.toLowerCase() !== ownerFilter.toLowerCase()) return false;
      return true;
    });
  }, [allProjects, searchQuery, statusFilter, businessUnitFilter, ownerFilter]);

  // Handle in-page workspace switching
  const handleOpenProjectInPage = (projectId: string, targetTab?: string) => {
    let resolvedTab = targetTab;
    if (!resolvedTab) {
      const w = workspaces.find(ws => ws.id === projectId);
      resolvedTab = w?.last_tab || 'Requirement Analysis';
    }
    setSelectedProjectId(projectId);
    setActiveTab(resolvedTab);
    setIsCreatingNewProject(false);
    updateWorkspaceTab(projectId, resolvedTab);
  };

  const handleCreateProjectSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!projectName.trim()) return;

    setIsUploading(true);
    try {
      let filePath = '';
      if (uploadedFile) {
        try {
          const uploadRes = await api.uploadFile(uploadedFile);
          filePath = uploadRes.file_path || (uploadRes as any).filename || '';
        } catch (err) {
          console.warn("Upload fallback:", err);
          filePath = uploadedFile.name;
        }
      }

      const pId = projectName.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/(^-|-$)/g, '') || `proj-${Date.now()}`;
      
      addWorkspace({
        id: pId,
        name: projectName,
        status: 'in_progress',
        created_at: new Date().toISOString(),
        updated_at: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      });

      if (filePath) {
        localStorage.setItem(`wf_file_path_${pId}`, filePath);
      }
      localStorage.setItem(`wf_validation_mode_${pId}`, validationMode);

      setSelectedProjectId(pId);
      setIsCreatingNewProject(false);
      setActiveTab('Pipeline');
    } catch (err) {
      console.error("Create project error:", err);
    } finally {
      setIsUploading(false);
    }
  };

  const handleSendMessage = (e: React.FormEvent) => {
    e.preventDefault();
    if (!chatInput.trim()) return;
    const userMsg = { sender: 'user' as const, text: chatInput, time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) };
    setChatMessages((prev) => [...prev, userMsg]);
    setChatInput('');

    setTimeout(() => {
      const botMsg = {
        sender: 'assistant' as const,
        text: `I've analyzed your input regarding "${userMsg.text}". All acceptance criteria for project ${selectedProjectId} are INVEST compliant with a 92% confidence score.`,
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      setChatMessages((prev) => [...prev, botMsg]);
    }, 600);
  };

  return (
    <div className="flex-1 flex flex-col min-h-screen bg-[#F7F9FC] text-[#111827] font-sans antialiased overflow-y-auto">
      
      {/* ── Top Header Bar ─────────────────────────────────────────────────── */}
      <header className="flex items-center justify-between px-8 py-4 bg-white border-b border-[#E5E7EB] shrink-0">
        <div className="flex-1 max-w-md relative">
          <Search className="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-[#A0AEC0]" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search projects, stories..."
            className="w-full pl-10 pr-4 py-2 text-xs bg-[#F7F9FC] border border-[#E5E7EB] rounded-full focus:outline-none focus:ring-2 focus:ring-[#7551FF] text-[#111827] placeholder-[#A0AEC0]"
          />
        </div>

        <div className="flex items-center gap-4">
          <button className="p-2 text-[#6B7280] hover:text-[#111827] hover:bg-[#F3F4F6] rounded-full transition-colors relative">
            <Bell className="w-4.5 h-4.5" />
            <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-[#FF602B] rounded-full" />
          </button>
          
          <div className="flex items-center gap-3 pl-2 border-l border-[#E5E7EB]">
            <img
              src="https://images.unsplash.com/photo-1494790108377-be9c29b29330?auto=format&fit=crop&q=80&w=120"
              alt="Sarah Jenkins"
              className="w-9 h-9 rounded-full object-cover border border-[#E5E7EB] shadow-sm"
            />
            <div className="flex flex-col text-left">
              <span className="text-xs font-bold text-[#111827] leading-tight">Sarah Jenkins</span>
              <span className="text-[11px] text-[#A0AEC0]">Product Owner</span>
            </div>
          </div>
        </div>
      </header>

      {/* ── Main Workspace Area ────────────────────────────────────────────── */}
      <main className="flex-1 px-8 py-6 space-y-6 max-w-7xl w-full mx-auto">
        
        {/* Welcome Banner & Action Button */}
        {(isCreatingNewProject || activeTab === 'Dashboard' || activeTab === 'Projects') && (
          <div className="flex items-start justify-between">
            <div>
              {(isCreatingNewProject || activeTab === 'Dashboard') && (
                <>
                  <h1 className="text-2xl font-bold text-[#111827] tracking-tight">
                    {isCreatingNewProject ? 'Create New Project' : 'Good morning, Sarah'}
                  </h1>
                  <p className="text-xs text-[#6B7280] mt-1">
                    {isCreatingNewProject ? 'Initialize a new requirement analysis workspace' : "Welcome back to your workspace. Let's forge some amazing stories today."}
                  </p>
                </>
              )}
            </div>

            {!isCreatingNewProject ? (
              <button 
                onClick={() => setIsCreatingNewProject(true)}
                className="flex items-center gap-2 px-6 py-2.5 bg-gradient-to-r from-[#FF602B] to-[#4318FF] text-white text-xs font-extrabold rounded-full shadow-[0_4px_16px_rgba(255,96,43,0.35)] hover:opacity-95 transition-opacity"
              >
                New Project
              </button>
            ) : (
              <button 
                onClick={() => setIsCreatingNewProject(false)}
                className="flex items-center gap-2 px-6 py-2.5 bg-[#F3F4F6] text-[#111827] text-xs font-bold rounded-full hover:bg-[#E5E7EB]"
              >
                <ArrowLeft className="w-4 h-4" /> Cancel
              </button>
            )}
          </div>
        )}

        {/* ── In-Page Workflow Tab Navigation (Logical Order) ──────────────── */}
        {!isCreatingNewProject && (
          <div className="flex items-center gap-2 overflow-x-auto pb-1">
            {navTabs.map(tab => {
              const isActive = activeTab === tab || 
                (tab === 'Outline Review' && (activeTab === 'Epics' || activeTab === 'Outline / Epics')) ||
                (tab === 'Story Board' && activeTab === 'Stories') ||
                (tab === 'Requirement Analysis' && activeTab === 'requirements');

              return (
                <button
                  key={tab}
                  onClick={() => {
                    setActiveTab(tab);
                    setIsCreatingNewProject(false);
                  }}
                  className={`px-4 py-1.5 text-xs font-bold rounded-md transition-all duration-200 whitespace-nowrap ${
                    isActive
                      ? 'bg-[#FF602B] text-white shadow-sm'
                      : 'bg-white text-[#6B7280] hover:bg-[#F3F4F6] hover:text-[#111827]'
                  }`}
                >
                  {tab}
                </button>
              );
            })}
          </div>
        )}

        {/* ======================================================================
            IN-PAGE CREATE NEW PROJECT FORM
           ====================================================================== */}
        {isCreatingNewProject && (
          <form onSubmit={handleCreateProjectSubmit} className="space-y-8 max-w-4xl bg-white p-8 rounded-3xl border border-[#E5E7EB] shadow-sm">
            
            {/* SECTION 1: Project Details */}
            <div className="space-y-4">
              <h2 className="text-base font-bold text-[#111827] border-b border-[#E5E7EB] pb-3 flex items-center gap-2">
                <span className="w-6 h-6 rounded-full bg-[#FF602B] text-white text-xs flex items-center justify-center font-bold">1</span>
                Project Details
              </h2>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-1.5">
                  <label className="text-xs font-bold text-[#111827] block">Project Name *</label>
                  <input
                    type="text"
                    required
                    value={projectName}
                    onChange={(e) => setProjectName(e.target.value)}
                    placeholder="e.g. Clarity Dental Portal V2"
                    className="w-full px-3.5 py-2.5 text-xs bg-[#F7F9FC] border border-[#E5E7EB] rounded-xl focus:outline-none focus:ring-2 focus:ring-[#7551FF]"
                  />
                </div>

                <div className="space-y-1.5">
                  <label className="text-xs font-bold text-[#111827] block">Business Unit *</label>
                  <select
                    value={businessUnit}
                    onChange={(e) => setBusinessUnit(e.target.value)}
                    className="w-full px-3.5 py-2.5 text-xs bg-[#F7F9FC] border border-[#E5E7EB] rounded-xl focus:outline-none focus:ring-2 focus:ring-[#7551FF]"
                  >
                    <option value="Product">Product</option>
                    <option value="Retail">Retail</option>
                    <option value="Medical">Medical</option>
                    <option value="Operations">Operations</option>
                    <option value="Platform">Platform</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-1.5">
                  <label className="text-xs font-bold text-[#111827] block">Client Name</label>
                  <input
                    type="text"
                    value={clientName}
                    onChange={(e) => setClientName(e.target.value)}
                    placeholder="e.g. FastLane Logistics"
                    className="w-full px-3.5 py-2.5 text-xs bg-[#F7F9FC] border border-[#E5E7EB] rounded-xl focus:outline-none focus:ring-2 focus:ring-[#7551FF]"
                  />
                </div>

                <div className="space-y-1.5">
                  <label className="text-xs font-bold text-[#111827] block">Project Description</label>
                  <input
                    type="text"
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    placeholder="e.g. Ingestion of PRD specification document"
                    className="w-full px-3.5 py-2.5 text-xs bg-[#F7F9FC] border border-[#E5E7EB] rounded-xl focus:outline-none focus:ring-2 focus:ring-[#7551FF]"
                  />
                </div>
              </div>
            </div>

            {/* SECTION 2: Document Source Injection */}
            <div className="space-y-4">
              <h2 className="text-base font-bold text-[#111827] border-b border-[#E5E7EB] pb-3 flex items-center gap-2">
                <span className="w-6 h-6 rounded-full bg-[#FF602B] text-white text-xs flex items-center justify-center font-bold">2</span>
                Document Source
              </h2>

              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 pb-4">
                
                {/* 1. Local Upload */}
                <div
                  onClick={() => setDocSource('upload')}
                  className={`w-full p-4 rounded-2xl border cursor-pointer transition-all flex flex-col items-start gap-2 text-left relative ${
                    docSource === 'upload' ? 'border-[#FF602B] ring-1 ring-[#FF602B] bg-white' : 'border-[#E5E7EB] bg-white opacity-60 hover:opacity-100'
                  }`}
                >
                  <div className="flex items-center justify-between w-full">
                    <Upload className={`w-5 h-5 ${docSource === 'upload' ? 'text-[#FF602B]' : 'text-blue-500'}`} />
                    {docSource === 'upload' && <span className="text-[9px] font-bold text-[#FF602B] bg-[#FFF0EB] px-2 py-0.5 rounded uppercase">Connected</span>}
                  </div>
                  <span className="text-sm font-bold text-[#111827] mt-1">Local Upload</span>
                  <p className="text-[10px] text-[#6B7280] leading-snug">Upload PDF, DOC, DOCX, XLS or recordings.</p>
                </div>

                {/* 2. Jira Cloud */}
                <div
                  onClick={() => setDocSource('jira')}
                  className={`w-full p-4 rounded-2xl border cursor-pointer transition-all flex flex-col items-start gap-2 text-left relative ${
                    docSource === 'jira' ? 'border-[#FF602B] ring-1 ring-[#FF602B] bg-white' : 'border-[#E5E7EB] bg-white opacity-60 hover:opacity-100'
                  }`}
                >
                  <div className="flex items-center justify-between w-full">
                    <XCircle className="w-5 h-5 text-blue-500" />
                    {docSource === 'jira' && <span className="text-[9px] font-bold text-[#FF602B] bg-[#FFF0EB] px-2 py-0.5 rounded uppercase">Connected</span>}
                  </div>
                  <span className="text-sm font-bold text-[#111827] mt-1">Jira Cloud</span>
                  <p className="text-[10px] text-[#6B7280] leading-snug">Import requirements directly from Jira Epics.</p>
                </div>

                {/* 3. Google Drive */}
                <div
                  onClick={() => setDocSource('google')}
                  className={`w-full p-4 rounded-2xl border cursor-pointer transition-all flex flex-col items-start gap-2 text-left relative ${
                    docSource === 'google' ? 'border-[#FF602B] ring-1 ring-[#FF602B] bg-white' : 'border-[#E5E7EB] bg-white opacity-60 hover:opacity-100'
                  }`}
                >
                  <div className="flex items-center justify-between w-full">
                    <XCircle className="w-5 h-5 text-emerald-500" />
                    {docSource === 'google' && <span className="text-[9px] font-bold text-[#FF602B] bg-[#FFF0EB] px-2 py-0.5 rounded uppercase">Connected</span>}
                  </div>
                  <span className="text-sm font-bold text-[#111827] mt-1">Google Drive</span>
                  <p className="text-[10px] text-[#6B7280] leading-snug">Import documents using Google drive connection.</p>
                </div>

                {/* 4. SharePoint */}
                <div
                  onClick={() => setDocSource('sharepoint')}
                  className={`w-full p-4 rounded-2xl border cursor-pointer transition-all flex flex-col items-start gap-2 text-left relative ${
                    docSource === 'sharepoint' ? 'border-[#FF602B] ring-1 ring-[#FF602B] bg-white' : 'border-[#E5E7EB] bg-white opacity-60 hover:opacity-100'
                  }`}
                >
                  <div className="flex items-center justify-between w-full">
                    <XCircle className="w-5 h-5 text-blue-600" />
                    {docSource === 'sharepoint' && <span className="text-[9px] font-bold text-[#FF602B] bg-[#FFF0EB] px-2 py-0.5 rounded uppercase">Connected</span>}
                  </div>
                  <span className="text-sm font-bold text-[#111827] mt-1">SharePoint</span>
                  <p className="text-[10px] text-[#6B7280] leading-snug">Connect to your corporate SharePoint repo.</p>
                </div>

                {/* 5. Voice Transcript */}
                <div
                  onClick={() => setDocSource('voice')}
                  className={`w-full p-4 rounded-2xl border cursor-pointer transition-all flex flex-col items-start gap-2 text-left relative ${
                    docSource === 'voice' ? 'border-[#FF602B] ring-1 ring-[#FF602B] bg-white' : 'border-[#E5E7EB] bg-white opacity-60 hover:opacity-100'
                  }`}
                >
                  <div className="flex items-center justify-between w-full">
                    <Mic className="w-5 h-5 text-purple-500" />
                    {docSource === 'voice' && <span className="text-[9px] font-bold text-[#FF602B] bg-[#FFF0EB] px-2 py-0.5 rounded uppercase">Connected</span>}
                  </div>
                  <span className="text-sm font-bold text-[#111827] mt-1">Voice Transcript</span>
                  <p className="text-[10px] text-[#6B7280] leading-snug">Extract stories from transcribed recordings.</p>
                </div>

                {/* 6. Azure DevOps */}
                <div
                  onClick={() => setDocSource('azure')}
                  className={`w-full p-4 rounded-2xl border cursor-pointer transition-all flex flex-col items-start gap-2 text-left relative ${
                    docSource === 'azure' ? 'border-[#FF602B] ring-1 ring-[#FF602B] bg-white' : 'border-[#E5E7EB] bg-white opacity-60 hover:opacity-100'
                  }`}
                >
                  <div className="flex items-center justify-between w-full">
                    <Cloud className="w-5 h-5 text-blue-500" />
                    {docSource === 'azure' && <span className="text-[9px] font-bold text-[#FF602B] bg-[#FFF0EB] px-2 py-0.5 rounded uppercase">Connected</span>}
                  </div>
                  <span className="text-sm font-bold text-[#111827] mt-1">Azure DevOps</span>
                  <p className="text-[10px] text-[#6B7280] leading-snug">Connect to your Azure boards and repos.</p>
                </div>
              </div>

              {/* Specific Source Inputs container */}
              <div className="p-6 rounded-xl bg-[#F7F9FC] border border-[#E5E7EB] flex flex-col items-center justify-center min-h-[200px] relative">
                
                {docSource === 'upload' && (
                  <div className="w-full max-w-lg text-center space-y-3">
                    <Upload className="w-8 h-8 mx-auto text-[#FF602B]" />
                    <div>
                      <label htmlFor="file-upload" className="cursor-pointer font-bold text-[#111827] block">
                        Upload PDF, DOC, DOCX, XLS, XLSX or Voice recordings.
                      </label>
                      <p className="text-xs text-[#6B7280] mt-1">Select a file from your file system. Max size limit 15MB.</p>
                      <input
                        id="file-upload"
                        type="file"
                        accept=".pdf,.docx,.txt"
                        onChange={(e) => setUploadedFile(e.target.files?.[0] || null)}
                        className="hidden"
                      />
                    </div>
                    {uploadedFile && (
                      <div className="mt-4 p-3 bg-white border border-[#E5E7EB] rounded-xl flex items-center gap-3 text-left w-full max-w-sm mx-auto shadow-sm">
                        <FileText className="w-6 h-6 text-[#FF602B]" />
                        <div>
                          <p className="text-xs font-bold text-[#111827]">{uploadedFile.name}</p>
                          <p className="text-[10px] text-[#6B7280]">{(uploadedFile.size / 1024).toFixed(0)} KB</p>
                        </div>
                      </div>
                    )}
                  </div>
                )}

                {docSource === 'sharepoint' && (
                  <div className="w-full max-w-lg text-center space-y-4">
                    <Globe className="w-8 h-8 mx-auto text-[#FF602B]" />
                    <div>
                      <p className="font-bold text-[#111827] block">Link SharePoint Repository</p>
                      <p className="text-xs text-[#6B7280] mt-1">Paste your corporate SharePoint document URL below.</p>
                    </div>
                    <input
                      type="url"
                      placeholder="e.g. https://company.sharepoint.com/sites/PRD"
                      className="w-full max-w-md mx-auto block px-4 py-3 text-xs bg-white border border-[#E5E7EB] rounded-xl focus:outline-none focus:ring-2 focus:ring-[#FF602B]"
                    />
                  </div>
                )}

                {docSource === 'jira' && (
                  <div className="w-full max-w-lg text-center space-y-4">
                    <Database className="w-8 h-8 mx-auto text-[#FF602B]" />
                    <div>
                      <p className="font-bold text-[#111827] block">Connect Jira Epic</p>
                      <p className="text-xs text-[#6B7280] mt-1">Provide the specific Jira Key for the epic you want to import.</p>
                    </div>
                    <input
                      type="text"
                      placeholder="e.g. PROJ-1234"
                      className="w-full max-w-md mx-auto block px-4 py-3 text-xs bg-white border border-[#E5E7EB] rounded-xl focus:outline-none focus:ring-2 focus:ring-[#FF602B]"
                    />
                  </div>
                )}

                {docSource === 'google' && (
                  <div className="w-full max-w-lg text-center space-y-4">
                    <Folder className="w-8 h-8 mx-auto text-[#FF602B]" />
                    <div>
                      <p className="font-bold text-[#111827] block">Link Google Drive Folder</p>
                      <p className="text-xs text-[#6B7280] mt-1">Provide the specific Google Drive link to import documents.</p>
                    </div>
                    <input
                      type="url"
                      placeholder="e.g. https://drive.google.com/drive/folders/xyz"
                      className="w-full max-w-md mx-auto block px-4 py-3 text-xs bg-white border border-[#E5E7EB] rounded-xl focus:outline-none focus:ring-2 focus:ring-[#FF602B]"
                    />
                  </div>
                )}

                {docSource === 'azure' && (
                  <div className="w-full max-w-lg text-center space-y-4">
                    <Cloud className="w-8 h-8 mx-auto text-[#FF602B]" />
                    <div>
                      <p className="font-bold text-[#111827] block">Connect Azure DevOps</p>
                      <p className="text-xs text-[#6B7280] mt-1">Provide the URL to your Azure Boards or Repository.</p>
                    </div>
                    <input
                      type="url"
                      placeholder="e.g. https://dev.azure.com/organization/project"
                      className="w-full max-w-md mx-auto block px-4 py-3 text-xs bg-white border border-[#E5E7EB] rounded-xl focus:outline-none focus:ring-2 focus:ring-[#FF602B]"
                    />
                  </div>
                )}

                {docSource === 'voice' && (
                  <div className="w-full max-w-lg text-center space-y-4">
                    <Mic className="w-8 h-8 mx-auto text-[#FF602B]" />
                    <div>
                      <p className="font-bold text-[#111827] block">Upload Voice Transcript</p>
                      <p className="text-xs text-[#6B7280] mt-1">Upload an audio recording or transcription file.</p>
                    </div>
                    <div className="w-full max-w-md mx-auto relative block">
                       <input
                         type="file"
                         accept="audio/*,.txt,.pdf"
                         className="w-full px-4 py-2.5 text-xs bg-white border border-[#E5E7EB] rounded-xl focus:outline-none focus:ring-2 focus:ring-[#FF602B] file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-xs file:font-semibold file:bg-[#FFF0EB] file:text-[#FF602B] hover:file:bg-[#FFE6DE] cursor-pointer"
                       />
                    </div>
                  </div>
                )}

              </div>
            </div>

            {/* Submit Action CTA */}
            <div className="flex items-center justify-end gap-3 pt-4 border-t border-[#E5E7EB]">
              <button
                type="button"
                onClick={() => setIsCreatingNewProject(false)}
                className="px-5 py-2.5 text-xs font-bold text-[#6B7280] bg-[#F3F4F6] rounded-xl hover:bg-[#E5E7EB]"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={isUploading}
                className="px-6 py-2.5 text-xs font-extrabold text-white bg-gradient-to-r from-[#FF602B] to-[#4318FF] rounded-xl shadow-md hover:opacity-95 flex items-center gap-2"
              >
                {isUploading ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Create Workspace & Inject Document →'}
              </button>
            </div>

          </form>
        )}

        {/* ======================================================================
            TAB 1: DASHBOARD VIEW
           ====================================================================== */}
        {!isCreatingNewProject && activeTab === 'Dashboard' && (
          <>
            {/* Stat Cards */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              <div className="p-5 rounded-2xl bg-[#E6F7F0] flex items-start justify-between border border-[#10B981]/20 shadow-sm">
                <div className="space-y-2">
                  <span className="text-xs font-semibold text-[#111827]">Documents Processed</span>
                  <div className="text-3xl font-extrabold text-[#111827]">47</div>
                  <div className="flex items-center gap-1 text-xs font-semibold text-[#10B981]">
                    <ArrowUpRight className="w-3.5 h-3.5" />
                    <span>+12.3% vs last week</span>
                  </div>
                </div>
                <div className="w-10 h-10 rounded-xl bg-[#D1FAE5] text-[#10B981] flex items-center justify-center shrink-0">
                  <FileCheck className="w-5 h-5" />
                </div>
              </div>

              <div className="p-5 rounded-2xl bg-[#EFEEFD] flex items-start justify-between border border-[#7551FF]/20 shadow-sm">
                <div className="space-y-2">
                  <span className="text-xs font-semibold text-[#111827]">Stories Generated</span>
                  <div className="text-3xl font-extrabold text-[#111827]">312</div>
                  <div className="flex items-center gap-1 text-xs font-semibold text-[#4318FF]">
                    <ArrowUpRight className="w-3.5 h-3.5" />
                    <span>+8.4% vs last week</span>
                  </div>
                </div>
                <div className="w-10 h-10 rounded-xl bg-[#D8E2FD] text-[#4318FF] flex items-center justify-center shrink-0">
                  <Layers className="w-5 h-5" />
                </div>
              </div>

              <div className="p-5 rounded-2xl bg-[#FFF0EB] flex items-start justify-between border border-[#FF602B]/20 shadow-sm">
                <div className="space-y-2">
                  <span className="text-xs font-semibold text-[#111827]">Avg Processing Time</span>
                  <div className="text-3xl font-extrabold text-[#111827]">2.3 min</div>
                  <div className="flex items-center gap-1 text-xs font-semibold text-[#FF602B]">
                    <ArrowUpRight className="w-3.5 h-3.5 rotate-90" />
                    <span>-15.1% vs last week</span>
                  </div>
                </div>
                <div className="w-10 h-10 rounded-xl bg-[#FFE0D6] text-[#FF602B] flex items-center justify-center shrink-0">
                  <Clock className="w-5 h-5" />
                </div>
              </div>

              <div className="p-5 rounded-2xl bg-[#EDF5FF] flex items-start justify-between border border-[#3B82F6]/20 shadow-sm">
                <div className="space-y-2">
                  <span className="text-xs font-semibold text-[#111827]">Active Projects</span>
                  <div className="text-3xl font-extrabold text-[#111827]">8</div>
                  <div className="flex items-center gap-1 text-xs font-semibold text-[#3B82F6]">
                    <ArrowUpRight className="w-3.5 h-3.5" />
                    <span>0% vs last week</span>
                  </div>
                </div>
                <div className="w-10 h-10 rounded-xl bg-[#D3E4FF] text-[#3B82F6] flex items-center justify-center shrink-0">
                  <Folder className="w-5 h-5" />
                </div>
              </div>
            </div>

            {/* Recent Projects Table Container */}
            <div className="bg-white rounded-3xl border border-[#E5E7EB] shadow-sm p-6 space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-base font-bold text-[#111827] tracking-tight">Recent Projects</h2>
                  <p className="text-xs text-[#6B7280] mt-0.5">Review status and live progress of active scopes</p>
                </div>
                <button
                  onClick={() => setActiveTab('Projects')}
                  className="px-4 py-2 text-xs font-bold text-[#111827] bg-white border border-[#E5E7EB] hover:bg-[#F9FAFB] rounded-full transition-colors flex items-center gap-2"
                >
                  View All Projects
                </button>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="border-b border-[#E5E7EB] text-[11px] font-bold text-[#A0AEC0] uppercase tracking-wider">
                      <th className="py-3 px-4">Name</th>
                      <th className="py-3 px-4">Client</th>
                      <th className="py-3 px-4">Status</th>
                      <th className="py-3 px-4">Stories</th>
                      <th className="py-3 px-4">Progress</th>
                      <th className="py-3 px-4 text-right">Updated</th>
                      <th className="py-3 px-4 text-right">Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#E5E7EB] text-xs">
                    {filteredProjects.map((proj, idx) => (
                      <tr 
                        key={`tbl-${proj.id}-${idx}`}
                        onClick={() => handleOpenProjectInPage(proj.id, proj.status === 'Completed' ? 'Document' : undefined)}
                        className="hover:bg-[#F7F9FC] transition-colors cursor-pointer group"
                      >
                        <td className="py-3.5 px-4 font-semibold text-[#111827] flex items-center gap-3">
                          <Folder className="w-4 h-4 text-[#FF602B] shrink-0" />
                          <span className="group-hover:text-[#7551FF] transition-colors">{proj.name}</span>
                        </td>
                        <td className="py-3.5 px-4 text-[#6B7280] font-medium">{proj.client}</td>
                        <td className="py-3.5 px-4">
                          <span className={`px-2.5 py-1 rounded-full text-[10px] font-bold ${proj.status === 'Completed' ? 'bg-[#E0E7FF] text-[#4318FF]' : 'bg-[#D1FAE5] text-[#10B981]'}`}>
                            {proj.status === 'Completed' ? 'Completed' : 'Active'}
                          </span>
                        </td>
                        <td className="py-3.5 px-4 text-[#6B7280] font-medium">
                          <span className="text-muted-foreground flex gap-1 items-center font-medium">
                            <Layers className="w-3.5 h-3.5 opacity-70" />
                            {projectStats[proj.id]?.stories || 0} stories
                          </span>
                        </td>
                        <td className="py-3.5 px-4">
                          <div className="flex items-center gap-3 max-w-[140px]">
                            <div className="flex-1 bg-[#F3F4F6] rounded-full h-1.5 overflow-hidden">
                              <div className="bg-gradient-to-r from-[#FF602B] to-[#4318FF] h-full rounded-full" style={{ width: `${proj.progress}%` }} />
                            </div>
                            <span className="text-[11px] font-bold text-[#111827]">{proj.progress}%</span>
                          </div>
                        </td>
                        <td className="py-3.5 px-4 text-right text-[#A0AEC0] font-medium">{proj.updated}</td>
                        <td className="py-3.5 px-4 text-right">
                          <button
                            type="button"
                            onClick={(e) => handleDeleteProject(proj.id, e)}
                            title="Delete project"
                            className="p-1.5 rounded-lg text-[#A0AEC0] hover:text-red-600 hover:bg-red-50 transition-colors"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </>
        )}

        {/* ======================================================================
            TAB 2: PROJECTS GRID VIEW
           ====================================================================== */}
        {!isCreatingNewProject && activeTab === 'Projects' && (
          <div className="space-y-6">
            <div>
              <h2 className="text-xl font-bold text-[#111827] tracking-tight">Projects</h2>
              <p className="text-xs text-[#6B7280] mt-0.5">Manage your requirement analysis workspaces and generated backlog boards.</p>
            </div>

            {/* Filter Bar */}
            <div className="flex flex-wrap items-center justify-between gap-3 bg-white p-3.5 rounded-2xl border border-[#E5E7EB] shadow-sm">
              <div className="flex-1 min-w-[240px] relative">
                <Search className="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-[#A0AEC0]" />
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Search projects..."
                  className="w-full pl-10 pr-4 py-2 text-xs bg-[#F7F9FC] border border-[#E5E7EB] rounded-xl focus:outline-none focus:ring-2 focus:ring-[#7551FF] text-[#111827]"
                />
              </div>

              <div className="flex items-center gap-2 flex-wrap">
                <select
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value)}
                  className="px-3 py-2 text-xs font-bold text-[#111827] bg-[#F7F9FC] border border-[#E5E7EB] rounded-xl cursor-pointer"
                >
                  <option value="All">Status: All</option>
                  <option value="Active">Status: Active</option>
                  <option value="Completed">Status: Completed</option>
                </select>

                <select
                  value={businessUnitFilter}
                  onChange={(e) => setBusinessUnitFilter(e.target.value)}
                  className="px-3 py-2 text-xs font-bold text-[#111827] bg-[#F7F9FC] border border-[#E5E7EB] rounded-xl cursor-pointer"
                >
                  <option value="All">Business Unit: All</option>
                  <option value="Product">Product</option>
                </select>

                <select
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value)}
                  className="px-3 py-2 text-xs font-bold text-[#111827] bg-[#F7F9FC] border border-[#E5E7EB] rounded-xl cursor-pointer"
                >
                  <option value="Recently Updated">Sort by: Recently Updated</option>
                  <option value="Name">Sort by: Name</option>
                </select>
              </div>
            </div>

            {/* Reference Project Cards Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
              {filteredProjects.map((proj, idx) => (
                <div
                  key={`crd-${proj.id}-${idx}`}
                  className="bg-white rounded-2xl border border-[#E5E7EB] shadow-sm overflow-hidden hover:border-[#7551FF] transition-all group flex flex-col justify-between"
                >
                  <div className="h-1.5 w-full bg-[#10B981]" />

                  <div className="p-5 space-y-4">
                    
                    {/* Title & Badge */}
                    <div className="flex items-start justify-between">
                      <div>
                        <h3 
                          onClick={() => handleOpenProjectInPage(proj.id, proj.status === 'Completed' ? 'Document' : undefined)}
                          className="font-bold text-base text-[#111827] group-hover:text-[#7551FF] transition-colors leading-tight cursor-pointer"
                        >
                          {proj.name}
                        </h3>
                        <p className="text-xs text-[#A0AEC0] font-medium mt-1">
                          Product • {proj.client}
                        </p>
                      </div>

                      <div className="flex items-center gap-2">
                        <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-extrabold ${proj.status === 'Completed' ? 'bg-[#E0E7FF] text-[#4318FF]' : 'bg-[#D1FAE5] text-[#10B981]'}`}>
                          {proj.status === 'Completed' ? 'Completed' : 'Active'}
                        </span>
                        <button
                          type="button"
                          onClick={(e) => handleDeleteProject(proj.id, e)}
                          title="Delete project"
                          className="p-1.5 rounded-xl text-[#A0AEC0] hover:text-red-600 hover:bg-red-50 transition-all"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </div>

                    {/* Counts Row */}
                    <div className="flex items-center text-xs py-2 border-t border-b border-[#E5E7EB]">
                      <div className="flex items-center gap-4 text-[#6B7280] font-semibold">
                        <span className="flex items-center gap-1.5">
                          <FileText className="w-3.5 h-3.5 text-[#A0AEC0]" /> {projectStats[proj.id]?.docs || 0} docs
                        </span>
                        <span className="flex items-center gap-1.5">
                          <Layers className="w-3.5 h-3.5 text-[#A0AEC0]" /> {projectStats[proj.id]?.stories || 0} stories
                        </span>
                      </div>
                    </div>

                    {/* DIRECT VERTICALS ACTION BUTTONS GRID */}
                    <div className="space-y-1.5 pt-1">
                      <span className="text-[10px] font-bold text-[#A0AEC0] uppercase tracking-wider block">DIRECT VERTICALS</span>
                      {proj.status === 'Completed' ? (
                        <div className="grid grid-cols-2 gap-2 mt-2">
                          <button
                            onClick={(e) => { e.stopPropagation(); handleOpenProjectInPage(proj.id, 'Document'); }}
                            className="w-full py-2 px-2 bg-gradient-to-r from-[#FF602B] to-[#ff6b4a] shadow-[0_4px_12px_rgba(255,87,51,0.25)] rounded-xl text-[11px] font-extrabold text-white hover:scale-[1.02] transition-all flex items-center justify-center gap-1.5"
                          >
                            <FileText className="w-3.5 h-3.5" /> Final Document
                          </button>
                          <button
                            onClick={(e) => { e.stopPropagation(); handleOpenProjectInPage(proj.id, 'Version Control'); }}
                            className="w-full py-2 px-2 bg-[#F7F9FC] border border-[#E5E7EB] rounded-xl text-[11px] font-bold text-[#111827] hover:bg-[#7551FF] hover:text-white hover:border-[#7551FF] transition-all flex items-center justify-center gap-1.5"
                          >
                            <History className="w-3.5 h-3.5" /> History
                          </button>
                        </div>
                      ) : (
                        <div className="grid grid-cols-3 gap-2 mt-1">
                          <button
                            onClick={(e) => { e.stopPropagation(); handleOpenProjectInPage(proj.id, 'Requirement Analysis'); }}
                            className="w-full py-1.5 px-2 bg-[#F7F9FC] border border-[#E5E7EB] rounded-xl text-[11px] font-bold text-[#111827] hover:bg-[#7551FF] hover:text-white hover:border-[#7551FF] transition-all flex items-center justify-center gap-1"
                          >
                            <BookOpen className="w-3 h-3" /> Req
                          </button>
                          <button
                            onClick={(e) => { e.stopPropagation(); handleOpenProjectInPage(proj.id, 'Outline / Epics'); }}
                            className="w-full py-1.5 px-2 bg-[#F7F9FC] border border-[#E5E7EB] rounded-xl text-[11px] font-bold text-[#111827] hover:bg-[#7551FF] hover:text-white hover:border-[#7551FF] transition-all flex items-center justify-center gap-1"
                          >
                            <GitBranch className="w-3 h-3" /> Epics
                          </button>
                          <button
                            onClick={(e) => { e.stopPropagation(); handleOpenProjectInPage(proj.id, 'Story Board'); }}
                            className="w-full py-1.5 px-2 bg-[#F7F9FC] border border-[#E5E7EB] rounded-xl text-[11px] font-bold text-[#111827] hover:bg-[#7551FF] hover:text-white hover:border-[#7551FF] transition-all flex items-center justify-center gap-1"
                          >
                            <ListChecks className="w-3 h-3" /> Stories
                          </button>
                          <button
                            onClick={(e) => { e.stopPropagation(); handleOpenProjectInPage(proj.id, 'Validation Gate'); }}
                            className="w-full py-1.5 px-2 bg-[#F7F9FC] border border-[#E5E7EB] rounded-xl text-[11px] font-bold text-[#111827] hover:bg-[#7551FF] hover:text-white hover:border-[#7551FF] transition-all flex items-center justify-center gap-1"
                          >
                            <ShieldCheck className="w-3 h-3" /> Valid
                          </button>
                          <button
                            onClick={(e) => { e.stopPropagation(); handleOpenProjectInPage(proj.id, 'Version Control'); }}
                            className="w-full py-1.5 px-2 bg-[#F7F9FC] border border-[#E5E7EB] rounded-xl text-[11px] font-bold text-[#111827] hover:bg-[#7551FF] hover:text-white hover:border-[#7551FF] transition-all flex items-center justify-center gap-1"
                          >
                            <History className="w-3 h-3" /> Versions
                          </button>
                          <button
                            onClick={(e) => { e.stopPropagation(); handleOpenProjectInPage(proj.id, 'Document'); }}
                            className="w-full py-1.5 px-2 bg-[#F7F9FC] border border-[#E5E7EB] rounded-xl text-[11px] font-bold text-[#111827] hover:bg-[#7551FF] hover:text-white hover:border-[#7551FF] transition-all flex items-center justify-center gap-1"
                          >
                            <FileText className="w-3 h-3" /> Document
                          </button>
                        </div>
                      )}
                    </div>

                  </div>

                  {/* Footer Row */}
                  <div className="px-5 py-3.5 bg-[#F7F9FC] border-t border-[#E5E7EB] flex items-center justify-between text-xs">
                    <div className="flex items-center gap-2">
                      <img
                        src="https://images.unsplash.com/photo-1494790108377-be9c29b29330?auto=format&fit=crop&q=80&w=120"
                        alt="Sarah M."
                        className="w-5 h-5 rounded-full object-cover border border-[#E5E7EB]"
                      />
                      <span className="font-semibold text-[#111827]">{proj.owner}</span>
                    </div>

                    <div className="flex items-center gap-2 text-[#A0AEC0] text-[11px]">
                      <span>{proj.updated}</span>
                      <button
                        type="button"
                        onClick={(e) => handleDeleteProject(proj.id, e)}
                        title="Delete project"
                        className="p-1 rounded-lg text-[#A0AEC0] hover:text-red-600 hover:bg-red-50 transition-colors flex items-center gap-1 font-semibold text-[10px]"
                      >
                        <Trash2 className="w-3.5 h-3.5" /> Delete
                      </button>
                    </div>
                  </div>

                </div>
              ))}
            </div>
          </div>
        )}



        {/* ======================================================================
            PIPELINE VIEW
           ====================================================================== */}
        {!isCreatingNewProject && (activeTab === 'Pipeline' || activeTab === 'processing') && (
          <ProcessingPage projectId={selectedProjectId} onNavigate={(targetTab) => { setActiveTab(targetTab); updateWorkspaceTab(selectedProjectId, targetTab); }} />
        )}

        {/* ======================================================================
            TAB 4: REQUIREMENT ANALYSIS IN-PAGE VIEW
           ====================================================================== */}
        {!isCreatingNewProject && (activeTab === 'Requirement Analysis' || activeTab === 'requirements') && (
          <RequirementsPage projectId={selectedProjectId} onNavigate={(targetTab) => { setActiveTab(targetTab); updateWorkspaceTab(selectedProjectId, targetTab); }} />
        )}

        {/* ======================================================================
            TAB 5: OUTLINE / EPICS IN-PAGE VIEW
           ====================================================================== */}
        {!isCreatingNewProject && (activeTab === 'Outline / Epics' || activeTab === 'Epics' || activeTab === 'epics' || activeTab === 'Outline Review') && (
          <EpicReviewPage projectId={selectedProjectId} onNavigate={(targetTab) => handleOpenProjectInPage(selectedProjectId, targetTab)} />
        )}

        {/* ======================================================================
            TAB 6: STORY BOARD IN-PAGE VIEW
           ====================================================================== */}
        {!isCreatingNewProject && (activeTab === 'Story Board' || activeTab === 'Stories' || activeTab === 'stories') && (
          <StoryBoardPage projectId={selectedProjectId} onNavigate={(targetTab) => handleOpenProjectInPage(selectedProjectId, targetTab)} />
        )}

        {/* ======================================================================
            VALIDATION GATE IN-PAGE VIEW
           ====================================================================== */}
        {!isCreatingNewProject && (activeTab === 'Validation Gate' || activeTab === 'validation') && (
          <FinalValidationPage projectId={selectedProjectId} onNavigate={(targetTab) => handleOpenProjectInPage(selectedProjectId, targetTab)} />
        )}

        {/* ======================================================================
            VERSION CONTROL IN-PAGE VIEW
           ====================================================================== */}
        {!isCreatingNewProject && (activeTab === 'Version Control' || activeTab === 'versioning') && (
          <VersioningPage projectId={selectedProjectId} />
        )}

        {/* ======================================================================
            DOCUMENT VIEW (Final Preview / Export)
           ====================================================================== */}
        {!isCreatingNewProject && activeTab === 'Document' && (
          <ExportPage 
            projectId={selectedProjectId} 
            onNavigate={(targetTab) => {
              if (targetTab === 'Dashboard') {
                setActiveTab('Dashboard');
                setSelectedProjectId('');
                setIsCreatingNewProject(false);
              } else {
                handleOpenProjectInPage(selectedProjectId, targetTab);
              }
            }} 
          />
        )}



      </main>
    </div>
  );
}

export default function DashboardPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen flex items-center justify-center bg-[#1B1B3A]">
        <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-[#FF602B]"></div>
      </div>
    }>
      <DashboardContent />
    </Suspense>
  );
}
