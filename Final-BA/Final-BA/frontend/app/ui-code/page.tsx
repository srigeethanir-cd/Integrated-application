'use client';

import React from 'react';
import { Code2, ArrowLeft } from 'lucide-react';
import Link from 'next/link';

export default function UiCodeAcceleratorPage() {
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
          <Code2 className="w-8 h-8" />
        </div>
        <h1 className="text-2xl font-extrabold text-gray-900 tracking-tight">UI Code Accelerator</h1>
        <p className="text-sm text-gray-500 max-w-md">
          Automated UI component generator and frontend design system sync module.
        </p>
        <div className="px-4 py-2 bg-purple-50 text-[#7551FF] border border-purple-200 rounded-xl text-xs font-bold">
          Accelerator 2 — Active Module
        </div>
      </div>
    </div>
  );
}
