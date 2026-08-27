'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

export default function RootRedirectPage() {
  const router = useRouter();

  useEffect(() => {
    router.replace('/dashboard');
  }, [router]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-[#1B1B3A]">
      <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-[#FF602B]"></div>
    </div>
  );
}
