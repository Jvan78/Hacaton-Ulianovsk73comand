// src/components/Header.jsx
import React from "react";
import { Link, useNavigate } from "react-router-dom";

function getUser() {
  try { return JSON.parse(localStorage.getItem("bas_auth") || "{}"); }
  catch { return {}; }
}

export default function Header() {
  const user = getUser();
  const nav = useNavigate();

  const logout = () => {
    localStorage.removeItem("bas_auth");
    nav("/dashboard");
    // force reload to update UI if needed:
    window.location.reload();
  };

  return (
    <header style={{
      display: "flex", justifyContent: "space-between", alignItems: "center",
      padding: "10px 20px", borderBottom: "1px solid #eee", marginBottom: 12
    }}>
      <div>
        <Link to="/dashboard" style={{ textDecoration: "none", color: "#333", fontWeight: "600" }}>
          BAS Analytics
        </Link>
      </div>

      <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
        {/* Если админ — показываем кнопку загрузки */}
        {user && user.role === "admin" ? (
          <>
            <Link to="/admin"><button>Загрузить данные</button></Link>
            <button onClick={logout}>Выйти ({user.username || "admin"})</button>
          </>
        ) : (
          <>
            {/* Гость: кнопка Войти */}
            <Link to="/login"><button>Войти</button></Link>
          </>
        )}
      </div>
    </header>
  );
}
