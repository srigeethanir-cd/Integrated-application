'use client';

import React, { useState, useRef, useEffect } from 'react';
import { 
  ArrowLeft, 
  UploadCloud, 
  Sparkles, 
  Image as ImageIcon, 
  Palette, 
  AlertCircle,
  CheckCircle2,
  RefreshCw,
  Trash2,
  Check,
  Save,
  RotateCcw,
  X,
  LayoutGrid,
  Folder,
  FileText,
  BookOpen,
  Layers,
  Settings as SettingsIcon,
  Lightbulb
} from 'lucide-react';
import Link from 'next/link';
import { usePersonalization } from '@/context/PersonalizationContext';

/* ─────────────────────────── SIDEBAR BACKGROUND PRESETS ─────────────────────── */
const SIDEBAR_BG_PRESETS = [
  { hex: '#1B1B3A', name: 'Deep Navy' },
  { hex: '#0F172A', name: 'Midnight Slate' },
  { hex: '#111827', name: 'Charcoal' },
  { hex: '#18181B', name: 'Zinc Dark' },
  { hex: '#1E1B4B', name: 'Indigo Night' },
  { hex: '#1C1917', name: 'Stone Black' },
  { hex: '#064E3B', name: 'Emerald Deep' },
  { hex: '#1E3A5F', name: 'Ocean Blue' },
  { hex: '#2D1B69', name: 'Royal Purple' },
  { hex: '#3B0A0A', name: 'Dark Crimson' },
  { hex: '#292524', name: 'Warm Dark' },
  { hex: '#0C4A6E', name: 'Teal Deep' },
];

/* ──────────────────────── HIGHLIGHT GRADIENT PALETTE PRESETS ─────────────────── */
interface HighlightPalette {
  id: string;
  name: string;
  from: string;
  via: string;
}

const HIGHLIGHT_PALETTES: HighlightPalette[] = [
  { id: 'aurora-blaze',      name: 'Aurora Blaze',      from: '#FF6A00', via: '#8A2BE2' },
  { id: 'deep-sea-current',  name: 'Deep Sea Current',  from: '#003366', via: '#00D4FF' },
  { id: 'peacock-feather',   name: 'Peacock Feather',   from: '#006D77', via: '#83F2C1' },
  { id: 'sunset-horizon',    name: 'Sunset Horizon',    from: '#D4145A', via: '#FBB03B' },
  { id: 'cosmic-dust',       name: 'Cosmic Dust',       from: '#4A00E0', via: '#8E2DE2' },
  { id: 'arctic-lights',     name: 'Arctic Lights',     from: '#141E30', via: '#243B55' },
  { id: 'forest-whisper',    name: 'Forest Whisper',    from: '#134E5E', via: '#71B280' },
  { id: 'citrus-zest',       name: 'Citrus Zest',       from: '#E52D27', via: '#FF8A00' },
  { id: 'golden-dusk',       name: 'Golden Dusk',       from: '#F4C430', via: '#F15F79' },
  { id: 'orchid-mist',       name: 'Orchid Mist',       from: '#8360C3', via: '#F9A8D4' },
  { id: 'midnight-slate',    name: 'Midnight Slate',    from: '#232526', via: '#414345' },
  { id: 'tropical-lagoon',   name: 'Tropical Lagoon',   from: '#11998E', via: '#38EF7D' },
];

/* ──────────────────────────── PREVIEW MENU ITEMS ─────────────────────────────── */
const PREVIEW_ITEMS = [
  { label: 'User Story',      icon: LayoutGrid },
  { label: 'UI Code',         icon: Folder },
  { label: 'API Code',        icon: FileText },
  { label: 'Unit Test Cases', icon: BookOpen },
  { label: 'App Testing',     icon: Layers },
];

/* ═══════════════════════════════════════════════════════════════════════════════ */

export default function SettingsPage() {
  const { 
    logoUrl, 
    sidebarBg,
    highlightFrom,
    highlightVia,
    savePersonalization,
    resetPersonalization,
    uploadLogo, 
    removeLogo, 
    isAdmin, 
    userRole
  } = usePersonalization();

  // Logo Upload State
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [isRemoving, setIsRemoving] = useState(false);

  // Draft/Temporary State for Live Preview before Saving
  const [draftBg, setDraftBg] = useState<string>(sidebarBg);
  const [draftFrom, setDraftFrom] = useState<string>(highlightFrom);
  const [draftVia, setDraftVia] = useState<string>(highlightVia);

  // Action status and loading states
  const [isSaving, setIsSaving] = useState(false);
  const [isResetting, setIsResetting] = useState(false);
  const [showResetConfirm, setShowResetConfirm] = useState(false);
  const [feedback, setFeedback] = useState<{ type: 'success' | 'error'; message: string } | null>(null);

  // Keep draft in sync when saved state changes externally (e.g. initial fetch or WebSocket)
  useEffect(() => { setDraftBg(sidebarBg); }, [sidebarBg]);
  useEffect(() => { setDraftFrom(highlightFrom); }, [highlightFrom]);
  useEffect(() => { setDraftVia(highlightVia); }, [highlightVia]);

  const isDirty = (
    draftBg !== sidebarBg ||
    draftFrom !== highlightFrom ||
    draftVia !== highlightVia ||
    previewUrl !== null
  );

  // Active preview item index
  const [previewActiveIdx, setPreviewActiveIdx] = useState(0);

  /* ────── Logo Upload Handlers ────── */
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    if (!file.type.startsWith('image/')) {
      setFeedback({ type: 'error', message: 'Please select a valid image file (PNG, JPG, SVG, WebP).' });
      return;
    }
    if (file.size > 10 * 1024 * 1024) {
      setFeedback({ type: 'error', message: 'Image size exceeds 10MB limit.' });
      return;
    }
    setSelectedFile(file);
    setPreviewUrl(URL.createObjectURL(file));
    setFeedback(null);
  };

  const handleUploadLogo = async () => {
    if (!selectedFile || !isAdmin) return;
    setIsUploading(true);
    setFeedback(null);
    try {
      await uploadLogo(selectedFile);
      setSelectedFile(null);
      setPreviewUrl(null);
      setFeedback({ type: 'success', message: 'Logo uploaded and applied successfully.' });
    } catch (err: any) {
      setFeedback({ type: 'error', message: err.message || 'Upload failed.' });
    } finally {
      setIsUploading(false);
    }
  };

  const handleRemoveLogo = async () => {
    if (!isAdmin) return;
    setIsRemoving(true);
    setFeedback(null);
    try {
      await removeLogo();
      setSelectedFile(null);
      setPreviewUrl(null);
      setFeedback({ type: 'success', message: 'Custom logo removed. Default branding restored.' });
    } catch (err: any) {
      setFeedback({ type: 'error', message: err.message || 'Failed to remove logo.' });
    } finally {
      setIsRemoving(false);
    }
  };

  /* ────── Save All Changes ────── */
  const handleSaveChanges = async () => {
    if (!isAdmin) {
      setFeedback({ type: 'error', message: 'Administrator permissions required.' });
      return;
    }
    setIsSaving(true);
    setFeedback(null);
    try {
      let uploadedLogoUrl = logoUrl;
      if (selectedFile) {
        uploadedLogoUrl = await uploadLogo(selectedFile);
        setSelectedFile(null);
        setPreviewUrl(null);
      }

      await savePersonalization({
        logoUrl: uploadedLogoUrl,
        sidebarBg: draftBg,
        highlightFrom: draftFrom,
        highlightVia: draftVia,
      });

      setFeedback({ type: 'success', message: 'Personalization settings saved and synced across all pages.' });
    } catch (err: any) {
      setFeedback({ type: 'error', message: err.message || 'Failed to save settings.' });
    } finally {
      setIsSaving(false);
    }
  };

  /* ────── Cancel Draft Changes ────── */
  const handleCancel = () => {
    setDraftBg(sidebarBg);
    setDraftFrom(highlightFrom);
    setDraftVia(highlightVia);
    setSelectedFile(null);
    setPreviewUrl(null);
    setFeedback(null);
  };

  /* ────── Reset to Defaults ────── */
  const handleConfirmReset = async () => {
    if (!isAdmin) return;
    setIsResetting(true);
    setFeedback(null);
    setShowResetConfirm(false);
    try {
      await resetPersonalization();
      setSelectedFile(null);
      setPreviewUrl(null);
      setFeedback({ type: 'success', message: 'All personalization settings reset to application defaults.' });
    } catch (err: any) {
      setFeedback({ type: 'error', message: err.message || 'Failed to reset settings.' });
    } finally {
      setIsResetting(false);
    }
  };

  /* ────── Computed Values ────── */
  const activeLogo = previewUrl || logoUrl;
  const draftGradient = `linear-gradient(to right, ${draftFrom}, ${draftVia})`;

  return (
    <div className="flex-1 flex flex-col min-h-screen bg-[var(--background,#F7F9FC)] font-sans p-6 md:p-8 space-y-6">
      {/* Top Header */}
      <header className="flex items-center justify-between pb-4 border-b border-border">
        <Link href="/dashboard" className="text-xs font-semibold text-muted-foreground hover:text-[var(--primary,#7551FF)] flex items-center gap-1.5 transition-colors">
          <ArrowLeft className="w-3.5 h-3.5" /> Return to Workspace
        </Link>
      </header>

      <div className="max-w-6xl mx-auto w-full space-y-6">
        {/* Page Title */}
        <div>
          <h1 className="text-2xl font-extrabold text-foreground tracking-tight flex items-center gap-2.5">
            <Palette className="w-6 h-6 text-primary" /> Settings &amp; Personalization
          </h1>
          <p className="text-sm text-muted-foreground mt-0.5">
            Customize your application logo and sidebar appearance.
          </p>
        </div>

        {/* Read-Only Notice */}
        {!isAdmin && (
          <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-800 dark:text-amber-300 text-xs flex items-center gap-3">
            <AlertCircle className="w-4 h-4 shrink-0 text-amber-500" />
            <span>
              You are signed in as <strong>{userRole}</strong> with read-only access. Administrator privileges are required to modify settings.
            </span>
          </div>
        )}

        {/* Feedback Alert */}
        {feedback && (
          <div className={`p-4 rounded-xl text-xs flex items-center gap-3 animate-in fade-in duration-150 ${feedback.type === 'success' ? 'bg-green-500/10 border border-green-500/20 text-green-700 dark:text-green-300' : 'bg-red-500/10 border border-red-500/20 text-red-700 dark:text-red-300'}`}>
            {feedback.type === 'success' ? <CheckCircle2 className="w-4 h-4 text-green-500 shrink-0" /> : <AlertCircle className="w-4 h-4 text-red-500 shrink-0" />}
            <span className="font-medium">{feedback.message}</span>
            <button onClick={() => setFeedback(null)} className="ml-auto text-muted-foreground hover:text-foreground cursor-pointer">
              <X className="w-3.5 h-3.5" />
            </button>
          </div>
        )}

        <div className="space-y-8">
          {/* ================================================================= */}
          {/* 1. CHANGE LOGO SECTION */}
          {/* ================================================================= */}
          <section className="bg-card border border-border rounded-2xl p-6 md:p-8 shadow-xs space-y-6">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-4 border-b border-border/60">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-orange-500/20 to-purple-500/20 flex items-center justify-center text-primary border border-primary/20">
                  <ImageIcon className="w-5 h-5" />
                </div>
                <div>
                  <h2 className="text-lg font-bold text-foreground">Change Logo</h2>
                  <p className="text-xs text-muted-foreground">Upload a custom application logo or reset to default branding.</p>
                </div>
              </div>
              <span className="text-[11px] font-semibold px-2.5 py-1 rounded-full bg-muted text-muted-foreground">Cloudinary Upload</span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 items-stretch">
              {/* Current Logo Display */}
              <div className="flex flex-col justify-between p-5 rounded-xl border border-border bg-muted/20 space-y-4">
                <div>
                  <span className="text-xs font-bold text-muted-foreground uppercase tracking-wider">Current Logo &amp; Preview</span>
                  <div className="mt-3 p-6 rounded-xl bg-muted/40 border border-border/80 flex items-center justify-center min-h-[110px]">
                    {activeLogo ? (
                      <div className="w-16 h-16 rounded-xl bg-white/10 p-2 flex items-center justify-center overflow-hidden shadow-md">
                        <img src={activeLogo} alt="Logo Preview" className="w-full h-full object-contain drop-shadow-sm" />
                      </div>
                    ) : (
                      <div className="flex items-center gap-3">
                        <div 
                          className="w-10 h-10 rounded-xl flex items-center justify-center text-white shadow-md transition-all"
                          style={{ background: draftGradient }}
                        >
                          <Sparkles className="w-5 h-5 fill-white" />
                        </div>
                        <div className="text-left">
                          <p className="font-extrabold text-foreground text-sm leading-tight">StoryForge AI</p>
                          <span className="text-[10px] text-muted-foreground">Default Branding</span>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
                <div className="flex items-center justify-between text-xs pt-2">
                  <span className="text-muted-foreground">Status: <strong className="text-foreground">{activeLogo ? (previewUrl ? 'Previewing New File' : 'Custom Logo') : 'Default Logo'}</strong></span>
                  {logoUrl && (
                    <button onClick={handleRemoveLogo} disabled={!isAdmin || isRemoving} className="text-red-500 hover:text-red-600 font-semibold flex items-center gap-1.5 hover:underline disabled:opacity-50 cursor-pointer text-xs">
                      {isRemoving ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Trash2 className="w-3.5 h-3.5" />} Remove
                    </button>
                  )}
                </div>
              </div>

              {/* Upload Input */}
              <div className="flex flex-col justify-between p-5 rounded-xl border border-border bg-card space-y-4">
                <div>
                  <span className="text-xs font-bold text-muted-foreground uppercase tracking-wider">Upload New Logo</span>
                  <input type="file" ref={fileInputRef} onChange={handleFileChange} accept="image/png,image/jpeg,image/svg+xml,image/webp" className="hidden" />
                  {previewUrl ? (
                    <div className="mt-3 p-4 rounded-xl border-2 border-dashed border-primary/50 bg-primary/5 flex flex-col items-center justify-center space-y-2 min-h-[110px]">
                      <div className="w-12 h-12 rounded-xl bg-white/20 p-1 overflow-hidden shadow-xs">
                        <img src={previewUrl} alt="Preview" className="w-full h-full object-contain" />
                      </div>
                      <span className="text-[11px] font-medium text-muted-foreground">{selectedFile?.name} ({(selectedFile ? selectedFile.size / 1024 : 0).toFixed(1)} KB)</span>
                    </div>
                  ) : (
                    <div onClick={() => isAdmin && fileInputRef.current?.click()} className={`mt-3 p-6 rounded-xl border-2 border-dashed border-border flex flex-col items-center justify-center space-y-2 text-center transition-colors min-h-[110px] ${isAdmin ? 'hover:border-primary/60 hover:bg-muted/30 cursor-pointer' : 'opacity-60 cursor-not-allowed'}`}>
                      <UploadCloud className="w-6 h-6 text-muted-foreground" />
                      <p className="text-xs font-semibold text-foreground">Click to browse or drag and drop</p>
                      <p className="text-[10px] text-muted-foreground">PNG, SVG, JPG, or WebP up to 10MB</p>
                    </div>
                  )}
                </div>
                <div className="flex items-center justify-end gap-3 pt-2">
                  {previewUrl && (
                    <button onClick={() => { setSelectedFile(null); setPreviewUrl(null); }} className="px-3 py-1.5 text-xs font-semibold text-muted-foreground hover:text-foreground rounded-lg border border-border bg-card cursor-pointer">
                      Discard
                    </button>
                  )}
                  <button 
                    onClick={previewUrl ? handleUploadLogo : () => fileInputRef.current?.click()} 
                    disabled={!isAdmin || isUploading} 
                    className={`px-4 py-2 text-xs font-bold text-white rounded-xl shadow-sm flex items-center gap-2 transition-transform cursor-pointer ${previewUrl ? 'bg-gradient-to-r from-orange-500 to-purple-600 hover:scale-[1.02]' : 'bg-[var(--primary,#7551FF)] hover:opacity-90'} disabled:opacity-50`}
                  >
                    {isUploading ? <><RefreshCw className="w-3.5 h-3.5 animate-spin" /> Uploading...</> : previewUrl ? <><UploadCloud className="w-3.5 h-3.5" /> Apply Logo</> : <><ImageIcon className="w-3.5 h-3.5" /> Select File</>}
                  </button>
                </div>
              </div>
            </div>
          </section>

          {/* ================================================================= */}
          {/* 2. SIDEBAR APPEARANCE SECTION */}
          {/* ================================================================= */}
          <section className="bg-card border border-border rounded-2xl p-6 md:p-8 shadow-xs space-y-6">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-4 border-b border-border/60">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500/20 to-purple-500/20 flex items-center justify-center text-primary border border-primary/20">
                  <Palette className="w-5 h-5" />
                </div>
                <div>
                  <h2 className="text-lg font-bold text-foreground">Sidebar Appearance</h2>
                  <p className="text-xs text-muted-foreground">Customize sidebar background color and highlight gradient palette.</p>
                </div>
              </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* ── LEFT COLUMN: Background + Highlight Palette + Custom Colors ── */}
              <div className="lg:col-span-2 space-y-6">

                {/* Sidebar Background Color */}
                <div className="space-y-3">
                  <h3 className="text-sm font-bold text-foreground">Sidebar Background</h3>
                  <div className="grid grid-cols-6 sm:grid-cols-12 gap-2">
                    {SIDEBAR_BG_PRESETS.map((p) => (
                      <button
                        key={p.hex}
                        onClick={() => isAdmin && setDraftBg(p.hex)}
                        title={`${p.name} (${p.hex})`}
                        disabled={!isAdmin}
                        className={`w-full aspect-square rounded-lg border-2 transition-all cursor-pointer disabled:cursor-not-allowed relative ${
                          draftBg === p.hex ? 'border-white ring-2 ring-primary scale-110 z-10 shadow-md' : 'border-transparent hover:border-white/40 hover:scale-105'
                        }`}
                        style={{ backgroundColor: p.hex }}
                      >
                        {draftBg === p.hex && (
                          <div className="absolute inset-0 flex items-center justify-center">
                            <Check className="w-3.5 h-3.5 text-white drop-shadow-md stroke-[3]" />
                          </div>
                        )}
                      </button>
                    ))}
                  </div>
                  <p className="text-[11px] text-muted-foreground">Selected: <code className="bg-muted px-1.5 py-0.5 rounded font-mono text-[10px]">{draftBg}</code></p>
                </div>

                {/* Highlight Color Palette */}
                <div className="space-y-4">
                  <div>
                    <h3 className="text-sm font-bold text-foreground">Highlight Color Palette</h3>
                    <p className="text-xs text-muted-foreground mt-0.5">Select a unique 2-color gradient combination for active/hover states and accent elements.</p>
                  </div>
                  
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3.5">
                    {HIGHLIGHT_PALETTES.map((p) => {
                      const isSelected = draftFrom === p.from && draftVia === p.via;
                      return (
                        <button
                          key={p.id}
                          onClick={() => { if (isAdmin) { setDraftFrom(p.from); setDraftVia(p.via); } }}
                          disabled={!isAdmin}
                          className={`relative p-3.5 rounded-2xl border-2 transition-all cursor-pointer disabled:cursor-not-allowed text-left ${
                            isSelected
                              ? 'border-[#7551FF] bg-card shadow-md ring-2 ring-[#7551FF]/20'
                              : 'border-border/80 bg-card hover:border-border hover:shadow-xs'
                          }`}
                        >
                          {isSelected && (
                            <div className="absolute -top-2 -right-2 w-5 h-5 rounded-full bg-[#7551FF] text-white flex items-center justify-center shadow-md">
                              <Check className="w-3 h-3 stroke-[3]" />
                            </div>
                          )}
                          {/* Gradient Swatch */}
                          <div 
                            className="w-full h-11 rounded-xl mb-2.5 shadow-xs" 
                            style={{ background: `linear-gradient(to right, ${p.from}, ${p.via})` }} 
                          />
                          <p className="text-xs font-bold text-foreground leading-tight">{p.name}</p>
                          <div className="flex items-center justify-between gap-1 mt-2 text-[11px] text-muted-foreground font-medium">
                            <div className="flex items-center gap-1.5">
                              <span className="w-2.5 h-2.5 rounded-full shrink-0" style={{ backgroundColor: p.from }} />
                              <span>from {p.from}</span>
                            </div>
                            <div className="flex items-center gap-1.5">
                              <span className="w-2.5 h-2.5 rounded-full shrink-0" style={{ backgroundColor: p.via }} />
                              <span>to {p.via}</span>
                            </div>
                          </div>
                        </button>
                      );
                    })}
                  </div>

                  <div className="flex items-center gap-2 pt-1 text-xs text-muted-foreground">
                    <Lightbulb className="w-4 h-4 text-muted-foreground shrink-0" />
                    <span>These unique combinations provide better contrast and a premium look for your application.</span>
                  </div>
                </div>

                {/* Custom Colors */}
                <div className="space-y-3">
                  <h3 className="text-sm font-bold text-foreground">Custom Colors</h3>
                  <p className="text-xs text-muted-foreground">Pick your own From / Via colors for a custom highlight gradient.</p>
                  <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-end">
                    <div className="flex items-center gap-3">
                      <label className="text-xs font-semibold text-muted-foreground w-12">From</label>
                      <div className="flex items-center gap-2 bg-muted/30 border border-border rounded-lg px-2 py-1">
                        <input type="color" value={draftFrom} onChange={(e) => isAdmin && setDraftFrom(e.target.value)} disabled={!isAdmin} className="w-7 h-7 rounded border-0 cursor-pointer disabled:cursor-not-allowed bg-transparent" />
                        <input type="text" value={draftFrom} onChange={(e) => isAdmin && /^#[0-9a-fA-F]{0,6}$/.test(e.target.value) && setDraftFrom(e.target.value)} disabled={!isAdmin} className="w-20 bg-transparent text-xs font-mono text-foreground focus:outline-none disabled:opacity-60" />
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      <label className="text-xs font-semibold text-muted-foreground w-12">Via</label>
                      <div className="flex items-center gap-2 bg-muted/30 border border-border rounded-lg px-2 py-1">
                        <input type="color" value={draftVia} onChange={(e) => isAdmin && setDraftVia(e.target.value)} disabled={!isAdmin} className="w-7 h-7 rounded border-0 cursor-pointer disabled:cursor-not-allowed bg-transparent" />
                        <input type="text" value={draftVia} onChange={(e) => isAdmin && /^#[0-9a-fA-F]{0,6}$/.test(e.target.value) && setDraftVia(e.target.value)} disabled={!isAdmin} className="w-20 bg-transparent text-xs font-mono text-foreground focus:outline-none disabled:opacity-60" />
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-[10px] text-muted-foreground">Preview:</span>
                      <div className="w-24 h-7 rounded-lg border border-border shadow-xs" style={{ background: draftGradient }} />
                    </div>
                  </div>
                </div>
              </div>

              {/* ── RIGHT COLUMN: Live Sidebar Preview ── */}
              <div className="space-y-3">
                <h3 className="text-sm font-bold text-foreground">Live Sidebar Preview</h3>
                <div
                  className="rounded-2xl border border-border/60 overflow-hidden shadow-lg transition-all"
                  style={{ backgroundColor: draftBg, minHeight: 420 }}
                >
                  {/* Preview Header */}
                  <div className="p-4 flex items-center gap-3">
                    {activeLogo ? (
                      <div className="w-8 h-8 rounded-xl bg-white/10 p-1 flex items-center justify-center overflow-hidden transition-all shadow-xs">
                        <img src={activeLogo} alt="Logo" className="w-full h-full object-contain" />
                      </div>
                    ) : (
                      <div 
                        className="w-8 h-8 rounded-2xl flex items-center justify-center transition-all shadow-xs" 
                        style={{ background: draftGradient }}
                      >
                        <Sparkles className="w-4 h-4 text-white fill-white" />
                      </div>
                    )}
                    <span className="text-sm font-extrabold text-white tracking-tight">StoryForge AI</span>
                  </div>

                  {/* Preview Menu Items */}
                  <div className="px-3 space-y-1.5">
                    {PREVIEW_ITEMS.map((item, idx) => {
                      const isActive = idx === previewActiveIdx;
                      return (
                        <button
                          key={item.label}
                          onClick={() => setPreviewActiveIdx(idx)}
                          className={`w-full flex items-center justify-between px-3 py-2.5 rounded-xl text-[11px] transition-all cursor-pointer ${
                            isActive ? 'text-white shadow-md' : 'text-[#8F9BBA] hover:text-white hover:bg-white/10'
                          }`}
                          style={isActive ? { background: draftGradient } : undefined}
                        >
                          <div className="flex items-center gap-2.5">
                            <item.icon className={`w-4 h-4 ${isActive ? 'text-white' : 'text-[#8F9BBA]'}`} />
                            <span className="font-semibold">{item.label}</span>
                          </div>
                          {isActive && <span className="w-1 h-3.5 bg-white rounded-full" />}
                        </button>
                      );
                    })}
                  </div>

                  {/* Preview Bottom */}
                  <div className="mt-4 mx-3 p-3 rounded-xl bg-white/5 border border-white/10">
                    <p className="text-[10px] font-bold text-white">Forge Stories</p>
                    <p className="text-[9px] text-[#A0AEC0]">Generate AI-powered stories</p>
                  </div>

                  <div className="px-3 py-3 mt-2">
                    <div className="flex items-center gap-2.5 px-3 py-2 rounded-xl text-[#8F9BBA] text-[11px] font-semibold">
                      <SettingsIcon className="w-4 h-4" />
                      <span>Settings</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* =============================================================== */}
            {/* 3. SAVE / CANCEL / RESET CONTROLS BAR */}
            {/* =============================================================== */}
            <div className="p-4 rounded-xl bg-muted/40 border border-border flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setShowResetConfirm(true)}
                  disabled={!isAdmin || isResetting}
                  className="px-4 py-2 text-xs font-semibold text-red-600 hover:text-red-700 hover:bg-red-500/10 border border-red-500/20 rounded-xl transition-colors flex items-center gap-1.5 cursor-pointer disabled:opacity-50"
                  title="Reset all branding and sidebar settings to default"
                >
                  <RotateCcw className="w-3.5 h-3.5" /> Reset Defaults
                </button>

                {isDirty && (
                  <span className="text-[11px] text-amber-600 dark:text-amber-400 font-medium px-2.5 py-1 rounded-md bg-amber-500/10 border border-amber-500/20">
                    Unsaved changes pending
                  </span>
                )}
              </div>

              <div className="flex items-center gap-3 self-end sm:self-auto">
                <button
                  onClick={handleCancel}
                  disabled={!isDirty || isSaving}
                  className="px-4 py-2 text-xs font-semibold text-muted-foreground hover:text-foreground rounded-xl border border-border bg-card hover:bg-muted/40 transition-colors cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed"
                >
                  Cancel
                </button>

                <button
                  onClick={handleSaveChanges}
                  disabled={!isAdmin || isSaving || !isDirty}
                  className="px-5 py-2 text-xs font-bold text-white rounded-xl shadow-sm flex items-center gap-2 bg-gradient-to-r from-orange-500 to-purple-600 hover:scale-[1.02] transition-all cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed disabled:hover:scale-100"
                >
                  {isSaving ? <><RefreshCw className="w-3.5 h-3.5 animate-spin" /> Saving...</> : <><Save className="w-3.5 h-3.5" /> Save Changes</>}
                </button>
              </div>
            </div>
          </section>
        </div>
      </div>

      {/* Confirmation Modal for Reset Defaults */}
      {showResetConfirm && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-xs flex items-center justify-center p-4 z-50 animate-in fade-in duration-100">
          <div className="bg-card border border-border rounded-2xl p-6 max-w-md w-full shadow-2xl space-y-4">
            <div className="flex items-center gap-3 text-red-600">
              <div className="w-10 h-10 rounded-xl bg-red-500/10 flex items-center justify-center border border-red-500/20">
                <AlertCircle className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-base font-bold text-foreground">Reset to Defaults?</h3>
                <p className="text-xs text-muted-foreground">This action cannot be undone.</p>
              </div>
            </div>

            <p className="text-xs text-muted-foreground leading-relaxed">
              This will restore the original StoryForge AI logo and restore the default Deep Navy background and Sunset Fire highlight palette across all pages.
            </p>

            <div className="flex items-center justify-end gap-3 pt-2">
              <button
                onClick={() => setShowResetConfirm(false)}
                className="px-4 py-2 text-xs font-semibold text-muted-foreground hover:text-foreground rounded-xl border border-border bg-card cursor-pointer"
              >
                Cancel
              </button>
              <button
                onClick={handleConfirmReset}
                disabled={isResetting}
                className="px-4 py-2 text-xs font-bold text-white bg-red-600 hover:bg-red-700 rounded-xl shadow-sm transition-colors flex items-center gap-2 cursor-pointer disabled:opacity-50"
              >
                {isResetting ? <><RefreshCw className="w-3.5 h-3.5 animate-spin" /> Resetting...</> : 'Yes, Reset Defaults'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
