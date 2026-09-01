'use client';

import React, { useEffect, useState, useRef } from 'react';
import {
  X, Check, Sun, Moon, Laptop, Cloud, Globe,
  CheckCircle2, Image as ImageIcon, Upload, Trash2, RefreshCw
} from 'lucide-react';
import { useTheme, THEMES, InterfaceMode } from '../theme/ThemeContext';
import { useLanguage, LangCode } from '../i18n/LanguageContext';
import { CLOUDINARY_CONFIG } from '../../config/cloudinary.config';

// ── Language list ─────────────────────────────────────────────────────────────
const LANGUAGES: { code: LangCode; nativeLabel: string; label: string; flag: string }[] = [
  { code: 'en', label: 'English', nativeLabel: 'English',   flag: '🇬🇧' },
  { code: 'ta', label: 'Tamil',   nativeLabel: 'தமிழ்',     flag: '🇮🇳' },
  { code: 'hi', label: 'Hindi',   nativeLabel: 'हिन्दी',    flag: '🇮🇳' },
  { code: 'fr', label: 'French',  nativeLabel: 'Français',  flag: '🇫🇷' },
];

const LOGO_STORAGE_KEY = 'app_logo_url';

// ── SHA-1 via Web Crypto API (for Cloudinary signed upload) ───────────────────
async function sha1Hex(message: string): Promise<string> {
  const encoded = new TextEncoder().encode(message);
  const hashBuffer = await crypto.subtle.digest('SHA-1', encoded);
  return Array.from(new Uint8Array(hashBuffer))
    .map((b) => b.toString(16).padStart(2, '0'))
    .join('');
}

// ── Signed Cloudinary upload (no upload_preset required) ─────────────────────
async function uploadSignedToCloudinary(file: File): Promise<string> {
  const { cloudName, apiKey, apiSecret, folder } = CLOUDINARY_CONFIG;
  const timestamp = Math.round(Date.now() / 1000).toString();

  // Signature = SHA1("folder=<folder>&timestamp=<ts><api_secret>")
  const stringToSign = `folder=${folder}&timestamp=${timestamp}${apiSecret}`;
  const signature = await sha1Hex(stringToSign);

  const formData = new FormData();
  formData.append('file', file);
  formData.append('api_key', apiKey);
  formData.append('timestamp', timestamp);
  formData.append('signature', signature);
  formData.append('folder', folder);

  const res = await fetch(
    `https://api.cloudinary.com/v1_1/${cloudName}/image/upload`,
    { method: 'POST', body: formData }
  );

  if (!res.ok) {
    const errText = await res.text().catch(() => res.statusText);
    throw new Error(`Upload failed (${res.status}): ${errText}`);
  }

  const data = await res.json();
  if (!data.secure_url) throw new Error('No URL in Cloudinary response');
  return data.secure_url as string;
}

// ─────────────────────────────────────────────────────────────────────────────

export function AppearanceSettingsDrawer() {
  const { currentThemeId, setTheme, interfaceMode, setInterfaceMode, isSettingsOpen, closeSettings } = useTheme();
  const { lang, setLang, t } = useLanguage();

  // ── Logo state ────────────────────────────────────────────────────────────
  const [logoUrl, setLogoUrl] = useState<string | null>(null);
  const [logoStatus, setLogoStatus] = useState<'idle' | 'uploading' | 'success' | 'error'>('idle');
  const [logoError, setLogoError] = useState('');
  const [logoSaved, setLogoSaved] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Load saved logo on mount + clear any stale cloudinary credentials
  useEffect(() => {
    try {
      // Remove old pre-filled cloudinary creds saved by previous version
      localStorage.removeItem('cloudinary_config');
      // Load saved logo
      const saved = localStorage.getItem(LOGO_STORAGE_KEY);
      if (saved) setLogoUrl(saved);
    } catch { /* empty */ }
  }, []);

  // ── Language state ────────────────────────────────────────────────────────
  const [langSaved, setLangSaved] = useState(false);

  // Close on ESC
  useEffect(() => {
    const fn = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isSettingsOpen) closeSettings();
    };
    window.addEventListener('keydown', fn);
    return () => window.removeEventListener('keydown', fn);
  }, [isSettingsOpen, closeSettings]);

  // Prevent background scroll when open
  useEffect(() => {
    document.body.style.overflow = isSettingsOpen ? 'hidden' : '';
    return () => { document.body.style.overflow = ''; };
  }, [isSettingsOpen]);

  // ── Logo upload handler ───────────────────────────────────────────────────
  async function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;

    setLogoError('');

    const allowed = ['image/jpeg', 'image/jpg', 'image/png'];
    if (!allowed.includes(file.type)) {
      setLogoStatus('error');
      setLogoError('Only JPG and PNG files are supported.');
      setTimeout(() => setLogoStatus('idle'), 3000);
      return;
    }
    if (file.size > CLOUDINARY_CONFIG.maxFileSizeMB * 1024 * 1024) {
      setLogoStatus('error');
      setLogoError(`File must be under ${CLOUDINARY_CONFIG.maxFileSizeMB}MB.`);
      setTimeout(() => setLogoStatus('idle'), 3000);
      return;
    }

    setLogoStatus('uploading');
    try {
      const url = await uploadSignedToCloudinary(file);
      setLogoUrl(url);
      setLogoStatus('success');
      setTimeout(() => setLogoStatus('idle'), 2500);
    } catch (err) {
      console.error('[Cloudinary upload error]', err);
      setLogoStatus('error');
      setLogoError(err instanceof Error ? err.message : 'Upload failed. Please try again.');
      setTimeout(() => { setLogoStatus('idle'); setLogoError(''); }, 4000);
    }

    // Reset so same file can be re-selected
    if (e.target) e.target.value = '';
  }

  function handleConfirmLogo() {
    if (!logoUrl) return;
    try {
      localStorage.setItem(LOGO_STORAGE_KEY, logoUrl);
      window.dispatchEvent(new Event('app_logo_updated'));
      setLogoSaved(true);
      setTimeout(() => setLogoSaved(false), 2500);
    } catch (err) {
      console.error('[Failed to save logo]', err);
    }
  }

  function handleRemoveLogo() {
    setLogoUrl(null);
    setLogoStatus('idle');
    setLogoError('');
    setLogoSaved(false);
    try {
      localStorage.removeItem(LOGO_STORAGE_KEY);
      window.dispatchEvent(new Event('app_logo_updated'));
    } catch { /* empty */ }
  }

  // ── Language confirm ──────────────────────────────────────────────────────
  function handleLanguageConfirm(code: LangCode) {
    setLang(code);
    setLangSaved(true);
    setTimeout(() => setLangSaved(false), 2000);
  }

  // ─────────────────────────────────────────────────────────────────────────
  return (
    <>
      {/* Backdrop */}
      <div
        onClick={closeSettings}
        aria-hidden="true"
        className={`fixed inset-0 z-40 bg-black/40 backdrop-blur-[2px] transition-opacity duration-300 ${
          isSettingsOpen ? 'opacity-100 pointer-events-auto' : 'opacity-0 pointer-events-none'
        }`}
      />

      {/* Slide-in Panel */}
      <aside
        role="dialog"
        aria-modal="true"
        aria-label={t('appearanceSettings')}
        className={`fixed top-0 right-0 z-50 h-full w-full max-w-[480px] bg-white text-[#111827] shadow-2xl flex flex-col border-l border-gray-200 transition-transform duration-300 ease-[cubic-bezier(0.16,1,0.3,1)] ${
          isSettingsOpen ? 'translate-x-0' : 'translate-x-full'
        }`}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-5 border-b border-gray-100 shrink-0">
          <h2 className="text-xl font-bold text-[#111827] tracking-tight">
            {t('appearanceSettings')}
          </h2>
          <button
            type="button"
            onClick={closeSettings}
            aria-label={t('close')}
            className="p-1.5 rounded-xl text-gray-400 hover:text-gray-700 hover:bg-gray-100 transition-colors cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Scrollable content */}
        <div className="flex-1 overflow-y-auto px-6 py-5 space-y-6">

          {/* ── Theme ── */}
          <section>
            <div className="flex items-center justify-between mb-3.5">
              <h3 className="text-sm font-bold text-[#1F2937]">{t('theme')}</h3>
              <span className="text-xs text-gray-400 font-medium">
                {THEMES.find((th) => th.id === currentThemeId)?.name ?? ''}
              </span>
            </div>
            <div className="grid grid-cols-2 gap-3.5">
              {THEMES.map((theme) => {
                const isSelected = currentThemeId === theme.id;
                return (
                  <div
                    key={theme.id}
                    onClick={() => setTheme(theme.id)}
                    role="button"
                    tabIndex={0}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); setTheme(theme.id); }
                    }}
                    className={`group rounded-2xl p-2.5 bg-white transition-all cursor-pointer select-none relative flex flex-col gap-2 ${
                      isSelected
                        ? 'border-2 border-[#EA580C] shadow-sm ring-2 ring-[#EA580C]/10'
                        : 'border border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    {/* Miniature mockup */}
                    <div className="w-full h-[76px] rounded-xl overflow-hidden flex border border-[#E2E8F0] bg-[#F8FAFC]">
                      <div className="w-[36%] h-full p-2 flex flex-col justify-between shrink-0" style={{ backgroundColor: theme.sidebarBg }}>
                        <div className="space-y-1.5">
                          <div className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: theme.previewAccent }} />
                          <div className="h-1.5 w-full rounded-full" style={{ background: `linear-gradient(90deg,${theme.gradientStart},${theme.gradientEnd})` }} />
                          <div className="h-1.5 w-4/5 rounded-full bg-white/20" />
                          <div className="h-1.5 w-3/4 rounded-full bg-white/20" />
                        </div>
                        <div className="w-1.5 h-1.5 rounded-full bg-white/25" />
                      </div>
                      <div className="flex-1 h-full bg-[#FAFBFC] p-2 flex flex-col justify-between">
                        <div className="h-1.5 w-1/2 rounded-full bg-gray-200" />
                        <div className="space-y-1.5 my-auto">
                          <div className="h-2 w-full rounded-md" style={{ background: `linear-gradient(90deg,${theme.gradientStart},${theme.gradientEnd})` }} />
                          <div className="h-2 w-full rounded-md" style={{ background: `linear-gradient(90deg,${theme.gradientStart},${theme.gradientEnd})` }} />
                        </div>
                        <div className="h-1 w-full bg-gray-200/80 rounded-full flex items-center justify-between px-0.5">
                          <div className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: theme.gradientStart }} />
                          <div className="w-2.5 h-1.5 rounded-full" style={{ backgroundColor: theme.gradientEnd }} />
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center justify-between px-0.5 pt-0.5 min-h-[22px]">
                      <span className={`text-xs truncate ${isSelected ? 'font-bold text-[#111827]' : 'font-medium text-[#4B5563]'}`}>
                        {theme.name}
                      </span>
                      {isSelected && (
                        <div className="w-4.5 h-4.5 rounded-full bg-[#EA580C] text-white flex items-center justify-center shrink-0 ml-1">
                          <Check className="w-3 h-3 stroke-[3]" />
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </section>

          {/* ── Interface Mode ── */}
          <section className="pt-4 border-t border-gray-100">
            <h3 className="text-sm font-bold text-[#1F2937] mb-3">{t('interfaceMode')}</h3>
            <div className="grid grid-cols-3 gap-2.5">
              {(
                [
                  { id: 'light',  labelKey: 'light'  as const, icon: Sun },
                  { id: 'dark',   labelKey: 'dark'   as const, icon: Moon },
                  { id: 'system', labelKey: 'system' as const, icon: Laptop },
                ]
              ).map((mode) => {
                const isActive = interfaceMode === mode.id;
                return (
                  <button
                    key={mode.id}
                    type="button"
                    onClick={() => setInterfaceMode(mode.id as InterfaceMode)}
                    className={`flex flex-col items-center justify-center gap-2 py-3 px-2 rounded-xl border transition-all cursor-pointer ${
                      isActive
                        ? 'border-2 border-[#EA580C] bg-[#FFF8F5] text-[#EA580C] font-bold'
                        : 'border-gray-200 bg-white text-gray-600 hover:border-gray-300 hover:bg-gray-50 font-medium'
                    }`}
                  >
                    <mode.icon className={`w-4.5 h-4.5 ${isActive ? 'text-[#EA580C]' : 'text-gray-500'}`} />
                    <span className="text-xs">{t(mode.labelKey)}</span>
                  </button>
                );
              })}
            </div>
          </section>

          {/* ── Cloudinary — Logo Upload only (no credentials shown) ── */}
          <section className="pt-4 border-t border-gray-100">
            <div className="flex items-center gap-2 mb-3">
              <div className="w-7 h-7 rounded-lg bg-[#3448C5]/10 flex items-center justify-center">
                <Cloud className="w-4 h-4 text-[#3448C5]" />
              </div>
              <h3 className="text-sm font-bold text-[#1F2937]">{t('cloudinaryConnect')}</h3>
            </div>

            {/* Supported formats badge */}
            <div className="flex items-center gap-1.5 mb-4 p-2.5 rounded-xl bg-[#F0F4FF] border border-[#DBEAFE]">
              <ImageIcon className="w-3.5 h-3.5 text-[#3448C5] shrink-0" />
              <span className="text-xs text-[#3448C5] font-medium">{t('supportsFormats')}</span>
            </div>

            {logoUrl ? (
              <div className="space-y-3">
                {/* ── Logo preview with Change / Remove ── */}
                <div className="flex items-center gap-4 p-4 rounded-2xl border border-gray-200 bg-[#FAFBFF]">
                  <div className="w-20 h-20 rounded-xl border border-gray-200 bg-white flex items-center justify-center overflow-hidden shadow-sm shrink-0">
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img src={logoUrl} alt="App Logo" className="w-full h-full object-contain p-1" />
                  </div>
                  <div className="flex flex-col gap-2 flex-1">
                    <p className="text-xs text-gray-500 font-medium">{t('uploadLogo')}</p>
                    <button
                      type="button"
                      onClick={() => fileInputRef.current?.click()}
                      className="flex items-center justify-center gap-1.5 px-3 py-2 rounded-xl text-xs font-semibold bg-[#3448C5] text-white hover:bg-[#2a3aad] transition-colors cursor-pointer"
                    >
                      <RefreshCw className="w-3.5 h-3.5" />
                      {t('changeLogo')}
                    </button>
                    <button
                      type="button"
                      onClick={handleRemoveLogo}
                      className="flex items-center justify-center gap-1.5 px-3 py-2 rounded-xl text-xs font-semibold bg-red-50 text-red-500 hover:bg-red-100 border border-red-200 transition-colors cursor-pointer"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                      {t('removeLogo')}
                    </button>
                  </div>
                </div>

                {/* ── Confirm & Save Logo button ── */}
                <button
                  type="button"
                  onClick={handleConfirmLogo}
                  className={`w-full flex items-center justify-center gap-2 py-2.5 rounded-xl text-xs font-bold transition-all cursor-pointer ${
                    logoSaved
                      ? 'bg-green-600 text-white shadow-md'
                      : 'bg-[#059669] hover:bg-[#047857] text-white shadow-sm'
                  }`}
                >
                  {logoSaved ? (
                    <>
                      <CheckCircle2 className="w-4 h-4" />
                      {t('logoUpdated')}
                    </>
                  ) : (
                    <>
                      <Check className="w-4 h-4 stroke-[3]" />
                      {t('confirmLogo')}
                    </>
                  )}
                </button>
              </div>
            ) : (
              /* ── Upload area ── */
              <div>
                <button
                  type="button"
                  onClick={() => fileInputRef.current?.click()}
                  disabled={logoStatus === 'uploading'}
                  className={`w-full flex flex-col items-center justify-center gap-2.5 py-8 rounded-2xl border-2 border-dashed transition-all cursor-pointer ${
                    logoStatus === 'uploading'
                      ? 'border-[#3448C5] bg-[#EEF2FF] cursor-not-allowed'
                      : logoStatus === 'success'
                      ? 'border-green-400 bg-green-50'
                      : logoStatus === 'error'
                      ? 'border-red-400 bg-red-50'
                      : 'border-gray-300 hover:border-[#3448C5] hover:bg-[#EEF2FF]'
                  }`}
                >
                  {logoStatus === 'uploading' && (
                    <>
                      <RefreshCw className="w-7 h-7 text-[#3448C5] animate-spin" />
                      <span className="text-sm text-[#3448C5] font-semibold">{t('uploading')}</span>
                    </>
                  )}
                  {logoStatus === 'success' && (
                    <>
                      <CheckCircle2 className="w-7 h-7 text-green-500" />
                      <span className="text-sm text-green-600 font-semibold">{t('uploadSuccess')}</span>
                    </>
                  )}
                  {logoStatus === 'error' && (
                    <>
                      <ImageIcon className="w-7 h-7 text-red-400" />
                      <span className="text-sm text-red-500 font-semibold">{t('uploadFailed')}</span>
                      {logoError && <span className="text-xs text-red-400 text-center px-4">{logoError}</span>}
                    </>
                  )}
                  {logoStatus === 'idle' && (
                    <>
                      <div className="w-12 h-12 rounded-2xl bg-[#EEF2FF] flex items-center justify-center">
                        <Upload className="w-6 h-6 text-[#3448C5]" />
                      </div>
                      <div className="text-center">
                        <p className="text-sm font-semibold text-[#111827]">{t('uploadLogo')}</p>
                        <p className="text-xs text-gray-400 mt-0.5">{t('logoUploadHint')}</p>
                      </div>
                    </>
                  )}
                </button>
              </div>
            )}

            {/* Hidden file input */}
            <input
              ref={fileInputRef}
              type="file"
              accept=".jpg,.jpeg,.png,image/jpeg,image/png"
              className="hidden"
              onChange={handleFileChange}
            />
          </section>

          {/* ── Language Settings ── */}
          <section className="pt-4 border-t border-gray-100">
            <div className="flex items-center gap-2 mb-3">
              <div className="w-7 h-7 rounded-lg bg-[#059669]/10 flex items-center justify-center">
                <Globe className="w-4 h-4 text-[#059669]" />
              </div>
              <h3 className="text-sm font-bold text-[#1F2937]">{t('language')}</h3>
              {langSaved && (
                <span className="ml-auto text-xs text-green-600 font-semibold flex items-center gap-1">
                  <CheckCircle2 className="w-3.5 h-3.5" /> {t('applied')}
                </span>
              )}
            </div>

            <p className="text-xs text-gray-500 mb-3">
              {t('current')}:{' '}
              <span className="font-semibold text-[#111827]">
                {LANGUAGES.find((l) => l.code === lang)?.nativeLabel ?? 'English'}
              </span>
            </p>

            <div className="space-y-2">
              {LANGUAGES.map((language) => {
                const isActive = lang === language.code;
                return (
                  <div
                    key={language.code}
                    className={`flex items-center justify-between p-3 rounded-xl border transition-all ${
                      isActive
                        ? 'border-[#059669] bg-[#F0FDF4]'
                        : 'border-gray-200 bg-white hover:border-gray-300 hover:bg-gray-50'
                    }`}
                  >
                    {/* Language info — clicking row selects instantly */}
                    <button
                      type="button"
                      onClick={() => handleLanguageConfirm(language.code)}
                      className="flex items-center gap-3 flex-1 text-left cursor-pointer"
                    >
                      <span className="text-xl leading-none">{language.flag}</span>
                      <div>
                        <p className={`text-sm font-semibold ${isActive ? 'text-[#059669]' : 'text-[#111827]'}`}>
                          {language.nativeLabel}
                        </p>
                        <p className="text-xs text-gray-500">{language.label}</p>
                      </div>
                      {isActive && <CheckCircle2 className="w-4 h-4 text-[#059669] ml-1" />}
                    </button>

                    {/* Per-language Confirm button */}
                    <button
                      type="button"
                      onClick={() => handleLanguageConfirm(language.code)}
                      className={`ml-3 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all shrink-0 cursor-pointer ${
                        isActive
                          ? 'bg-[#059669] text-white cursor-default'
                          : 'bg-gray-100 text-gray-700 hover:bg-[#059669] hover:text-white border border-gray-200 hover:border-[#059669]'
                      }`}
                    >
                      {isActive ? t('active') : t('confirm')}
                    </button>
                  </div>
                );
              })}
            </div>
          </section>

        </div>
      </aside>
    </>
  );
}
