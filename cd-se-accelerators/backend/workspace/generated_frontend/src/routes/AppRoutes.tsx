import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import MainLayout from '../layouts/MainLayout';
import Login from '../pages/Login';
import SignUp from '../pages/SignUp';
import Dashboard from '../pages/Dashboard';

export default function AppRoutes() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/signup" element={<SignUp />} />
        <Route element={<MainLayout />}>
          <Route path="/dashboard" element={<Dashboard />} />
        </Route>
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
