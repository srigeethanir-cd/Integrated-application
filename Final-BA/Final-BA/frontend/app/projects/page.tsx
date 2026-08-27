'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

export default function ProjectsRedirectPage() {
  const router = useRouter();

  useEffect(() => {
    // Seamlessly redirect /projects to /dashboard (where Projects in-page workspace lives)
    router.replace('/dashboard');
  }, [router]);

  return null;
}
