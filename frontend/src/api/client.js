import axios from "axios";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000/api",
});

// Attach JWT token only when needed
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("accessToken");

  // Prevent sending token for login/register
  const isAuthFree =
    config.url.includes("/auth/login") ||
    config.url.includes("/auth/register") ||
    config.url.includes("/auth/google");

  if (token && !isAuthFree) {
    config.headers.Authorization = `Bearer ${token}`;
  }

  return config;
});

export const analyzeQuery = async (query) => {
  const res = await api.post("/analyze/", { query });
  return res.data;
};

export const uploadDataset = async (file) => {
  const formData = new FormData();
  formData.append("file", file);
  const res = await api.post("/dataset/upload/", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return res.data;
};

export const fetchMyHistory = async () => {
  const res = await api.get("/history/my/");
  return res.data;
};

export const fetchUserHistoryAdmin = async (userId) => {
  const res = await api.get(`/history/admin/${userId}/`);
  return res.data;
};

// Auth APIs
export const registerUser = async (payload) => await api.post("/auth/register/", payload).then(res => res.data);
export const loginUser = async (payload) => await api.post("/auth/login/", payload).then(res => res.data);
export const fetchMe = async () => await api.get("/auth/me/").then(res => res.data);

export const fetchAdminUsers = async () => await api.get("/auth/admin/users/").then(res => res.data);
export const changeUserRole = async (userId, role, password) => await api.post(`/auth/admin/users/${userId}/role/`, { role, password }).then(res => res.data);
export const deleteUserAdmin = async (userId, password) => await api.post(`/auth/admin/users/${userId}/delete/`, { password }).then(res => res.data);

export const exportAllHistoryAdmin = async () => await api.get("/history/export-all/").then(res => res.data);

export default api;
