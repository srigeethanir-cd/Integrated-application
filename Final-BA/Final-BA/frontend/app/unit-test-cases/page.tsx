'use client';

import React from 'react';

export default function UnitTestCasesAcceleratorPage() {
  return (
    <div className="flex-1 w-full h-full min-h-screen bg-[#F7F9FC] flex flex-col overflow-hidden">
      <iframe
        src="/unit-test-cases/?embedded=true"
        title="Unit Test Cases Accelerator"
        className="w-full h-screen border-none block flex-1"
        style={{ width: '100%', height: '100vh', border: 'none' }}
      />
    </div>
  );
}
