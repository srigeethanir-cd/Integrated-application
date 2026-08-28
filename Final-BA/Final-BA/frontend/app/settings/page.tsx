'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

export default function SettingsPage() {
  const router = useRouter();

  useEffect(() => {
    // Redirect to dashboard and open the Appearance Settings slide-in drawer
    router.replace('/dashboard?openSettings=true');
  }, [router]);

  return (
    <div className="flex-1 flex items-center justify-center min-h-screen bg-[#F7F9FC]">
      <div className="animate-pulse text-xs font-semibold text-gray-400">
        Loading Appearance Settings...
      </div>
    </div>
  );
}
