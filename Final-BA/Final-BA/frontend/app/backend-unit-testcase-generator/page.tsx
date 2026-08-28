'use client';

import React from 'react';

export default function BackendUnitTestcaseGeneratorPage() {
  return (
    <div className="flex-1 w-full h-full min-h-screen bg-[#F7F9FC] flex flex-col overflow-hidden">
      <iframe
        src="/backend-unit-testcase-generator/?embedded=true"
        title="Backend Unit-Testcase Generator"
        className="w-full h-screen border-none block flex-1"
        style={{ width: '100%', height: '100vh', border: 'none' }}
      />
    </div>
  );
}
