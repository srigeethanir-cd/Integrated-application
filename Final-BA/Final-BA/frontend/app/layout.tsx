'use client';

import React from 'react';
import { usePathname } from 'next/navigation';
import { Outfit, Geist, Geist_Mono } from 'next/font/google';
import './globals.css';
import { ThemeProvider } from '@/components/theme-provider';
import { ConnectionToast } from '@/components/common/ConnectionToast';
import { Sidebar } from '@/components/sidebar/Sidebar';

const geistSans = Geist({
  variable: '--font-geist-sans',
  subsets: ['latin'],
});

const geistMono = Geist_Mono({
  variable: '--font-geist-mono',
  subsets: ['latin'],
});

const outfit = Outfit({
  variable: '--font-outfit',
  subsets: ['latin'],
});

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const pathname = usePathname();

  // Automatically redirect from port 3000 to the Nginx gateway port 80
  React.useEffect(() => {
    if (typeof window !== 'undefined' && window.location.port === '3000') {
      const newUrl = window.location.protocol + '//' + window.location.hostname + window.location.pathname + window.location.search + window.location.hash;
      window.location.replace(newUrl);
    }
  }, []);

  // Hide sidebar on Auth pages (/login, /register, /)
  const isAuthPage = pathname === '/login' || pathname === '/register' || pathname === '/';

  return (
    <html lang="en" suppressHydrationWarning>
      <body className={`min-h-screen antialiased text-foreground bg-[#f8f9fc] ${outfit.className} ${outfit.variable} ${geistSans.variable} ${geistMono.variable}`}>
        <ThemeProvider attribute="class" defaultTheme="light" enableSystem={false}>
          {isAuthPage ? (
            // Auth Layout (No Sidebar)
            <div className="min-h-screen w-screen overflow-x-hidden bg-[#f8f9fc]">
              {children}
            </div>
          ) : (
            // App Layout (With Single Global Sidebar)
            <div className="flex h-screen w-screen overflow-hidden bg-[#f8f9fc]">
              <Sidebar />
              <main className="flex-1 flex flex-col h-full overflow-y-auto relative bg-[#f8f9fc]">
                {children}
              </main>
            </div>
          )}
          <ConnectionToast />
        </ThemeProvider>
      </body>
    </html>
  );
}
