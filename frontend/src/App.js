// src/App.js
import React from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import LoginPage from "./pages/LoginPage";
import AdminPanel from "./pages/AdminPanel";
import UserDashboard from "./pages/UserDashboard";
import ProtectedRoute from "./components/ProtectedRoute";
import Header from "./components/Header";

export default function App() {
  return (
    <div>
      <Header />
      <Routes>
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route path="/login" element={<LoginPage />} />

        {/* Public dashboard */}
        <Route path="/dashboard" element={<UserDashboard />} />

        {/* Admin protected */}
        <Route path="/admin" element={
          <ProtectedRoute requireRole="admin">
            <AdminPanel />
          </ProtectedRoute>
        } />

        <Route path="*" element={<div>Not found</div>} />
      </Routes>
    </div>
  );
}
