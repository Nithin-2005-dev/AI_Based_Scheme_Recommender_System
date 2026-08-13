"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import api from "@/lib/api";

interface DashboardData {
  stats: {
    total_users: number;
    total_schemes: number;
    total_central: number;
    total_state: number;
    total_categories: number;
    total_notifications_sent: number;
    total_applications: number;
    active_users_today: number;
  };
  popular_schemes: { scheme_name: string; slug: string; view_count: number; application_count: number; category: string }[];
  category_distribution: { category: string; count: number; percentage: number }[];
  notification_stats: { total: number; read: number; unread: number; read_rate: number };
  monthly_signups: { month: string; count: number }[];
}

export default function AdminPage() {
  const router = useRouter();
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState("overview");
  const [users, setUsers] = useState<Record<string, unknown>[]>([]);
  const [userSearch, setUserSearch] = useState("");

  // Notification form
  const [notifTitle, setNotifTitle] = useState("");
  const [notifMessage, setNotifMessage] = useState("");
  const [notifSending, setNotifSending] = useState(false);
  const [notifResult, setNotifResult] = useState("");

  useEffect(() => {
    const stored = localStorage.getItem("user");
    if (!stored) { router.push("/auth/login"); return; }
    const user = JSON.parse(stored);
    if (user.role !== "admin") { router.push("/dashboard"); return; }
    loadDashboard();
  }, [router]);

  const loadDashboard = async () => {
    try {
      const dashData = await api.getAnalyticsDashboard() as DashboardData;
      setData(dashData);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const loadUsers = async () => {
    try {
      const result = await api.getAdminUsers(1, userSearch) as { users: Record<string, unknown>[] };
      setUsers(result.users || []);
    } catch (err) {
      console.error(err);
    }
  };

  const sendNotification = async () => {
    if (!notifTitle || !notifMessage) return;
    setNotifSending(true);
    try {
      const result = await api.sendAdminNotification({
        title: notifTitle,
        message: notifMessage,
        notification_type: "system",
        priority: "normal",
      }) as { message: string };
      setNotifResult(result.message);
      setNotifTitle("");
      setNotifMessage("");
    } catch (err) {
      setNotifResult("Failed to send notification");
    } finally {
      setNotifSending(false);
    }
  };

  useEffect(() => {
    if (activeTab === "users") loadUsers();
  }, [activeTab, userSearch]);

  if (loading) {
    return <div style={{ minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center" }}><p>Loading admin dashboard...</p></div>;
  }

  const stats = data?.stats;

  return (
    <div>
      <nav className="nav">
        <div className="nav-inner">
          <Link href="/" className="nav-logo"><span style={{ fontSize: "1.5rem" }}>🏛️</span><span>Admin Panel</span></Link>
          <div className="nav-links">
            <Link href="/admin" className="nav-link active">Dashboard</Link>
            <Link href="/schemes" className="nav-link">Schemes</Link>
            <Link href="/dashboard" className="nav-link">User View</Link>
          </div>
        </div>
      </nav>

      <div className="container page">
        <h1 style={{ marginBottom: "2rem" }}>📊 Admin Dashboard</h1>

        {/* Tabs */}
        <div style={{ display: "flex", gap: "0.25rem", marginBottom: "2rem", borderBottom: "2px solid var(--border)" }}>
          {[
            { id: "overview", label: "📊 Overview" },
            { id: "users", label: "👥 Users" },
            { id: "notifications", label: "📢 Send Notification" },
          ].map((tab) => (
            <button key={tab.id} onClick={() => setActiveTab(tab.id)} className="btn btn-ghost"
              style={{
                borderBottom: activeTab === tab.id ? "2px solid var(--primary)" : "2px solid transparent",
                borderRadius: 0, color: activeTab === tab.id ? "var(--primary)" : "var(--text-muted)",
                fontWeight: activeTab === tab.id ? 700 : 500,
              }}>
              {tab.label}
            </button>
          ))}
        </div>

        {/* Overview Tab */}
        {activeTab === "overview" && stats && (
          <div className="animate-fade-in">
            <div className="grid-stats" style={{ marginBottom: "2rem" }}>
              {[
                { value: stats.total_users, label: "Total Users", icon: "👥" },
                { value: stats.total_schemes, label: "Total Schemes", icon: "📋" },
                { value: stats.total_central, label: "Central Schemes", icon: "🏛️" },
                { value: stats.total_state, label: "State Schemes", icon: "🗺️" },
                { value: stats.total_categories, label: "Categories", icon: "📂" },
                { value: stats.active_users_today, label: "Active Today", icon: "🟢" },
                { value: stats.total_applications, label: "Applications", icon: "📝" },
                { value: stats.total_notifications_sent, label: "Notifications", icon: "🔔" },
              ].map((s, i) => (
                <div key={i} className="stat-card">
                  <div style={{ fontSize: "1.25rem" }}>{s.icon}</div>
                  <div className="stat-value">{s.value.toLocaleString()}</div>
                  <div className="stat-label">{s.label}</div>
                </div>
              ))}
            </div>

            {/* Popular Schemes */}
            <div className="card" style={{ marginBottom: "2rem" }}>
              <h3 style={{ marginBottom: "1rem" }}>🔥 Most Popular Schemes</h3>
              <div style={{ overflowX: "auto" }}>
                <table style={{ width: "100%", borderCollapse: "collapse" }}>
                  <thead>
                    <tr style={{ borderBottom: "2px solid var(--border)" }}>
                      <th style={{ textAlign: "left", padding: "0.75rem", fontSize: "0.8125rem", color: "var(--text-muted)" }}>#</th>
                      <th style={{ textAlign: "left", padding: "0.75rem", fontSize: "0.8125rem", color: "var(--text-muted)" }}>Scheme</th>
                      <th style={{ textAlign: "left", padding: "0.75rem", fontSize: "0.8125rem", color: "var(--text-muted)" }}>Category</th>
                      <th style={{ textAlign: "right", padding: "0.75rem", fontSize: "0.8125rem", color: "var(--text-muted)" }}>Views</th>
                      <th style={{ textAlign: "right", padding: "0.75rem", fontSize: "0.8125rem", color: "var(--text-muted)" }}>Applications</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data?.popular_schemes.slice(0, 10).map((s, i) => (
                      <tr key={i} style={{ borderBottom: "1px solid var(--border)" }}>
                        <td style={{ padding: "0.75rem", fontSize: "0.875rem" }}>{i + 1}</td>
                        <td style={{ padding: "0.75rem", fontSize: "0.875rem" }}>
                          <Link href={`/schemes/${s.slug}`} style={{ color: "var(--primary-light)", textDecoration: "none" }}>
                            {s.scheme_name.substring(0, 60)}
                          </Link>
                        </td>
                        <td style={{ padding: "0.75rem" }}>
                          <span className="badge badge-warning" style={{ fontSize: "0.6875rem" }}>
                            {(s.category || "").split(",")[0].trim().substring(0, 20)}
                          </span>
                        </td>
                        <td style={{ padding: "0.75rem", textAlign: "right", fontWeight: 600 }}>{s.view_count}</td>
                        <td style={{ padding: "0.75rem", textAlign: "right", fontWeight: 600 }}>{s.application_count}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Category Distribution */}
            <div className="card">
              <h3 style={{ marginBottom: "1rem" }}>📂 Category Distribution</h3>
              <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
                {data?.category_distribution.slice(0, 10).map((cat, i) => (
                  <div key={i}>
                    <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.875rem", marginBottom: "0.25rem" }}>
                      <span>{cat.category}</span>
                      <span style={{ color: "var(--text-muted)" }}>{cat.count} ({cat.percentage}%)</span>
                    </div>
                    <div className="progress-bar">
                      <div className="progress-bar-fill eligible" style={{ width: `${Math.min(cat.percentage * 2, 100)}%` }} />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Users Tab */}
        {activeTab === "users" && (
          <div className="animate-fade-in">
            <div style={{ marginBottom: "1.5rem" }}>
              <input className="input" style={{ maxWidth: "400px" }} placeholder="Search users by email..." value={userSearch}
                onChange={(e) => setUserSearch(e.target.value)} />
            </div>
            <div className="card">
              <table style={{ width: "100%", borderCollapse: "collapse" }}>
                <thead>
                  <tr style={{ borderBottom: "2px solid var(--border)" }}>
                    <th style={{ textAlign: "left", padding: "0.75rem", fontSize: "0.8125rem", color: "var(--text-muted)" }}>User</th>
                    <th style={{ textAlign: "left", padding: "0.75rem", fontSize: "0.8125rem", color: "var(--text-muted)" }}>Role</th>
                    <th style={{ textAlign: "left", padding: "0.75rem", fontSize: "0.8125rem", color: "var(--text-muted)" }}>State</th>
                    <th style={{ textAlign: "left", padding: "0.75rem", fontSize: "0.8125rem", color: "var(--text-muted)" }}>Verified</th>
                    <th style={{ textAlign: "left", padding: "0.75rem", fontSize: "0.8125rem", color: "var(--text-muted)" }}>Joined</th>
                  </tr>
                </thead>
                <tbody>
                  {users.map((u, i) => (
                    <tr key={i} style={{ borderBottom: "1px solid var(--border)" }}>
                      <td style={{ padding: "0.75rem" }}>
                        <div style={{ fontWeight: 600, fontSize: "0.875rem" }}>{u.full_name as string || "—"}</div>
                        <div style={{ fontSize: "0.8125rem", color: "var(--text-muted)" }}>{u.email as string}</div>
                      </td>
                      <td style={{ padding: "0.75rem" }}>
                        <span className={`badge ${u.role === "admin" ? "badge-error" : "badge-primary"}`}>{u.role as string}</span>
                      </td>
                      <td style={{ padding: "0.75rem", fontSize: "0.875rem" }}>{u.state as string || "—"}</td>
                      <td style={{ padding: "0.75rem" }}>{u.is_email_verified ? "✅" : "❌"}</td>
                      <td style={{ padding: "0.75rem", fontSize: "0.8125rem", color: "var(--text-muted)" }}>
                        {u.created_at ? new Date(u.created_at as string).toLocaleDateString() : "—"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Send Notification Tab */}
        {activeTab === "notifications" && (
          <div className="animate-fade-in" style={{ maxWidth: "600px" }}>
            <div className="card">
              <h3 style={{ marginBottom: "1.5rem" }}>📢 Send Notification to All Users</h3>
              <div style={{ marginBottom: "1.25rem" }}>
                <label className="label">Title</label>
                <input className="input" placeholder="Notification title" value={notifTitle} onChange={(e) => setNotifTitle(e.target.value)} />
              </div>
              <div style={{ marginBottom: "1.25rem" }}>
                <label className="label">Message</label>
                <textarea className="input" rows={4} placeholder="Write your notification message..." value={notifMessage}
                  onChange={(e) => setNotifMessage(e.target.value)}
                  style={{ resize: "vertical" }} />
              </div>
              <button onClick={sendNotification} className="btn btn-primary" disabled={notifSending || !notifTitle || !notifMessage}>
                {notifSending ? "Sending..." : "Send to All Users"}
              </button>
              {notifResult && (
                <div style={{
                  marginTop: "1rem", padding: "0.75rem", borderRadius: "var(--radius-sm)",
                  background: notifResult.includes("Failed") ? "#fef2f2" : "#ecfdf5",
                  color: notifResult.includes("Failed") ? "var(--error)" : "var(--success)",
                  fontSize: "0.875rem",
                }}>
                  {notifResult}
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
