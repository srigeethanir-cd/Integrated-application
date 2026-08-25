'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

export default function RootPage() {
  const router = useRouter();

  useEffect(() => {
    // Starts directly from Login Page
    router.replace('/login');
  }, [router]);

  return null;
}
