'use client';

import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';

// ─── Translation map ───────────────────────────────────────────────────────────
export const TRANSLATIONS = {
  en: {
    // Sidebar
    userStory: 'User Story',
    uiCode: 'UI Code',
    apiCode: 'API Code',
    unitTestCases: 'Unit Test Cases',
    appTesting: 'Application Testing',
    backendGenerator: 'Backend Unit-Testcase Generator',
    settings: 'Settings',
    // Settings drawer
    appearanceSettings: 'Appearance Settings',
    theme: 'Theme',
    interfaceMode: 'Interface Mode',
    light: 'Light',
    dark: 'Dark',
    system: 'System',
    cloudinaryConnect: 'Cloudinary Connect',
    cloudName: 'Cloud Name',
    apiKey: 'API Key',
    apiSecret: 'API Secret',
    confirmCloudinary: 'Confirm Cloudinary Settings',
    saved: 'Saved!',
    language: 'Language',
    current: 'Current',
    active: 'Active',
    confirm: 'Confirm',
    applied: 'Applied',
    uploadLogo: 'Upload Logo',
    changeLogo: 'Change',
    removeLogo: 'Remove',
    confirmLogo: 'Confirm & Save Logo',
    logoUpdated: 'Logo updated in app!',
    logoUploadHint: 'JPG, PNG up to 2MB',
    uploading: 'Uploading...',
    uploadSuccess: 'Logo uploaded!',
    uploadFailed: 'Upload failed',
    allFieldsRequired: 'All fields are required.',
    supportsFormats: 'Supports screenshots, .jpg, .jpeg, .png',
    // Dashboard / common
    dashboard: 'Dashboard',
    projects: 'Projects',
    newProject: 'New Project',
    loading: 'Loading...',
    save: 'Save',
    cancel: 'Cancel',
    delete: 'Delete',
    edit: 'Edit',
    close: 'Close',
  },
  ta: {
    // Sidebar
    userStory: 'பயனர் கதை',
    uiCode: 'UI குறியீடு',
    apiCode: 'API குறியீடு',
    unitTestCases: 'அலகு சோதனை வழக்குகள்',
    appTesting: 'பயன்பாட்டு சோதனை',
    backendGenerator: 'பின்தள அலகு சோதனை உருவாக்கி',
    settings: 'அமைப்புகள்',
    // Settings drawer
    appearanceSettings: 'தோற்ற அமைப்புகள்',
    theme: 'கருப்பொருள்',
    interfaceMode: 'இடைமுக முறை',
    light: 'வெளிச்சம்',
    dark: 'இருள்',
    system: 'கணினி',
    cloudinaryConnect: 'கிளவுடினரி இணைப்பு',
    cloudName: 'கிளவுட் பெயர்',
    apiKey: 'API திறவுகோல்',
    apiSecret: 'API ரகசியம்',
    confirmCloudinary: 'கிளவுடினரி அமைப்புகளை உறுதிப்படுத்து',
    saved: 'சேமிக்கப்பட்டது!',
    language: 'மொழி',
    current: 'தற்போதைய',
    active: 'செயலில்',
    confirm: 'உறுதிப்படுத்து',
    applied: 'பயன்படுத்தப்பட்டது',
    uploadLogo: 'லோகோவை பதிவேற்று',
    changeLogo: 'மாற்று',
    removeLogo: 'அகற்று',
    confirmLogo: 'லோகோவை உறுதிசெய்து சேமி',
    logoUpdated: 'லோகோ பயன்பாட்டில் புதுப்பிக்கப்பட்டது!',
    logoUploadHint: 'JPG, PNG 2MB வரை',
    uploading: 'பதிவேற்றுகிறது...',
    uploadSuccess: 'லோகோ பதிவேற்றப்பட்டது!',
    uploadFailed: 'பதிவேற்றம் தோல்வியடைந்தது',
    allFieldsRequired: 'அனைத்து புலங்களும் தேவை.',
    supportsFormats: 'ஸ்கிரீன்ஷாட்கள், .jpg, .jpeg, .png ஆதரிக்கிறது',
    dashboard: 'டாஷ்போர்டு',
    projects: 'திட்டங்கள்',
    newProject: 'புதிய திட்டம்',
    loading: 'ஏற்றுகிறது...',
    save: 'சேமி',
    cancel: 'ரத்து செய்',
    delete: 'நீக்கு',
    edit: 'திருத்து',
    close: 'மூடு',
  },
  hi: {
    // Sidebar
    userStory: 'उपयोगकर्ता कहानी',
    uiCode: 'UI कोड',
    apiCode: 'API कोड',
    unitTestCases: 'यूनिट परीक्षण मामले',
    appTesting: 'एप्लिकेशन परीक्षण',
    backendGenerator: 'बैकएंड यूनिट-टेस्टकेस जेनरेटर',
    settings: 'सेटिंग्स',
    // Settings drawer
    appearanceSettings: 'उपस्थिति सेटिंग्स',
    theme: 'थीम',
    interfaceMode: 'इंटरफ़ेस मोड',
    light: 'हल्का',
    dark: 'अंधेरा',
    system: 'सिस्टम',
    cloudinaryConnect: 'क्लाउडिनरी कनेक्ट',
    cloudName: 'क्लाउड नाम',
    apiKey: 'API कुंजी',
    apiSecret: 'API रहस्य',
    confirmCloudinary: 'क्लाउडिनरी सेटिंग्स की पुष्टि करें',
    saved: 'सहेजा गया!',
    language: 'भाषा',
    current: 'वर्तमान',
    active: 'सक्रिय',
    confirm: 'पुष्टि करें',
    applied: 'लागू किया',
    uploadLogo: 'लोगो अपलोड करें',
    changeLogo: 'बदलें',
    removeLogo: 'हटाएं',
    confirmLogo: 'लोगो की पुष्टि करें और सहेजें',
    logoUpdated: 'लोगो ऐप में अपडेट हो गया!',
    logoUploadHint: 'JPG, PNG 2MB तक',
    uploading: 'अपलोड हो रहा है...',
    uploadSuccess: 'लोगो अपलोड हो गया!',
    uploadFailed: 'अपलोड विफल',
    allFieldsRequired: 'सभी फ़ील्ड आवश्यक हैं।',
    supportsFormats: 'स्क्रीनशॉट, .jpg, .jpeg, .png का समर्थन करता है',
    dashboard: 'डैशबोर्ड',
    projects: 'प्रोजेक्ट्स',
    newProject: 'नया प्रोजेक्ट',
    loading: 'लोड हो रहा है...',
    save: 'सहेजें',
    cancel: 'रद्द करें',
    delete: 'हटाएं',
    edit: 'संपादित करें',
    close: 'बंद करें',
  },
  fr: {
    // Sidebar
    userStory: 'Histoire Utilisateur',
    uiCode: 'Code UI',
    apiCode: 'Code API',
    unitTestCases: 'Cas de Test Unitaire',
    appTesting: 'Test Application',
    backendGenerator: 'Générateur de Tests Backend',
    settings: 'Paramètres',
    // Settings drawer
    appearanceSettings: 'Paramètres d\'Apparence',
    theme: 'Thème',
    interfaceMode: 'Mode Interface',
    light: 'Clair',
    dark: 'Sombre',
    system: 'Système',
    cloudinaryConnect: 'Connexion Cloudinary',
    cloudName: 'Nom du Cloud',
    apiKey: 'Clé API',
    apiSecret: 'Secret API',
    confirmCloudinary: 'Confirmer les Paramètres Cloudinary',
    saved: 'Enregistré!',
    language: 'Langue',
    current: 'Actuel',
    active: 'Actif',
    confirm: 'Confirmer',
    applied: 'Appliqué',
    uploadLogo: 'Télécharger le Logo',
    changeLogo: 'Changer',
    removeLogo: 'Supprimer',
    confirmLogo: 'Confirmer et enregistrer le logo',
    logoUpdated: 'Logo mis à jour dans l\'application !',
    logoUploadHint: 'JPG, PNG jusqu\'à 2MB',
    uploading: 'Téléchargement...',
    uploadSuccess: 'Logo téléchargé!',
    uploadFailed: 'Échec du téléchargement',
    allFieldsRequired: 'Tous les champs sont requis.',
    supportsFormats: 'Supporte captures d\'écran, .jpg, .jpeg, .png',
    dashboard: 'Tableau de bord',
    projects: 'Projets',
    newProject: 'Nouveau Projet',
    loading: 'Chargement...',
    save: 'Sauvegarder',
    cancel: 'Annuler',
    delete: 'Supprimer',
    edit: 'Modifier',
    close: 'Fermer',
  },
} as const;

export type LangCode = keyof typeof TRANSLATIONS;
export type TranslationKey = keyof typeof TRANSLATIONS['en'];

// ─── Context ───────────────────────────────────────────────────────────────────
interface LanguageContextValue {
  lang: LangCode;
  setLang: (lang: LangCode) => void;
  t: (key: TranslationKey) => string;
}

const LanguageContext = createContext<LanguageContextValue>({
  lang: 'en',
  setLang: () => {},
  t: (key) => TRANSLATIONS.en[key],
});

const LANG_STORAGE_KEY = 'app_language';

export function LanguageProvider({ children }: { children: React.ReactNode }) {
  const [lang, setLangState] = useState<LangCode>('en');

  // Load from localStorage on mount
  useEffect(() => {
    try {
      const saved = localStorage.getItem(LANG_STORAGE_KEY) as LangCode | null;
      if (saved && saved in TRANSLATIONS) {
        setLangState(saved);
        document.documentElement.lang = saved;
      }
    } catch { /* ignore */ }
  }, []);

  const setLang = useCallback((newLang: LangCode) => {
    setLangState(newLang);
    try {
      localStorage.setItem(LANG_STORAGE_KEY, newLang);
      document.documentElement.lang = newLang;
    } catch { /* ignore */ }
  }, []);

  const t = useCallback(
    (key: TranslationKey): string => TRANSLATIONS[lang][key] ?? TRANSLATIONS.en[key],
    [lang]
  );

  return (
    <LanguageContext.Provider value={{ lang, setLang, t }}>
      {children}
    </LanguageContext.Provider>
  );
}

export function useLanguage() {
  return useContext(LanguageContext);
}
