'use client';

import React from 'react';
import { Settings, ArrowLeft } from 'lucide-react';
import Link from 'next/link';

export default function SettingsPage() {
  return (
    <div className="flex-1 flex flex-col min-h-screen bg-[#F7F9FC] font-sans p-8 space-y-6">
      <header className="flex items-center justify-between pb-4 border-b border-gray-200">
        <div className="flex items-center gap-3">
          <Link href="/dashboard" className="text-xs font-semibold text-gray-500 hover:text-[#FF602B] flex items-center gap-1">
            <ArrowLeft className="w-3.5 h-3.5" /> Return to User Story Workspace
          </Link>
        </div>
      </header>

      <div className="flex-1 flex flex-col items-center justify-center p-12 text-center bg-white rounded-2xl border border-gray-200 shadow-sm max-w-2xl mx-auto space-y-4">
        <div className="w-16 h-16 rounded-2xl bg-gradient-to-r from-[#FF602B] to-[#4318FF] flex items-center justify-center text-white shadow-lg">
          <Settings className="w-8 h-8" />
        </div>
        <h1 className="text-2xl font-extrabold text-gray-900 tracking-tight">System Settings &amp; Integrations</h1>
        <p className="text-sm text-gray-500 max-w-md">
          Configure API keys, Jira/ADO connections, LLM provider endpoints, and workspace permissions.
        </p>
      </div>
    </div>
  );
}
