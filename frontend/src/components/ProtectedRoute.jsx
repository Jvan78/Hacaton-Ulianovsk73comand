// src/components/ProtectedRoute.jsx
import React from "react";
import { Navigate } from "react-router-dom";

function getUser() {
  try { return JSON.parse(localStorage.getItem("bas_auth") || "{}"); }
  catch { return {}; }
}

/**
 * props:
 * - children
 * - requireRole (optional): 'admin' или 'user'
 */
export default function ProtectedRoute({ children, requireRole }) {
  const user = getUser();
  if (!user || !user.token) return <Navigate to="/login" replace />;
  if (requireRole && user.role !== requireRole) {
    return <div style={{ padding: 20 }}>Доступ запрещён — требуется роль: {requireRole}</div>;
  }
  return children;
}
