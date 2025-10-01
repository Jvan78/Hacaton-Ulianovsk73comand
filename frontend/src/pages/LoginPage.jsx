import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { loginWithCredentials } from "../api";

export default function LoginPage() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [tokenManual, setTokenManual] = useState("");
  const [error, setError] = useState("");
  const nav = useNavigate();

  const submitCreds = async (e) => {
    e.preventDefault();
    try {
      const resp = await loginWithCredentials(username, password);
      const token = resp.data.access_token || resp.data.token || "";
      // backend может возвращать {access_token, token_type}
      const role = resp.data.role || "admin"; // fallback
      localStorage.setItem("bas_auth", JSON.stringify({ token, role, username }));
      nav("/dashboard");
    } catch (err) {
      setError(err?.response?.data?.detail || err.message || "Login failed");
    }
  };

  const useManualToken = (e) => {
    e.preventDefault();
    if (!tokenManual) { setError("Введите токен"); return; }
    // для простоты считаем, что тот кто вводит токен — admin
    localStorage.setItem("bas_auth", JSON.stringify({ token: tokenManual, role: "admin", username: "admin" }));
    nav("/admin");
  };

  return (
    <div style={{ padding: 20 }}>
      <h2>Login</h2>
      <form onSubmit={submitCreds} style={{ marginBottom: 20 }}>
        <div>
          <label>Username</label><br/>
          <input value={username} onChange={e=>setUsername(e.target.value)} />
        </div>
        <div>
          <label>Password</label><br/>
          <input type="password" value={password} onChange={e=>setPassword(e.target.value)} />
        </div>
        <button type="submit">Login</button>
      </form>

      <hr/>

      <h3>Или использовать admin token</h3>
      <form onSubmit={useManualToken}>
        <div>
          <label>Admin token</label><br/>
          <input value={tokenManual} onChange={e=>setTokenManual(e.target.value)} placeholder="вставьте supersecret123" style={{width: 400}} />
        </div>
        <button type="submit">Use token</button>
      </form>

      {error && <div style={{color:"red", marginTop:10}}>{error}</div>}
    </div>
  );
}
