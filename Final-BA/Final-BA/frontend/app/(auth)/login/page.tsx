'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { Mail, Lock, Eye, EyeOff, Sparkles, Cpu, Zap, Share2 } from 'lucide-react';
import { FaMicrosoft, FaGoogle } from 'react-icons/fa';

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState('sarah.m@claritydental.com');
  const [password, setPassword] = useState('••••••••••••');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !password) {
      setError('Please enter your email and password');
      return;
    }
    localStorage.setItem('auth_token', 'mock_session_token');
    router.push('/dashboard');
  };

  const handleSocialLogin = () => {
    localStorage.setItem('auth_token', 'mock_session_token');
    router.push('/dashboard');
  };

  return (
    <div className="min-h-screen w-full flex bg-[#f8f9fc] font-sans antialiased text-[#111827]">
      
      {/* LEFT PANEL: Hero Gradient & Feature Highlights */}
      <div className="hidden lg:flex flex-col justify-between w-[55%] p-12 lg:p-16 relative overflow-hidden bg-gradient-to-br from-[#ff5733] via-[#1d123d] to-[#0d0f22] text-white">
        
        {/* Top Logo */}
        <div className="flex items-center gap-3 z-10">
          <div className="w-9 h-9 rounded-2xl bg-white/10 border border-white/20 flex items-center justify-center shrink-0 shadow-lg backdrop-blur-md">
            <Sparkles className="w-5 h-5 text-white fill-white" />
          </div>
          <span className="text-xl font-extrabold text-white tracking-tight">
            StoryForge AI
          </span>
        </div>

        {/* Hero Headline & Subtitle */}
        <div className="max-w-xl space-y-6 z-10 my-auto py-12">
          <h1 className="text-4xl lg:text-5xl font-extrabold text-white leading-tight tracking-tight">
            Transform Requirements into User Stories with AI
          </h1>
          <p className="text-sm text-gray-300 leading-relaxed max-w-lg">
            Save hundreds of hours of manual mapping. Upload business requirement documents and watch them turn into beautifully formatted Agile artifacts instantly.
          </p>
        </div>

        {/* 3 Feature Bullet Cards at Bottom Left */}
        <div className="grid grid-cols-1 gap-4 z-10 max-w-lg">
          <div className="flex items-start gap-3.5 p-3.5 rounded-2xl bg-white/5 border border-white/10 backdrop-blur-md">
            <div className="w-8 h-8 rounded-xl bg-white/10 flex items-center justify-center shrink-0 text-white mt-0.5">
              <Cpu className="w-4 h-4" />
            </div>
            <div>
              <h4 className="text-xs font-bold text-white">AI-Powered Analysis</h4>
              <p className="text-[11px] text-gray-300 leading-snug">Automatic identification of actors, functional scope, and edge cases.</p>
            </div>
          </div>

          <div className="flex items-start gap-3.5 p-3.5 rounded-2xl bg-white/5 border border-white/10 backdrop-blur-md">
            <div className="w-8 h-8 rounded-xl bg-white/10 flex items-center justify-center shrink-0 text-white mt-0.5">
              <Zap className="w-4 h-4" />
            </div>
            <div>
              <h4 className="text-xs font-bold text-white">Instant Story Generation</h4>
              <p className="text-[11px] text-gray-300 leading-snug">Agile user stories mapped complete with comprehensive acceptance criteria.</p>
            </div>
          </div>

          <div className="flex items-start gap-3.5 p-3.5 rounded-2xl bg-white/5 border border-white/10 backdrop-blur-md">
            <div className="w-8 h-8 rounded-xl bg-white/10 flex items-center justify-center shrink-0 text-white mt-0.5">
              <Share2 className="w-4 h-4" />
            </div>
            <div>
              <h4 className="text-xs font-bold text-white">Enterprise Export</h4>
              <p className="text-[11px] text-gray-300 leading-snug">One-click synchronization with Jira, Azure DevOps, or clean CSV formats.</p>
            </div>
          </div>
        </div>

        {/* Ambient Glow Orbs */}
        <div className="absolute -top-32 -left-32 w-96 h-96 rounded-full bg-[#ff5733]/20 blur-3xl pointer-events-none" />
        <div className="absolute -bottom-32 -right-32 w-96 h-96 rounded-full bg-purple-600/20 blur-3xl pointer-events-none" />
      </div>

      {/* RIGHT PANEL: Auth Card Form */}
      <div className="flex-1 flex flex-col justify-center items-center p-6 md:p-12 relative">
        
        {/* Mobile Header Logo */}
        <div className="lg:hidden flex items-center gap-3 mb-8">
          <div className="w-8 h-8 rounded-xl bg-[#ff5733] flex items-center justify-center text-white font-bold">
            ✦
          </div>
          <span className="text-lg font-extrabold text-gray-900">StoryForge AI</span>
        </div>

        <div className="w-full max-w-md bg-white border border-gray-200/80 rounded-3xl p-8 md:p-10 shadow-2xl space-y-6">
          
          {/* Header */}
          <div className="space-y-1">
            <h2 className="text-2xl font-bold text-gray-900 tracking-tight">Welcome back</h2>
            <p className="text-xs text-gray-500">Enter your credentials to access your workspaces</p>
          </div>

          {error && (
            <div className="bg-red-50 text-red-600 text-xs p-3 rounded-xl border border-red-200 text-center font-medium">
              {error}
            </div>
          )}

          <form onSubmit={handleLogin} className="space-y-4">
            
            {/* Email Address */}
            <div className="space-y-1.5">
              <label className="text-xs font-bold text-gray-700 block">Email Address</label>
              <div className="relative">
                <Mail className="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-400" />
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="sarah.m@claritydental.com"
                  className="w-full bg-gray-50/60 border border-gray-200 rounded-xl pl-10 pr-4 py-2.5 text-xs text-gray-900 focus:outline-none focus:ring-2 focus:ring-[#ff5733]"
                  required
                />
              </div>
            </div>
            
            {/* Password */}
            <div className="space-y-1.5">
              <div className="flex items-center justify-between">
                <label className="text-xs font-bold text-gray-700">Password</label>
                <a href="#" className="text-xs font-semibold text-[#ff5733] hover:underline">Forgot password?</a>
              </div>
              <div className="relative">
                <Lock className="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-400" />
                <input
                  type={showPassword ? "text" : "password"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••••••"
                  className="w-full bg-gray-50/60 border border-gray-200 rounded-xl pl-10 pr-12 py-2.5 text-xs text-gray-900 focus:outline-none focus:ring-2 focus:ring-[#ff5733]"
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3.5 top-1/2 -translate-y-1/2 text-xs font-semibold text-gray-400 hover:text-gray-600"
                >
                  {showPassword ? "Hide" : "Show"}
                </button>
              </div>
            </div>

            {/* Sign In CTA Button */}
            <button 
              type="submit" 
              className="w-full py-3 bg-[#ff5733] hover:bg-[#e04826] text-white text-xs font-extrabold rounded-xl shadow-[0_4px_16px_rgba(255,87,51,0.35)] transition-all duration-200 cursor-pointer mt-2"
            >
              Sign In
            </button>
          </form>

          {/* Social Divider */}
          <div className="relative flex items-center justify-center my-4">
            <span className="absolute w-full border-t border-gray-100" />
            <span className="relative bg-white px-3 text-[11px] text-gray-400 font-medium">or continue with</span>
          </div>

          {/* Social Logins */}
          <div className="space-y-3">
            <button 
              type="button"
              onClick={handleSocialLogin}
              className="w-full flex items-center justify-center gap-2 bg-white hover:bg-gray-50 border border-gray-200 text-gray-800 text-xs font-bold py-2.5 rounded-xl transition-colors cursor-pointer shadow-sm"
            >
              <FaMicrosoft className="w-4 h-4 text-blue-500" />
              Sign in with Microsoft
            </button>

            <button 
              type="button"
              onClick={handleSocialLogin}
              className="w-full flex items-center justify-center gap-2 bg-white hover:bg-gray-50 border border-gray-200 text-gray-800 text-xs font-bold py-2.5 rounded-xl transition-colors cursor-pointer shadow-sm"
            >
              <FaGoogle className="w-4 h-4 text-red-500" />
              Sign in with Google
            </button>
          </div>

          {/* Sign Up Footer */}
          <div className="text-center text-xs text-gray-500 pt-2">
            Don't have an account? <Link href="/register" className="text-[#ff5733] font-bold hover:underline">Sign Up</Link>
          </div>

        </div>

      </div>

    </div>
  );
}
