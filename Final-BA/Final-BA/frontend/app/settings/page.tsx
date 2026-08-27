'use client';

import React, { useState, useRef } from 'react';
import { 
  ArrowLeft, 
  UploadCloud, 
  Sparkles, 
  Image as ImageIcon, 
  Check, 
  Palette, 
  AlertCircle,
  CheckCircle2,
  RefreshCw,
  Sun,
  Moon,
  Trash2
} from 'lucide-react';
import Link from 'next/link';
import { usePersonalization } from '@/context/PersonalizationContext';

interface ThemeDefinition {
  id: string;
  name: string;
  family: 'purple' | 'blue' | 'green' | 'orange' | 'rose';
  mode: 'light' | 'dark';
  accentHex: string;
  bgHex: string;
  cardHex: string;
  sidebarHex: string;
  borderHex: string;
  gradient: string;
}

const THEMES: ThemeDefinition[] = [
  {
    id: 'purple-light',
    name: 'Purple Light',
    family: 'purple',
    mode: 'light',
    accentHex: '#7551FF',
    bgHex: '#F7F9FC',
    cardHex: '#FFFFFF',
    sidebarHex: '#1B1B3A',
    borderHex: '#E5E7EB',
    gradient: 'linear-gradient(135deg, #FF602B 0%, #4318FF 100%)',
  },
  {
    id: 'purple-dark',
    name: 'Purple Dark',
    family: 'purple',
    mode: 'dark',
    accentHex: '#8B5CF6',
    bgHex: '#0F0C1B',
    cardHex: '#1A162B',
    sidebarHex: '#0A0814',
    borderHex: '#2E284A',
    gradient: 'linear-gradient(135deg, #EC4899 0%, #7551FF 100%)',
  },
  {
    id: 'blue-light',
    name: 'Blue Light',
    family: 'blue',
    mode: 'light',
    accentHex: '#2563EB',
    bgHex: '#F8FAFC',
    cardHex: '#FFFFFF',
    sidebarHex: '#0F172A',
    borderHex: '#E2E8F0',
    gradient: 'linear-gradient(135deg, #0EA5E9 0%, #2563EB 100%)',
  },
  {
    id: 'blue-dark',
    name: 'Blue Dark',
    family: 'blue',
    mode: 'dark',
    accentHex: '#3B82F6',
    bgHex: '#0B0F19',
    cardHex: '#111827',
    sidebarHex: '#080C14',
    borderHex: '#1E293B',
    gradient: 'linear-gradient(135deg, #0284C7 0%, #2563EB 100%)',
  },
  {
    id: 'green-light',
    name: 'Green Light',
    family: 'green',
    mode: 'light',
    accentHex: '#059669',
    bgHex: '#F7FBF9',
    cardHex: '#FFFFFF',
    sidebarHex: '#064E3B',
    borderHex: '#D1FAE5',
    gradient: 'linear-gradient(135deg, #10B981 0%, #047857 100%)',
  },
  {
    id: 'green-dark',
    name: 'Green Dark',
    family: 'green',
    mode: 'dark',
    accentHex: '#10B981',
    bgHex: '#061A14',
    cardHex: '#0B2920',
    sidebarHex: '#04140F',
    borderHex: '#134E39',
    gradient: 'linear-gradient(135deg, #059669 0%, #047857 100%)',
  },
  {
    id: 'orange-light',
    name: 'Orange Light',
    family: 'orange',
    mode: 'light',
    accentHex: '#EA580C',
    bgHex: '#FFFBF7',
    cardHex: '#FFFFFF',
    sidebarHex: '#2A1208',
    borderHex: '#FED7AA',
    gradient: 'linear-gradient(135deg, #F59E0B 0%, #EA580C 100%)',
  },
  {
    id: 'orange-dark',
    name: 'Orange Dark',
    family: 'orange',
    mode: 'dark',
    accentHex: '#F97316',
    bgHex: '#180D06',
    cardHex: '#27160D',
    sidebarHex: '#100804',
    borderHex: '#432111',
    gradient: 'linear-gradient(135deg, #D97706 0%, #EA580C 100%)',
  },
  {
    id: 'rose-light',
    name: 'Rose Light',
    family: 'rose',
    mode: 'light',
    accentHex: '#E11D48',
    bgHex: '#FFF8F9',
    cardHex: '#FFFFFF',
    sidebarHex: '#2C0B14',
    borderHex: '#FECDD3',
    gradient: 'linear-gradient(135deg, #FB7185 0%, #E11D48 100%)',
  },
  {
    id: 'rose-dark',
    name: 'Rose Dark',
    family: 'rose',
    mode: 'dark',
    accentHex: '#F43F5E',
    bgHex: '#17060B',
    cardHex: '#280C14',
    sidebarHex: '#0F0307',
    borderHex: '#4C1220',
    gradient: 'linear-gradient(135deg, #BE123C 0%, #E11D48 100%)',
  },
];

export default function SettingsPage() {
  const { 
    logoUrl, 
    theme, 
    setTheme, 
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
  const [logoStatus, setLogoStatus] = useState<{ type: 'success' | 'error'; message: string } | null>(null);

  // Theme State
  const [themeFilterMode, setThemeFilterMode] = useState<'all' | 'light' | 'dark'>('all');
  const [, setIsSavingTheme] = useState(false);
  const [themeStatus, setThemeStatus] = useState<{ type: 'success' | 'error'; message: string } | null>(null);

  // Handle Logo selection
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (!file.type.startsWith('image/')) {
      setLogoStatus({ type: 'error', message: 'Please select a valid image file (PNG, JPG, SVG, WebP).' });
      return;
    }

    if (file.size > 10 * 1024 * 1024) {
      setLogoStatus({ type: 'error', message: 'Image size exceeds 10MB limit.' });
      return;
    }

    setSelectedFile(file);
    const objectUrl = URL.createObjectURL(file);
    setPreviewUrl(objectUrl);
    setLogoStatus(null);
  };

  const handleUploadLogo = async () => {
    if (!selectedFile) return;
    if (!isAdmin) {
      setLogoStatus({ type: 'error', message: 'Administrator permissions required to change application branding.' });
      return;
    }

    setIsUploading(true);
    setLogoStatus(null);

    try {
      await uploadLogo(selectedFile);
      setLogoStatus({ type: 'success', message: 'Logo successfully uploaded to Cloudinary and applied globally.' });
      setSelectedFile(null);
      setPreviewUrl(null);
    } catch (err: any) {
      setLogoStatus({ type: 'error', message: err.message || 'Failed to upload logo to Cloudinary.' });
    } finally {
      setIsUploading(false);
    }
  };

  const handleRemoveLogo = async () => {
    if (!isAdmin) {
      setLogoStatus({ type: 'error', message: 'Administrator permissions required to modify application branding.' });
      return;
    }

    setIsRemoving(true);
    setLogoStatus(null);

    try {
      await removeLogo();
      setSelectedFile(null);
      setPreviewUrl(null);
      setLogoStatus({ type: 'success', message: 'Custom logo removed. Default branding restored.' });
    } catch (err: any) {
      setLogoStatus({ type: 'error', message: err.message || 'Failed to remove logo.' });
    } finally {
      setIsRemoving(false);
    }
  };

  const handleSelectTheme = async (targetThemeId: string) => {
    if (!isAdmin) {
      setThemeStatus({ type: 'error', message: 'Administrator permissions required to update the global theme.' });
      return;
    }

    setIsSavingTheme(true);
    setThemeStatus(null);

    try {
      await setTheme(targetThemeId);
      setThemeStatus({ type: 'success', message: `Theme updated to '${targetThemeId}' successfully.` });
    } catch (err: any) {
      setThemeStatus({ type: 'error', message: err.message || 'Failed to update theme.' });
    } finally {
      setIsSavingTheme(false);
    }
  };

  const filteredThemes = THEMES.filter((t) => {
    if (themeFilterMode === 'light') return t.mode === 'light';
    if (themeFilterMode === 'dark') return t.mode === 'dark';
    return true;
  });

  return (
    <div className="flex-1 flex flex-col min-h-screen bg-[var(--background,#F7F9FC)] font-sans p-6 md:p-8 space-y-6">
      {/* Top Header */}
      <header className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-border gap-4">
        <div className="flex items-center gap-3">
          <Link href="/dashboard" className="text-xs font-semibold text-muted-foreground hover:text-[var(--primary,#7551FF)] flex items-center gap-1.5 transition-colors">
            <ArrowLeft className="w-3.5 h-3.5" /> Return to Workspace
          </Link>
        </div>
      </header>

      {/* Main Settings Container */}
      <div className="max-w-6xl mx-auto w-full space-y-6">
        {/* Page Title */}
        <div>
          <h1 className="text-2xl font-extrabold text-foreground tracking-tight flex items-center gap-2.5">
            <Palette className="w-6 h-6 text-primary" /> Settings &amp; Personalization
          </h1>
          <p className="text-sm text-muted-foreground mt-0.5">
            Customize application logo branding and select from 10 global visual themes.
          </p>
        </div>

        {/* Read-Only Notice if non-admin */}
        {!isAdmin && (
          <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-800 dark:text-amber-300 text-xs flex items-center gap-3">
            <AlertCircle className="w-4 h-4 shrink-0 text-amber-500" />
            <span>
              You are currently signed in as <strong>{userRole}</strong> with read-only access. Global branding and theme modifications require administrator privileges.
            </span>
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
                  <p className="text-xs text-muted-foreground">
                    Upload a custom application logo to Cloudinary storage or reset to default branding.
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-2">
                <span className="text-[11px] font-semibold px-2.5 py-1 rounded-full bg-muted text-muted-foreground">
                  Cloudinary Upload
                </span>
              </div>
            </div>

            {/* Logo Status Message */}
            {logoStatus && (
              <div className={`p-3.5 rounded-xl text-xs flex items-center gap-2.5 ${
                logoStatus.type === 'success' 
                  ? 'bg-green-500/10 border border-green-500/20 text-green-700 dark:text-green-300' 
                  : 'bg-red-500/10 border border-red-500/20 text-red-700 dark:text-red-300'
              }`}>
                {logoStatus.type === 'success' ? <CheckCircle2 className="w-4 h-4 text-green-500 shrink-0" /> : <AlertCircle className="w-4 h-4 text-red-500 shrink-0" />}
                <span>{logoStatus.message}</span>
              </div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 items-stretch">
              {/* Left Card: Current Active Logo */}
              <div className="flex flex-col justify-between p-5 rounded-xl border border-border bg-muted/20 space-y-4">
                <div>
                  <span className="text-xs font-bold text-muted-foreground uppercase tracking-wider">Current Logo</span>
                  <div className="mt-3 p-6 rounded-xl bg-muted/40 border border-border/80 flex items-center justify-center min-h-[110px]">
                    {logoUrl ? (
                      <img 
                        src={logoUrl} 
                        alt="Custom Application Logo" 
                        className="max-h-16 max-w-full object-contain drop-shadow-sm" 
                      />
                    ) : (
                      <div className="flex items-center gap-3">
                        <div className="w-9 h-9 rounded-xl bg-gradient-to-r from-[#FF602B] to-[#4318FF] flex items-center justify-center text-white shadow-md">
                          <Sparkles className="w-5 h-5 fill-white" />
                        </div>
                        <div className="text-left">
                          <p className="font-extrabold text-foreground text-sm leading-tight">StoryForge AI</p>
                          <span className="text-[10px] text-muted-foreground">Default Application Logo</span>
                        </div>
                      </div>
                    )}
                  </div>
                </div>

                <div className="flex items-center justify-between text-xs pt-2">
                  <span className="text-muted-foreground">
                    Status: <strong className="text-foreground">{logoUrl ? 'Custom Logo' : 'Default Logo'}</strong>
                  </span>

                  {logoUrl && (
                    <button
                      onClick={handleRemoveLogo}
                      disabled={!isAdmin || isRemoving}
                      className="text-red-500 hover:text-red-600 font-semibold flex items-center gap-1.5 hover:underline disabled:opacity-50 cursor-pointer text-xs"
                    >
                      {isRemoving ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Trash2 className="w-3.5 h-3.5" />}
                      Remove / Reset Logo
                    </button>
                  )}
                </div>
              </div>

              {/* Right Card: Upload & Preview New Logo */}
              <div className="flex flex-col justify-between p-5 rounded-xl border border-border bg-card space-y-4">
                <div>
                  <span className="text-xs font-bold text-muted-foreground uppercase tracking-wider">Upload New Logo</span>
                  
                  {/* Hidden file input */}
                  <input 
                    type="file" 
                    ref={fileInputRef}
                    onChange={handleFileChange}
                    accept="image/png,image/jpeg,image/svg+xml,image/webp" 
                    className="hidden"
                  />

                  {previewUrl ? (
                    /* File Selected Preview */
                    <div className="mt-3 p-4 rounded-xl border-2 border-dashed border-primary/50 bg-primary/5 flex flex-col items-center justify-center space-y-3 min-h-[110px]">
                      <img 
                        src={previewUrl} 
                        alt="New Logo Preview" 
                        className="max-h-14 max-w-full object-contain" 
                      />
                      <span className="text-[11px] font-medium text-muted-foreground">
                        {selectedFile?.name} ({(selectedFile ? selectedFile.size / 1024 : 0).toFixed(1)} KB)
                      </span>
                    </div>
                  ) : (
                    /* Drag & Drop Box */
                    <div 
                      onClick={() => isAdmin && fileInputRef.current?.click()}
                      className={`mt-3 p-6 rounded-xl border-2 border-dashed border-border flex flex-col items-center justify-center space-y-2 text-center transition-colors min-h-[110px] ${
                        isAdmin ? 'hover:border-primary/60 hover:bg-muted/30 cursor-pointer' : 'opacity-60 cursor-not-allowed'
                      }`}
                    >
                      <UploadCloud className="w-6 h-6 text-muted-foreground" />
                      <p className="text-xs font-semibold text-foreground">Click to browse or drag and drop image</p>
                      <p className="text-[10px] text-muted-foreground">PNG, SVG, JPG, or WebP up to 10MB</p>
                    </div>
                  )}
                </div>

                {/* Actions */}
                <div className="flex items-center justify-end gap-3 pt-2">
                  {previewUrl && (
                    <button
                      onClick={() => {
                        setSelectedFile(null);
                        setPreviewUrl(null);
                      }}
                      className="px-3 py-1.5 text-xs font-semibold text-muted-foreground hover:text-foreground rounded-lg border border-border bg-card cursor-pointer"
                    >
                      Cancel
                    </button>
                  )}

                  <button
                    onClick={previewUrl ? handleUploadLogo : () => fileInputRef.current?.click()}
                    disabled={!isAdmin || isUploading}
                    className={`px-4 py-2 text-xs font-bold text-white rounded-xl shadow-sm flex items-center gap-2 transition-transform cursor-pointer ${
                      previewUrl ? 'bg-gradient-to-r from-orange-500 to-purple-600 hover:scale-[1.02]' : 'bg-[var(--primary,#7551FF)] hover:opacity-90'
                    } disabled:opacity-50`}
                  >
                    {isUploading ? (
                      <>
                        <RefreshCw className="w-3.5 h-3.5 animate-spin" /> Uploading to Cloudinary...
                      </>
                    ) : previewUrl ? (
                      <>
                        <UploadCloud className="w-3.5 h-3.5" /> Upload &amp; Save Logo
                      </>
                    ) : (
                      <>
                        <ImageIcon className="w-3.5 h-3.5" /> Select Logo File
                      </>
                    )}
                  </button>
                </div>
              </div>
            </div>
          </section>

          {/* ================================================================= */}
          {/* 2. CHANGE THEME SECTION (10 Visual Themes) */}
          {/* ================================================================= */}
          <section className="bg-card border border-border rounded-2xl p-6 md:p-8 shadow-xs space-y-6">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-border/60">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500/20 to-purple-500/20 flex items-center justify-center text-primary border border-primary/20">
                  <Palette className="w-5 h-5" />
                </div>
                <div>
                  <h2 className="text-lg font-bold text-foreground">Change Theme</h2>
                  <p className="text-xs text-muted-foreground">
                    Select from 10 enterprise color themes across Light and Dark visual modes.
                  </p>
                </div>
              </div>

              {/* Filter Mode Buttons */}
              <div className="flex items-center bg-muted/60 p-1 rounded-xl border border-border text-xs gap-1">
                <button
                  onClick={() => setThemeFilterMode('all')}
                  className={`px-3 py-1 rounded-lg font-semibold transition-all cursor-pointer ${
                    themeFilterMode === 'all' ? 'bg-card text-foreground shadow-xs' : 'text-muted-foreground hover:text-foreground'
                  }`}
                >
                  All (10)
                </button>
                <button
                  onClick={() => setThemeFilterMode('light')}
                  className={`px-3 py-1 rounded-lg font-semibold flex items-center gap-1.5 transition-all cursor-pointer ${
                    themeFilterMode === 'light' ? 'bg-card text-foreground shadow-xs' : 'text-muted-foreground hover:text-foreground'
                  }`}
                >
                  <Sun className="w-3 h-3 text-amber-500" /> Light
                </button>
                <button
                  onClick={() => setThemeFilterMode('dark')}
                  className={`px-3 py-1 rounded-lg font-semibold flex items-center gap-1.5 transition-all cursor-pointer ${
                    themeFilterMode === 'dark' ? 'bg-card text-foreground shadow-xs' : 'text-muted-foreground hover:text-foreground'
                  }`}
                >
                  <Moon className="w-3 h-3 text-indigo-400" /> Dark
                </button>
              </div>
            </div>

            {/* Theme Status Message */}
            {themeStatus && (
              <div className={`p-3.5 rounded-xl text-xs flex items-center gap-2.5 ${
                themeStatus.type === 'success' 
                  ? 'bg-green-500/10 border border-green-500/20 text-green-700 dark:text-green-300' 
                  : 'bg-red-500/10 border border-red-500/20 text-red-700 dark:text-red-300'
              }`}>
                {themeStatus.type === 'success' ? <CheckCircle2 className="w-4 h-4 text-green-500 shrink-0" /> : <AlertCircle className="w-4 h-4 text-red-500 shrink-0" />}
                <span>{themeStatus.message}</span>
              </div>
            )}

            {/* Theme Grid (10 Themes as visual swatches & mockup cards) */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
              {filteredThemes.map((t) => {
                const isSelected = theme === t.id;

                return (
                  <div
                    key={t.id}
                    onClick={() => isAdmin && handleSelectTheme(t.id)}
                    className={`relative flex flex-col p-4 rounded-2xl border-2 transition-all cursor-pointer group ${
                      isSelected
                        ? 'border-[var(--primary,#7551FF)] bg-[var(--primary,#7551FF)]/5 shadow-md shadow-purple-500/10 scale-[1.02]'
                        : 'border-border bg-card hover:border-border/80 hover:shadow-xs'
                    } ${!isAdmin ? 'opacity-80' : ''}`}
                  >
                    {/* Checkmark circle badge in top right */}
                    {isSelected && (
                      <div className="absolute top-2.5 right-2.5 w-5 h-5 rounded-full bg-[var(--primary,#7551FF)] text-white flex items-center justify-center shadow-xs">
                        <Check className="w-3 h-3 stroke-[3]" />
                      </div>
                    )}

                    {/* Visual UI Miniature Card Preview */}
                    <div 
                      className="w-full h-24 rounded-xl border border-border/80 overflow-hidden flex flex-col shadow-inner"
                      style={{ backgroundColor: t.bgHex }}
                    >
                      {/* Mockup Header */}
                      <div 
                        className="h-5.5 border-b border-border/50 px-2 flex items-center justify-between"
                        style={{ backgroundColor: t.cardHex }}
                      >
                        <div className="flex items-center gap-1">
                          <span className="w-1.5 h-1.5 rounded-full bg-red-400 opacity-60" />
                          <span className="w-1.5 h-1.5 rounded-full bg-amber-400 opacity-60" />
                          <span className="w-1.5 h-1.5 rounded-full bg-green-400 opacity-60" />
                        </div>
                        <span 
                          className="w-8 h-2 rounded-full" 
                          style={{ backgroundColor: t.accentHex, opacity: 0.8 }} 
                        />
                      </div>

                      {/* Mockup Body with Sidebar & Content */}
                      <div className="flex-1 flex overflow-hidden">
                        {/* Mock Sidebar */}
                        <div 
                          className="w-6 border-r border-border/40 p-1 flex flex-col gap-1"
                          style={{ backgroundColor: t.sidebarHex }}
                        >
                          <span className="w-3 h-1.5 rounded-xs" style={{ background: t.gradient }} />
                          <span className="w-3 h-1 rounded-xs bg-white/20" />
                          <span className="w-3 h-1 rounded-xs bg-white/20" />
                        </div>

                        {/* Mock Content */}
                        <div className="flex-1 p-2 space-y-1.5 flex flex-col justify-center">
                          <div 
                            className="h-2 rounded-xs w-4/5" 
                            style={{ backgroundColor: t.cardHex, border: `1px solid ${t.borderHex}` }} 
                          />
                          <div 
                            className="h-2 rounded-xs w-3/5" 
                            style={{ backgroundColor: t.cardHex, border: `1px solid ${t.borderHex}` }} 
                          />
                        </div>
                      </div>
                    </div>

                    {/* Theme Name & Metadata */}
                    <div className="mt-3 flex items-center justify-between">
                      <div>
                        <p className="font-bold text-xs text-foreground leading-tight">{t.name}</p>
                        <span className="text-[10px] text-muted-foreground capitalize">{t.mode} Mode</span>
                      </div>

                      {/* Accent Swatch */}
                      <div 
                        className="w-4 h-4 rounded-full border border-white/50 shadow-xs shrink-0"
                        style={{ backgroundColor: t.accentHex }}
                        title={`Accent: ${t.accentHex}`}
                      />
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Theme Summary Banner */}
            <div className="p-4 rounded-xl bg-muted/30 border border-border flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs">
              <div className="flex items-center gap-2.5">
                <div 
                  className="w-4 h-4 rounded-full shrink-0" 
                  style={{ backgroundColor: THEMES.find(t => t.id === theme)?.accentHex || '#7551FF' }} 
                />
                <span>
                  Currently active theme: <strong className="text-foreground">{THEMES.find(t => t.id === theme)?.name || theme}</strong>
                </span>
              </div>

              <span className="text-muted-foreground text-[11px]">
                Colors apply automatically across the workspace, top navigation, and sidebar.
              </span>
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}
