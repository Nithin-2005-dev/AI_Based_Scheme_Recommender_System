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

export default function RecommendationsPage() {
  const router = useRouter();
  const { t } = useLanguage();
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [loading, setLoading] = useState(true);
  const [profileSummary, setProfileSummary] = useState<Record<string, unknown>>({});
  const [expandedCards, setExpandedCards] = useState<Set<number>>(new Set());
  const [unreadCount, setUnreadCount] = useState(0);

  useEffect(() => {
    const token = localStorage.getItem("access_token");
    if (!token) {
      router.push("/auth/login");
      return;
    }
    api.getUnreadCount().then((d) => setUnreadCount(d.unread_count)).catch(() => {});
    loadRecommendations();
  }, [router]);

  const loadRecommendations = async () => {
    setLoading(true);
    try {
      // Exactly top 5 recommended schemes
      const data = (await api.getRecommendations(5)) as {
        recommendations: Recommendation[];
        user_profile_summary: Record<string, unknown>;
      };
      setRecommendations((data.recommendations || []).slice(0, 5));
      setProfileSummary(data.user_profile_summary || {});
    } catch (err) {
      console.error("Error loading recommendations:", err);
    } finally {
      setLoading(false);
    }
  };

  const toggleExpand = (index: number) => {
    const newSet = new Set(expandedCards);
    if (newSet.has(index)) newSet.delete(index);
    else newSet.add(index);
    setExpandedCards(newSet);
  };

  return (
    <div>
      <Navbar unreadCount={unreadCount} />

      <div className="container page">
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            marginBottom: "2rem",
            flexWrap: "wrap",
            gap: "1rem",
          }}
        >
          <div>
            <h1 style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
              🎯 {t("recommendations.title", "Top 5 Recommended Schemes")}
            </h1>
            <p style={{ color: "var(--text-secondary)" }}>
              {t("recommendations.subtitle", "AI-powered personalized recommendations strictly verified against your eligibility")}
            </p>
          </div>
          <div style={{ display: "flex", gap: "0.5rem", alignItems: "center" }}>
            <span className="badge badge-primary" style={{ padding: "0.5rem 0.75rem", fontSize: "0.875rem" }}>
              {t("recommendations.showingTop5", "Showing Top 5 Schemes")}
            </span>
          </div>
        </div>

        {/* Profile Summary */}
        <div className="card" style={{ marginBottom: "2rem", background: "var(--bg-sidebar)" }}>
          <h4 style={{ marginBottom: "0.75rem" }}>{t("recommendations.profileSummary", "Your Profile Summary")}</h4>
          <div style={{ display: "flex", gap: "0.75rem", flexWrap: "wrap" }}>
            {Object.entries(profileSummary)
              .filter(([, v]) => v !== null && v !== undefined && v !== "")
              .map(([k, v]) => (
                <span key={k} className="badge badge-primary">
                  {k.replace(/_/g, " ")}: {String(v)}
                </span>
              ))}
          </div>
          {!profileSummary.profile_completed && (
            <div style={{ marginTop: "0.75rem" }}>
              <Link href="/profile" className="btn btn-primary btn-sm">
                {t("recommendations.completeProfileNotice", "Complete profile for more accurate matches →")}
              </Link>
            </div>
          )}
        </div>

        {/* Recommendations List */}
        {loading ? (
          <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
            {[...Array(5)].map((_, i) => (
              <div key={i} className="skeleton" style={{ height: "200px" }} />
            ))}
          </div>
        ) : recommendations.length === 0 ? (
          <div className="card" style={{ textAlign: "center", padding: "3rem" }}>
            <div style={{ fontSize: "3rem", marginBottom: "1rem" }}>🎯</div>
            <h3>{t("recommendations.emptyTitle", "No recommendations found")}</h3>
            <p style={{ color: "var(--text-muted)", marginTop: "0.5rem" }}>
              {t("recommendations.emptySubtitle", "Update your profile or relax filters to receive personalized recommendations.")}
            </p>
            <Link href="/profile" className="btn btn-primary" style={{ marginTop: "1rem" }}>
              {t("dashboard.completeProfileBtn", "Update Profile")}
            </Link>
          </div>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: "1.25rem" }}>
            {recommendations.map((rec, i) => {
              const expanded = expandedCards.has(i);
              // Strict invariant check: an ineligible scheme must have 0%
              const isEligible =
                (rec.eligibility_probability ?? 0) >= 0.5 &&
                rec.eligibility_status !== "ineligible" &&
                (!rec.failed_conditions || rec.failed_conditions.length === 0);
              const eligibilityPercentage = isEligible ? Math.round(rec.eligibility_probability * 100) : 0;

              return (
                <div key={i} className="card animate-fade-in" style={{ animationDelay: `${i * 0.08}s` }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: "1.5rem" }}>
                    {/* Left: Scheme Info */}
                    <div style={{ flex: 1 }}>
                      <div style={{ display: "flex", gap: "0.5rem", marginBottom: "0.5rem", flexWrap: "wrap", alignItems: "center" }}>
                        <span
                          style={{
                            fontSize: "0.75rem",
                            fontWeight: 700,
                            color: "white",
                            background: "var(--primary)",
                            padding: "0.125rem 0.5rem",
                            borderRadius: "var(--radius-full)",
                          }}
                        >
                          #{i + 1}
                        </span>
                        <span
                          className="badge"
                          style={{
                            background: isEligible ? "rgba(16,185,129,0.1)" : "rgba(239,68,68,0.1)",
                            color: isEligible ? "var(--success)" : "var(--error)",
                            fontWeight: 700,
                            fontSize: "0.6875rem",
                          }}
                        >
                          {isEligible
                            ? `✅ ${t("common.eligible", "ELIGIBLE")}`
                            : `❌ ${t("common.notEligible", "NOT ELIGIBLE")}`}
                        </span>
                        <span className={`badge ${rec.scheme.level === "Central" ? "badge-primary" : "badge-accent"}`}>
                          {rec.scheme.level === "Central" ? t("schemes.centralLevel", "Central") : t("schemes.stateLevel", "State")}
                        </span>
                        {rec.scheme.scheme_category && (
                          <span className="badge badge-warning">{rec.scheme.scheme_category.split(",")[0].trim()}</span>
                        )}
                      </div>
                      <Link href={`/schemes/${rec.scheme.slug}`} style={{ textDecoration: "none" }}>
                        <h3 style={{ color: "var(--text)", marginBottom: "0.5rem", fontSize: "1.125rem" }}>
                          {rec.scheme.scheme_name}
                        </h3>
                      </Link>
                      <p style={{ color: "var(--text-secondary)", fontSize: "0.875rem", lineHeight: 1.5 }}>
                        {rec.scheme.details?.substring(0, 200)}...
                      </p>
                    </div>

                    {/* Right: Score */}
                    <div style={{ textAlign: "center", minWidth: "110px", flexShrink: 0 }}>
                      <div
                        style={{
                          width: "80px",
                          height: "80px",
                          borderRadius: "50%",
                          margin: "0 auto",
                          display: "flex",
                          flexDirection: "column",
                          alignItems: "center",
                          justifyContent: "center",
                          border: `3px solid ${
                            isEligible
                              ? eligibilityPercentage >= 70
                                ? "var(--success)"
                                : "var(--warning)"
                              : "var(--error)"
                          }`,
                        }}
                      >
                        <div
                          style={{
                            fontSize: "1.5rem",
                            fontWeight: 800,
                            color: isEligible
                              ? eligibilityPercentage >= 70
                                ? "var(--success)"
                                : "var(--warning)"
                              : "var(--error)",
                          }}
                        >
                          {eligibilityPercentage}%
                        </div>
                      </div>
                      <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginTop: "0.375rem" }}>
                        {isEligible ? t("recommendations.matchScore", "Match Score") : t("common.notEligible", "Not Eligible")}
                      </div>
                    </div>
                  </div>

                  {/* Reasons — always visible */}
                  {rec.reasons.length > 0 && (
                    <div style={{ marginTop: "1rem", display: "flex", flexDirection: "column", gap: "0.375rem" }}>
                      {rec.reasons.slice(0, expanded ? undefined : 2).map((reason, ri) => (
                        <div key={ri} style={{ display: "flex", gap: "0.5rem", fontSize: "0.875rem", color: "var(--success)" }}>
                          <span>✓</span>
                          <span>{reason}</span>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Benefits preview */}
                  {rec.scheme.benefits && (
                    <div style={{ marginTop: "0.75rem", padding: "0.75rem", background: "var(--bg-sidebar)", borderRadius: "var(--radius-sm)" }}>
                      <strong style={{ fontSize: "0.8125rem" }}>🎁 {t("schemes.benefits", "Benefits")}: </strong>
                      <span style={{ fontSize: "0.8125rem", color: "var(--text-secondary)" }}>
                        {rec.scheme.benefits.substring(0, expanded ? 1000 : 200)}
                        {!expanded && rec.scheme.benefits.length > 200 ? "..." : ""}
                      </span>
                    </div>
                  )}

                  {/* Expanded: Matched & Failed */}
                  {expanded && (
                    <div style={{ marginTop: "1rem", paddingTop: "1rem", borderTop: "1px solid var(--border)" }}>
                      {rec.matched_conditions.length > 0 && (
                        <div style={{ marginBottom: "0.75rem" }}>
                          <strong style={{ fontSize: "0.875rem", color: "var(--success)" }}>
                            {t("recommendations.matchedCriteria", "Matched Conditions")}:
                          </strong>
                          {rec.matched_conditions.map((c, ci) => (
                            <div key={ci} style={{ fontSize: "0.8125rem", color: "var(--text-secondary)", paddingLeft: "1rem" }}>
                              • {c}
                            </div>
                          ))}
                        </div>
                      )}
                      {rec.failed_conditions.length > 0 && (
                        <div>
                          <strong style={{ fontSize: "0.875rem", color: "var(--error)" }}>
                            {t("recommendations.failedCriteria", "Failed Conditions")}:
                          </strong>
                          {rec.failed_conditions.map((c, ci) => (
                            <div key={ci} style={{ fontSize: "0.8125rem", color: "var(--text-secondary)", paddingLeft: "1rem" }}>
                              • {typeof c === "object" && c !== null ? (c as { reason?: string }).reason || JSON.stringify(c) : String(c)}
                            </div>
                          ))}
                        </div>
                      )}
                      <div style={{ marginTop: "0.75rem", fontSize: "0.8125rem", color: "var(--text-muted)" }}>
                        {t("recommendations.confidence", "Confidence")}: {Math.round(rec.confidence * 100)}% • {t("recommendations.score", "Score")}: {rec.score.toFixed(3)}
                      </div>
                    </div>
                  )}

                  {/* Actions */}
                  <div style={{ marginTop: "1rem", display: "flex", gap: "0.75rem", alignItems: "center", flexWrap: "wrap" }}>
                    <Link href={`/schemes/${rec.scheme.slug}`} className="btn btn-primary btn-sm">
                      {t("schemes.viewDetails", "View Details")}
                    </Link>
                    <button onClick={() => toggleExpand(i)} className="btn btn-ghost btn-sm">
                      {expanded ? t("recommendations.showLess", "Show less ↑") : t("recommendations.explainWhy", "Explain why ↓")}
                    </button>
                    {rec.scheme.application_link && (
                      <a href={rec.scheme.application_link} target="_blank" rel="noopener noreferrer" className="btn btn-accent btn-sm">
                        {t("schemes.applyNow", "Apply →")}
                      </a>
                    )}
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
