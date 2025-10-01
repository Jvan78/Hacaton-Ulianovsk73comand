import React, { useState } from "react";
import { uploadFile, importFromUpload } from "../api";
import { useNavigate } from "react-router-dom";

export default function AdminPanel(){
  const [file, setFile] = useState(null);
  const [msg, setMsg] = useState("");
  const nav = useNavigate();

  const doUpload = async () => {
    if (!file) return setMsg("Выберите файл");
    setMsg("Загружаю...");
    try {
      const resp = await uploadFile(file);
      setMsg(`Uploaded: ${resp.data.path || JSON.stringify(resp.data)}`);
    } catch (e) {
      setMsg("Upload failed: " + (e?.response?.data?.detail || e.message));
    }
  };

  const doImport = async () => {
    setMsg("Запуск импорта...");
    try {
      const resp = await importFromUpload();
      setMsg("Import: " + JSON.stringify(resp.data));
    } catch (e) {
      setMsg("Import failed: " + (e?.response?.data?.detail || e.message));
    }
  };

  return (
    <div style={{ padding: 20 }}>
      <h2>Admin Panel</h2>
      <div>
        <input type="file" accept=".ndjson,.json" onChange={e=>setFile(e.target.files[0])} />
        <button onClick={doUpload} style={{marginLeft:10}}>Upload to API</button>
      </div>
      <div style={{marginTop:10}}>
        <button onClick={doImport}>Run import_from_upload</button>
      </div>
      <div style={{marginTop:10, color:"green"}}>{msg}</div>
      <div style={{marginTop:20}}>
        <button onClick={() => { localStorage.removeItem("bas_auth"); nav("/login"); }}>Logout</button>
      </div>
    </div>
  );
}
