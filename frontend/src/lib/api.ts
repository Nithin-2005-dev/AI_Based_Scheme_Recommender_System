/**
 * API client for communicating with the FastAPI backend.
 * Handles JWT token management, request/response interceptors.
 */

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface ApiOptions {
  method?: string;
  body?: unknown;
  headers?: Record<string, string>;
  requireAuth?: boolean;
}

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  private getToken(): string | null {
    if (typeof window === "undefined") return null;
    return localStorage.getItem("access_token");
  }

  private getRefreshToken(): string | null {
    if (typeof window === "undefined") return null;
    return localStorage.getItem("refresh_token");
  }

  setTokens(access: string, refresh: string) {
    if (typeof window === "undefined") return;
    localStorage.setItem("access_token", access);
    localStorage.setItem("refresh_token", refresh);
  }

  clearTokens() {
    if (typeof window === "undefined") return;
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    localStorage.removeItem("user");
  }

  private async refreshAccessToken(): Promise<boolean> {
    const refreshToken = this.getRefreshToken();
    if (!refreshToken) return false;

    try {
      const response = await fetch(`${this.baseUrl}/api/v1/auth/refresh`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh_token: refreshToken }),
      });

      if (!response.ok) return false;

      const data = await response.json();
      this.setTokens(data.access_token, data.refresh_token);
      return true;
    } catch {
      return false;
    }
  }

  async request<T>(endpoint: string, options: ApiOptions = {}): Promise<T> {
    const { method = "GET", body, headers = {}, requireAuth = true } = options;

    const requestHeaders: Record<string, string> = {
      "Content-Type": "application/json",
      ...headers,
    };

    if (requireAuth) {
      const token = this.getToken();
      if (token) {
        requestHeaders["Authorization"] = `Bearer ${token}`;
      }
    }

    let response = await fetch(`${this.baseUrl}${endpoint}`, {
      method,
      headers: requestHeaders,
      body: body ? JSON.stringify(body) : undefined,
    });

    // Handle 401 — try refreshing token
    if (response.status === 401 && requireAuth) {
      const refreshed = await this.refreshAccessToken();
      if (refreshed) {
        const newToken = this.getToken();
        requestHeaders["Authorization"] = `Bearer ${newToken}`;
        response = await fetch(`${this.baseUrl}${endpoint}`, {
          method,
          headers: requestHeaders,
          body: body ? JSON.stringify(body) : undefined,
        });
      } else {
        this.clearTokens();
        if (typeof window !== "undefined") {
          window.location.href = "/auth/login";
        }
        throw new Error("Session expired");
      }
    }

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: "Request failed" }));
      throw new Error(error.detail || `HTTP ${response.status}`);
    }

    return response.json();
  }

  // Auth
  async signup(data: { email: string; password: string; full_name: string }) {
    return this.request("/api/v1/auth/signup", { method: "POST", body: data, requireAuth: false });
  }

  async login(data: { email: string; password: string }) {
    return this.request<{
      access_token: string;
      refresh_token: string;
      user: Record<string, unknown>;
    }>("/api/v1/auth/login", { method: "POST", body: data, requireAuth: false });
  }

  async logout() {
    try {
      await this.request("/api/v1/auth/logout", { method: "POST" });
    } finally {
      this.clearTokens();
    }
  }

  async forgotPassword(email: string) {
    return this.request("/api/v1/auth/forgot-password", {
      method: "POST", body: { email }, requireAuth: false,
    });
  }

  async resetPassword(token: string, newPassword: string) {
    return this.request("/api/v1/auth/reset-password", {
      method: "POST", body: { token, new_password: newPassword }, requireAuth: false,
    });
  }

  // User Profile
  async getProfile() {
    return this.request("/api/v1/users/me");
  }

  async updateProfile(data: Record<string, unknown>) {
    return this.request("/api/v1/users/me", { method: "PUT", body: data });
  }

  // Schemes
  async getSchemes(params: Record<string, string | number> = {}) {
    const searchParams = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== null && v !== "") searchParams.set(k, String(v));
    });
    return this.request(`/api/v1/schemes?${searchParams}`, { requireAuth: false });
  }

  async getScheme(slug: string) {
    return this.request(`/api/v1/schemes/${slug}`, { requireAuth: false });
  }

  async getCategories() {
    return this.request("/api/v1/schemes/categories", { requireAuth: false });
  }

  async getPopularSchemes(limit = 10) {
    return this.request(`/api/v1/schemes/popular?limit=${limit}`, { requireAuth: false });
  }

  async saveScheme(schemeId: number) {
    return this.request("/api/v1/schemes/save", { method: "POST", body: { scheme_id: schemeId } });
  }

  async getSavedSchemes() {
    return this.request("/api/v1/schemes/saved/list");
  }

  async getApplications() {
    return this.request("/api/v1/schemes/applications/list");
  }

  async startApplication(schemeId: number) {
    return this.request(`/api/v1/schemes/apply/${schemeId}`, { method: "POST" });
  }

  // Recommendations
  async getRecommendations(topK = 5) {
    return this.request(`/api/v1/recommendations?top_k=${topK}`);
  }

  // Eligibility — Full dashboard
  async getFullEligibility(params: Record<string, string | number> = {}) {
    const searchParams = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== null && v !== "") searchParams.set(k, String(v));
    });
    return this.request(`/api/v1/eligibility?${searchParams}`);
  }

  async getEligibleSchemes(params: Record<string, string | number> = {}) {
    const searchParams = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== null && v !== "") searchParams.set(k, String(v));
    });
    return this.request(`/api/v1/eligibility/eligible?${searchParams}`);
  }

  async getIneligibleSchemes(params: Record<string, string | number> = {}) {
    const searchParams = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== null && v !== "") searchParams.set(k, String(v));
    });
    return this.request(`/api/v1/eligibility/ineligible?${searchParams}`);
  }

  // Eligibility — Single scheme
  async checkEligibility(schemeId: number) {
    return this.request(`/api/v1/eligibility/check/${schemeId}`);
  }

  // Search
  async search(params: Record<string, string | number> = {}) {
    const searchParams = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== null && v !== "") searchParams.set(k, String(v));
    });
    return this.request(`/api/v1/search?${searchParams}`, { requireAuth: false });
  }

  async autocomplete(query: string) {
    return this.request(`/api/v1/search/autocomplete?q=${encodeURIComponent(query)}`, { requireAuth: false });
  }

  // Notifications
  async getNotifications(page = 1) {
    return this.request(`/api/v1/notifications?page=${page}`);
  }

  async getUnreadCount() {
    return this.request<{ unread_count: number }>("/api/v1/notifications/unread-count");
  }

  async markNotificationRead(id: number) {
    return this.request(`/api/v1/notifications/${id}/read`, { method: "PUT" });
  }

  async markAllNotificationsRead() {
    return this.request("/api/v1/notifications/read-all", { method: "PUT" });
  }

  async deleteNotification(id: number) {
    return this.request(`/api/v1/notifications/${id}`, { method: "DELETE" });
  }

  // Chatbot
  async askChatbot(message: string, sessionId?: string, language: string = "en") {
    return this.request("/api/v1/chatbot", {
      method: "POST",
      body: { message, session_id: sessionId, language },
    });
  }

  async getChatbotLanguages() {
    return this.request<{ languages: { code: string; name: string }[] }>("/api/v1/chatbot/languages");
  }

  async getChatHistory(sessionId: string) {
    return this.request(`/api/v1/chatbot/history/${sessionId}`);
  }

  // Analytics (admin)
  async getAnalyticsDashboard() {
    return this.request("/api/v1/analytics/dashboard");
  }

  // Admin
  async getAdminUsers(page = 1, search = "") {
    return this.request(`/api/v1/admin/users?page=${page}&search=${search}`);
  }

  async sendAdminNotification(data: Record<string, unknown>) {
    return this.request("/api/v1/admin/notifications/send", { method: "POST", body: data });
  }

  // Translation
  async getLanguages() {
    return this.request("/api/v1/translate/languages", { requireAuth: false });
  }

  async getUITranslations(language: string) {
    return this.request(`/api/v1/translate/ui/${language}`, { requireAuth: false });
  }

  async translateText(text: string, targetLang: string) {
    return this.request("/api/v1/translate", {
      method: "POST",
      body: { text, target_language: targetLang },
      requireAuth: false,
    });
  }
}

export const api = new ApiClient(API_URL);
export default api;
