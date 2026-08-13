"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import api from "@/lib/api";

interface NotificationItem {
  id: number;
  title: string;
  message: string;
  notification_type: string;
  channel: string;
  priority: string;
  scheme_name: string | null;
  scheme_id: number | null;
  is_read: boolean;
  change_details: Record<string, unknown> | null;
  created_at: string;
}

export default function NotificationsPage() {
  const router = useRouter();
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const [total, setTotal] = useState(0);
  const [unreadCount, setUnreadCount] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<"all" | "unread">("all");

  useEffect(() => {
    const token = localStorage.getItem("access_token");
    if (!token) { router.push("/auth/login"); return; }
    loadNotifications();
  }, [page, filter, router]);

  const loadNotifications = async () => {
    setLoading(true);
    try {
      const data = await api.getNotifications(page) as {
        notifications: NotificationItem[];
        total: number;
        unread_count: number;
      };
      let items = data.notifications || [];
      if (filter === "unread") items = items.filter((n) => !n.is_read);
      setNotifications(items);
      setTotal(data.total || 0);
      setUnreadCount(data.unread_count || 0);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const markRead = async (id: number) => {
    try {
      await api.markNotificationRead(id);
      setNotifications(prev => prev.map(n => n.id === id ? { ...n, is_read: true } : n));
      setUnreadCount(prev => Math.max(0, prev - 1));
    } catch (err) {
      console.error(err);
    }
  };

  const markAllRead = async () => {
    try {
      await api.markAllNotificationsRead();
      setNotifications(prev => prev.map(n => ({ ...n, is_read: true })));
      setUnreadCount(0);
    } catch (err) {
      console.error(err);
    }
  };

  const deleteNotification = async (id: number) => {
    try {
      await api.deleteNotification(id);
      setNotifications(prev => prev.filter(n => n.id !== id));
      setTotal(prev => prev - 1);
    } catch (err) {
      console.error(err);
    }
  };

  const getIcon = (type: string) => {
    switch (type) {
      case "rule_change": return "📝";
      case "deadline": return "⏰";
      case "recommendation": return "🎯";
      case "new_scheme": return "🆕";
      case "eligibility_update": return "✅";
      case "system": return "📢";
      default: return "🔔";
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case "urgent": return "var(--error)";
      case "high": return "#f59e0b";
      case "normal": return "var(--primary-light)";
      default: return "var(--text-muted)";
    }
  };

  const getTypeBadge = (type: string) => {
    switch (type) {
      case "rule_change": return { label: "Rule Change", cls: "badge-warning" };
      case "deadline": return { label: "Deadline", cls: "badge-error" };
      case "recommendation": return { label: "Recommendation", cls: "badge-primary" };
      case "new_scheme": return { label: "New Scheme", cls: "badge-success" };
      case "eligibility_update": return { label: "Eligibility", cls: "badge-primary" };
      default: return { label: type.replace("_", " "), cls: "badge-primary" };
    }
  };

  return (
    <div>
      <nav className="nav">
        <div className="nav-inner">
          <Link href="/" className="nav-logo"><span style={{ fontSize: "1.5rem" }}>🏛️</span><span>GovScheme AI</span></Link>
          <div className="nav-links">
            <Link href="/dashboard" className="nav-link">Dashboard</Link>
            <Link href="/schemes" className="nav-link">Schemes</Link>
            <Link href="/eligibility" className="nav-link">Eligibility</Link>
            <Link href="/chatbot" className="nav-link">AI Chat</Link>
            <Link href="/notifications" className="nav-link active" style={{ position: "relative" }}>
              🔔
              {unreadCount > 0 && (
                <span style={{
                  position: "absolute", top: "-2px", right: "-8px", minWidth: "18px", height: "18px",
                  background: "var(--error)", borderRadius: "var(--radius-full)", fontSize: "0.6875rem",
                  color: "white", display: "flex", alignItems: "center", justifyContent: "center",
                  fontWeight: 700, padding: "0 4px",
                }}>{unreadCount}</span>
              )}
            </Link>
            <Link href="/profile" className="nav-link">Profile</Link>
          </div>
        </div>
      </nav>

      <div className="container page" style={{ maxWidth: "800px" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "2rem" }}>
          <div>
            <h1>🔔 Notifications</h1>
            <p style={{ color: "var(--text-secondary)" }}>
              {unreadCount} unread · {total} total
            </p>
          </div>
          <div style={{ display: "flex", gap: "0.75rem" }}>
            <div style={{ display: "flex", gap: "0.25rem", background: "var(--bg-sidebar)", borderRadius: "var(--radius-sm)", padding: "0.25rem" }}>
              <button className={`btn btn-sm ${filter === "all" ? "btn-primary" : "btn-ghost"}`} onClick={() => setFilter("all")}>All</button>
              <button className={`btn btn-sm ${filter === "unread" ? "btn-primary" : "btn-ghost"}`} onClick={() => setFilter("unread")}>Unread</button>
            </div>
            {unreadCount > 0 && (
              <button onClick={markAllRead} className="btn btn-outline btn-sm">Mark all read</button>
            )}
          </div>
        </div>

        {loading ? (
          <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
            {[...Array(5)].map((_, i) => <div key={i} className="skeleton" style={{ height: "80px" }} />)}
          </div>
        ) : notifications.length === 0 ? (
          <div className="card" style={{ textAlign: "center", padding: "3rem" }}>
            <div style={{ fontSize: "3rem", marginBottom: "1rem" }}>🔔</div>
            <h3>No notifications</h3>
            <p style={{ color: "var(--text-muted)", marginTop: "0.5rem" }}>
              {filter === "unread" ? "All caught up!" : "You'll see scheme updates and reminders here"}
            </p>
          </div>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
            {notifications.map((n, i) => {
              const typeBadge = getTypeBadge(n.notification_type);
              return (
                <div key={n.id} className="card animate-fade-in" style={{
                  padding: "1.25rem", animationDelay: `${i * 0.05}s`,
                  borderLeft: `3px solid ${n.is_read ? "var(--border)" : getPriorityColor(n.priority)}`,
                  opacity: n.is_read ? 0.7 : 1,
                }}>
                  <div style={{ display: "flex", gap: "1rem", alignItems: "flex-start" }}>
                    <div style={{ fontSize: "1.5rem", flexShrink: 0 }}>{getIcon(n.notification_type)}</div>
                    <div style={{ flex: 1 }}>
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                        <h4 style={{ fontSize: "0.9375rem", marginBottom: "0.25rem" }}>{n.title}</h4>
                        <div style={{ display: "flex", gap: "0.5rem", alignItems: "center", flexShrink: 0 }}>
                          {!n.is_read && (
                            <button onClick={() => markRead(n.id)} className="btn btn-ghost btn-sm"
                              style={{ fontSize: "0.75rem", padding: "0.125rem 0.5rem" }}>
                              Mark read
                            </button>
                          )}
                          <button onClick={() => deleteNotification(n.id)} className="btn btn-ghost btn-sm"
                            style={{ fontSize: "0.75rem", padding: "0.125rem 0.5rem", color: "var(--error)" }}>
                            ✕
                          </button>
                        </div>
                      </div>
                      <p style={{ color: "var(--text-secondary)", fontSize: "0.875rem", lineHeight: 1.5 }}>
                        {n.message}
                      </p>
                      <div style={{ display: "flex", gap: "0.75rem", marginTop: "0.5rem", alignItems: "center", flexWrap: "wrap" }}>
                        <span style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
                          {new Date(n.created_at).toLocaleString()}
                        </span>
                        <span className={`badge ${typeBadge.cls}`} style={{ fontSize: "0.6875rem" }}>
                          {typeBadge.label}
                        </span>
                        <span className={`badge ${n.priority === "urgent" ? "badge-error" : n.priority === "high" ? "badge-warning" : "badge-primary"}`}
                          style={{ fontSize: "0.6875rem" }}>
                          {n.priority}
                        </span>
                        {n.scheme_name && (
                          <Link href={`/schemes`}
                            style={{ fontSize: "0.75rem", color: "var(--primary-light)", textDecoration: "none" }}>
                            {n.scheme_name} →
                          </Link>
                        )}
                      </div>
                      {/* Rule change details */}
                      {n.change_details && n.notification_type === "rule_change" && (
                        <div style={{
                          marginTop: "0.75rem", padding: "0.75rem", background: "var(--bg-sidebar)",
                          borderRadius: "var(--radius-sm)", fontSize: "0.8125rem",
                        }}>
                          <strong>Change Details:</strong>
                          {(n.change_details as { changed_fields?: string[] }).changed_fields && (
                            <div style={{ marginTop: "0.25rem", color: "var(--text-secondary)" }}>
                              Changed fields: {((n.change_details as { changed_fields?: string[] }).changed_fields || []).join(", ")}
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
