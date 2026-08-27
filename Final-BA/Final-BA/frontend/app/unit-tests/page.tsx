'use client';

import { useEffect } from 'react';

export default function UnitTestsAcceleratorPage() {
  useEffect(() => {
    // Force a full-page reload/navigation to let Nginx handle /unit-test-cases/
    window.location.href = '/unit-test-cases/';
  }, []);

  return (
    <div className="min-h-screen flex items-center justify-center bg-[#1B1B3A]">
      <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-[#FF602B]"></div>
    </div>
  );
}
