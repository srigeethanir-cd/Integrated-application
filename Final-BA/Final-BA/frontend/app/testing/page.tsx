'use client';

import { useEffect } from 'react';

export default function ApplicationTestingAcceleratorPage() {
  useEffect(() => {
    // Force a full-page reload/navigation to let Nginx handle /application-testing/
    window.location.href = '/application-testing/';
  }, []);

  return (
    <div className="min-h-screen flex items-center justify-center bg-[#1B1B3A]">
      <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-[#FF602B]"></div>
    </div>
  );
}
