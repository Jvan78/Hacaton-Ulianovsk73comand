import axios from "axios";

const api = axios.create({
  baseURL: "", // proxy в package.json проксирует к http://localhost:8000
  timeout: 30000,
});

// добавляем токен из localStorage автоматически
api.interceptors.request.use(config => {
  const auth = localStorage.getItem("bas_auth");
  if (auth) {
    try {
      const { token } = JSON.parse(auth);
      if (token) config.headers["Authorization"] = `Bearer ${token}`;
    } catch (e) {}
  }
  return config;
});

export const loginWithCredentials = async (username, password) => {
  // если backend /login есть, можно использовать:
  const form = new URLSearchParams();
  form.append("username", username);
  form.append("password", password);
  return api.post("/login", form, { headers: { "Content-Type": "application/x-www-form-urlencoded" }});
};

export const topRegions = (params = {}) => api.get("/api/v1/top-regions", { params });
export const listFlights = (params = {}) => api.get("/api/v1/flights", { params });
export const uploadFile = (file) => {
  const fd = new FormData();
  fd.append("file", file);
  return api.post("/api/v1/upload", fd, { headers: { "Content-Type": "multipart/form-data" }});
};
export const importFromUpload = () => api.post("/api/v1/import_from_upload");

export default api;
