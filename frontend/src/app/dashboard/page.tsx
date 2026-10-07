"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import api from "@/lib/api";
import Navbar from "@/components/Navbar";
import { useLanguage } from "@/context/LanguageContext";

interface Recommendation {
  scheme: {
    id: number;
    scheme_name: string;
    slug: string;
    details: string;
    benefits: string;
    eligibility: string;
    level: string;
    scheme_category: string;
    application_link?: string;
  };
  score: number;
  confidence: number;
  reasons: string[];
  matched_conditions: string[];
  failed_conditions: string[];
  eligibility_probability: number;
  eligibility_status?: string;
}

interface Notification {
  id: number;
  title: string;
  message: string;
  notification_type: string;
  is_read: boolean;
  created_at: string;
}

export default function DashboardPage() {
  const router = useRouter();
  const { t } = useLanguage();
  const [user, setUser] = useState<Record<string, unknown> | null>(null);
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [savedCount, setSavedCount] = useState(0);
  const [eligibleCount, setEligibleCount] = useState(0);
  const [ineligibleCount, setIneligibleCount] = useState(0);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem("access_token");
    if (!token) {
      router.push("/auth/login");
      return;
    }

    const stored = localStorage.getItem("user");
    if (stored) setUser(JSON.parse(stored));

    loadDashboard();
  }, [router]);

  const loadDashboard = async () => {
    try {
      const [profile, recs, notifs, saved, eligibility] = await Promise.allSettled([
        api.getProfile(),
        api.getRecommendations(5),
        api.getNotifications(1),
        api.getSavedSchemes(),
        api.getFullEligibility({ page: 1, page_size: 1 }),
      ]);

      if (profile.status === "fulfilled") setUser(profile.value as Record<string, unknown>);
      if (recs.status === "fulfilled") {
        const r = recs.value as { recommendations: Recommendation[] };
        setRecommendations((r.recommendations || []).slice(0, 5));
      }
      if (notifs.status === "fulfilled") {
        const n = notifs.value as { notifications: Notification[]; unread_count: number };
        setNotifications((n.notifications || []).slice(0, 5));
        setUnreadCount(n.unread_count || 0);
      }
      if (saved.status === "fulfilled") {
        const s = saved.value as unknown[];
        setSavedCount(Array.isArray(s) ? s.length : 0);
      }
      if (eligibility.status === "fulfilled") {
        const e = eligibility.value as { eligible_count: number; ineligible_count: number };
        setEligibleCount(e.eligible_count || 0);
        setIneligibleCount(e.ineligible_count || 0);
      }
    } catch (err) {
      console.error("Dashboard load error:", err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div style={{ minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center" }}>
        <div style={{ textAlign: "center" }}>
          <div style={{ fontSize: "2rem", marginBottom: "1rem" }}>⏳</div>
          <p style={{ color: "var(--text-muted)" }}>{t("common.loading", "Loading your dashboard...")}</p>
        </div>
      </div>
    );
  }

  const profileCompletion = (user?.profile_completion_percentage as number) || 0;

  return (
    <div>
      <Navbar unreadCount={unreadCount} />

      <div className="container page">
        {/* Welcome */}
        <div className="animate-fade-in" style={{ marginBottom: "2rem" }}>
          <h1 style={{ marginBottom: "0.5rem" }}>
            {t("dashboard.welcome", "Welcome")}, {(user?.full_name as string) || "Citizen"} 👋
          </h1>
          <p style={{ color: "var(--text-secondary)" }}>
            {t("dashboard.subtitle", "Here's your personalized scheme discovery dashboard")}
          </p>
        </div>

        {/* Profile Completion Banner */}
        {profileCompletion < 70 && (
          <div
            className="card animate-fade-in"
            style={{
              marginBottom: "2rem",
              background: "linear-gradient(135deg, #1a365d, #2b6cb0)",
              color: "white",
              border: "none",
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "1rem" }}>
              <div>
                <h4 style={{ marginBottom: "0.5rem" }}>{t("dashboard.completeProfile", "Complete your profile for better recommendations")}</h4>
                <p style={{ opacity: 0.8, fontSize: "0.9375rem" }}>
                  {t("dashboard.profileIsComplete", `Profile is ${profileCompletion}% complete. Add more details to get accurate scheme matches.`, { count: profileCompletion })}
                </p>
                <div className="progress-bar" style={{ marginTop: "0.75rem", maxWidth: "300px", background: "rgba(255,255,255,0.2)" }}>
                  <div className="progress-bar-fill partial" style={{ width: `${profileCompletion}%` }} />
                </div>
              </div>
              <Link href="/profile" className="btn" style={{ background: "white", color: "var(--primary)" }}>
                {t("dashboard.completeProfileBtn", "Complete Profile →")}
              </Link>
            </div>
          </div>
        )}

        {/* Quick Stats */}
        <div className="grid-stats animate-fade-in" style={{ marginBottom: "2rem" }}>
          <div className="stat-card">
            <div className="stat-value">{recommendations.length}</div>
            <div className="stat-label">{t("dashboard.statsRecommended", "Recommended Schemes")}</div>
          </div>
          <Link href="/eligibility" className="stat-card" style={{ textDecoration: "none", cursor: "pointer" }}>
            <div className="stat-value" style={{ color: "var(--success)" }}>{eligibleCount}</div>
            <div className="stat-label">{t("dashboard.statsEligible", "Eligible Schemes")}</div>
          </Link>
          <Link href="/eligibility" className="stat-card" style={{ textDecoration: "none", cursor: "pointer" }}>
            <div className="stat-value" style={{ color: "var(--error)" }}>{ineligibleCount}</div>
            <div className="stat-label">{t("dashboard.statsIneligible", "Not Eligible")}</div>
          </Link>
          <div className="stat-card">
            <div className="stat-value">{savedCount}</div>
            <div className="stat-label">{t("dashboard.statsSaved", "Saved Schemes")}</div>
          </div>
          <div className="stat-card">
            <div className="stat-value">{unreadCount}</div>
            <div className="stat-label">{t("dashboard.statsUnread", "Unread Notifications")}</div>
          </div>
          <div className="stat-card">
            <div className="stat-value" style={{ color: profileCompletion >= 70 ? "var(--success)" : "var(--warning)" }}>
              {profileCompletion}%
            </div>
            <div className="stat-label">{t("dashboard.statsProfileComplete", "Profile Complete")}</div>
          </div>
        </div>

        {/* Quick Actions */}
        <div style={{ display: "flex", gap: "0.75rem", marginBottom: "2.5rem", flexWrap: "wrap" }}>
          <Link href="/eligibility" className="btn btn-primary">📊 {t("dashboard.checkEligibility", "Check Eligibility")}</Link>
          <Link href="/search" className="btn btn-outline">🔍 {t("dashboard.searchSchemes", "Search Schemes")}</Link>
          <Link href="/recommendations" className="btn btn-accent">🎯 {t("dashboard.viewRecommendations", "Top 5 Recommendations")}</Link>
          <Link href="/chatbot" className="btn btn-outline">🤖 {t("dashboard.askAi", "Ask AI Chatbot")}</Link>
          <Link href="/schemes" className="btn btn-ghost">🏛️ {t("dashboard.browseAll", "Browse All Schemes")}</Link>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "2fr 1fr", gap: "2rem" }}>
          {/* Recommendations */}
          <div>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1rem" }}>
              <h3>🎯 {t("dashboard.topRecommendations", "Top Recommendations")}</h3>
              <Link href="/recommendations" style={{ color: "var(--primary-light)", fontSize: "0.875rem", textDecoration: "none" }}>
                {t("dashboard.viewAll", "View all →")}
              </Link>
            </div>
            {recommendations.length === 0 ? (
              <div className="card" style={{ textAlign: "center", padding: "2rem" }}>
                <p style={{ color: "var(--text-muted)" }}>{t("dashboard.noRecs", "Complete your profile to get personalized recommendations")}</p>
              </div>
            ) : (
              <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
                {recommendations.slice(0, 5).map((rec, i) => {
                  const isEligible = (rec.eligibility_probability ?? 0) >= 0.5 && rec.eligibility_status !== "ineligible";
                  const pct = isEligible ? Math.round(rec.eligibility_probability * 100) : 0;
                  return (
                    <div key={i} className="card animate-fade-in" style={{ animationDelay: `${i * 0.1}s` }}>
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "0.75rem" }}>
                        <div style={{ flex: 1 }}>
                          <Link
                            href={`/schemes/${rec.scheme.slug}`}
                            style={{
                              fontWeight: 700,
                              fontSize: "1rem",
                              color: "var(--text)",
                              textDecoration: "none",
                            }}
                          >
                            {rec.scheme.scheme_name}
                          </Link>
                          <div style={{ display: "flex", gap: "0.5rem", marginTop: "0.375rem", flexWrap: "wrap" }}>
                            <span
                              className={`badge ${isEligible ? "badge-success" : "badge-error"}`}
                              style={{
                                background: isEligible ? "rgba(16,185,129,0.1)" : "rgba(239,68,68,0.1)",
                                color: isEligible ? "var(--success)" : "var(--error)",
                                fontWeight: 700,
                                fontSize: "0.6875rem",
                              }}
                            >
                              {isEligible ? `✅ ${t("common.eligible", "ELIGIBLE")}` : `❌ ${t("common.notEligible", "NOT ELIGIBLE")}`}
                            </span>
                            <span className={`badge ${rec.scheme.level === "Central" ? "badge-primary" : "badge-accent"}`}>
                              {rec.scheme.level === "Central" ? t("schemes.centralLevel", "Central") : t("schemes.stateLevel", "State")}
                            </span>
                            {rec.scheme.scheme_category && (
                              <span className="badge badge-warning">{rec.scheme.scheme_category.split(",")[0]}</span>
                            )}
                          </div>
                        </div>
                        <div style={{ textAlign: "right" }}>
                          <div
                            style={{
                              fontSize: "1.25rem",
                              fontWeight: 800,
                              color: isEligible
                                ? pct >= 70
                                  ? "var(--success)"
                                  : "var(--warning)"
                                : "var(--error)",
                            }}
                          >
                            {pct}%
                          </div>
                          <div style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>{t("recommendations.matchScore", "match")}</div>
                        </div>
                      </div>
                      {rec.reasons.length > 0 && (
                        <div style={{ fontSize: "0.875rem", color: "var(--success)", marginBottom: "0.5rem" }}>
                          ✓ {rec.reasons[0]}
                        </div>
                      )}
                      <div className="progress-bar" style={{ marginTop: "0.5rem" }}>
                        <div
                          className={`progress-bar-fill ${isEligible ? (pct >= 70 ? "eligible" : "partial") : "not-eligible"}`}
                          style={{ width: `${pct}%` }}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* Recent Notifications */}
          <div>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1rem" }}>
              <h3>🔔 {t("dashboard.recentAlerts", "Recent Alerts")}</h3>
              <Link href="/notifications" style={{ color: "var(--primary-light)", fontSize: "0.875rem", textDecoration: "none" }}>
                {t("dashboard.viewAll", "View all →")}
              </Link>
            </div>
            {notifications.length === 0 ? (
              <div className="card" style={{ textAlign: "center", padding: "2rem" }}>
                <p style={{ color: "var(--text-muted)", fontSize: "0.875rem" }}>{t("dashboard.noAlerts", "No notifications yet")}</p>
              </div>
            ) : (
              <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
                {notifications.map((n, i) => (
                  <div
                    key={n.id}
                    className="card animate-fade-in"
                    style={{
                      padding: "1rem",
                      animationDelay: `${i * 0.1}s`,
                      borderLeft: `3px solid ${n.is_read ? "var(--border)" : "var(--primary-light)"}`,
                    }}
                  >
                    <div style={{ fontWeight: 600, fontSize: "0.875rem", marginBottom: "0.25rem" }}>
                      {n.title}
                    </div>
                    <div style={{ fontSize: "0.8125rem", color: "var(--text-muted)", lineHeight: 1.4 }}>
                      {n.message.substring(0, 100)}...
                    </div>
                    <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginTop: "0.5rem" }}>
                      {new Date(n.created_at).toLocaleDateString()}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
