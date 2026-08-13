"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import api from "@/lib/api";

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
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [loading, setLoading] = useState(true);
  const [profileSummary, setProfileSummary] = useState<Record<string, unknown>>({});
  const [topK, setTopK] = useState(10);
  const [expandedCards, setExpandedCards] = useState<Set<number>>(new Set());
  const [unreadCount, setUnreadCount] = useState(0);

  useEffect(() => {
    const token = localStorage.getItem("access_token");
    if (!token) { router.push("/auth/login"); return; }
    api.getUnreadCount().then(d => setUnreadCount(d.unread_count)).catch(() => {});
    loadRecommendations();
  }, [topK, router]);

  const loadRecommendations = async () => {
    setLoading(true);
    try {
      const data = await api.getRecommendations(topK) as {
        recommendations: Recommendation[];
        user_profile_summary: Record<string, unknown>;
      };
      setRecommendations(data.recommendations || []);
      setProfileSummary(data.user_profile_summary || {});
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const toggleExpand = (index: number) => {
    const newSet = new Set(expandedCards);
    if (newSet.has(index)) newSet.delete(index); else newSet.add(index);
    setExpandedCards(newSet);
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
            <Link href="/recommendations" className="nav-link active">For You</Link>
            <Link href="/chatbot" className="nav-link">AI Chat</Link>
            <Link href="/notifications" className="nav-link" style={{ position: "relative" }}>
              🔔
              {unreadCount > 0 && (
                <span style={{
                  position: "absolute", top: "-2px", right: "-8px", minWidth: "18px", height: "18px",
                  background: "var(--error)", borderRadius: "var(--radius-full)", fontSize: "0.6875rem",
                  color: "white", display: "flex", alignItems: "center", justifyContent: "center",
                  fontWeight: 700, padding: "0 4px",
                }}>{unreadCount > 99 ? "99+" : unreadCount}</span>
              )}
            </Link>
            <Link href="/profile" className="nav-link">Profile</Link>
          </div>
        </div>
      </nav>

      <div className="container page">
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "2rem", flexWrap: "wrap", gap: "1rem" }}>
          <div>
            <h1>🎯 Personalized Recommendations</h1>
            <p style={{ color: "var(--text-secondary)" }}>
              AI-powered scheme matches based on your profile
            </p>
          </div>
          <div style={{ display: "flex", gap: "0.75rem", alignItems: "center" }}>
            <label className="label" style={{ marginBottom: 0 }}>Show top:</label>
            <select className="select" style={{ width: "80px" }} value={topK} onChange={(e) => setTopK(Number(e.target.value))}>
              <option value={5}>5</option>
              <option value={10}>10</option>
              <option value={15}>15</option>
              <option value={20}>20</option>
            </select>
          </div>
        </div>

        {/* Profile Summary */}
        <div className="card" style={{ marginBottom: "2rem", background: "var(--bg-sidebar)" }}>
          <h4 style={{ marginBottom: "0.75rem" }}>Your Profile Summary</h4>
          <div style={{ display: "flex", gap: "1rem", flexWrap: "wrap" }}>
            {Object.entries(profileSummary).filter(([, v]) => v).map(([k, v]) => (
              <span key={k} className="badge badge-primary">
                {k.replace(/_/g, " ")}: {String(v)}
              </span>
            ))}
          </div>
          {!profileSummary.profile_completed && (
            <div style={{ marginTop: "0.75rem" }}>
              <Link href="/profile" className="btn btn-primary btn-sm">
                Complete profile for better results →
              </Link>
            </div>
          )}
        </div>

        {/* Recommendations List */}
        {loading ? (
          <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
            {[...Array(5)].map((_, i) => <div key={i} className="skeleton" style={{ height: "200px" }} />)}
          </div>
        ) : recommendations.length === 0 ? (
          <div className="card" style={{ textAlign: "center", padding: "3rem" }}>
            <div style={{ fontSize: "3rem", marginBottom: "1rem" }}>🎯</div>
            <h3>No recommendations yet</h3>
            <p style={{ color: "var(--text-muted)", marginTop: "0.5rem" }}>
              Complete your profile to get personalized scheme recommendations
            </p>
            <Link href="/profile" className="btn btn-primary" style={{ marginTop: "1rem" }}>Complete Profile</Link>
          </div>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: "1.25rem" }}>
            {recommendations.map((rec, i) => {
              const expanded = expandedCards.has(i);
              const isEligible = rec.eligibility_probability >= 0.5;
              return (
                <div key={i} className="card animate-fade-in" style={{ animationDelay: `${i * 0.08}s` }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: "1.5rem" }}>
                    {/* Left: Scheme Info */}
                    <div style={{ flex: 1 }}>
                      <div style={{ display: "flex", gap: "0.5rem", marginBottom: "0.5rem", flexWrap: "wrap" }}>
                        <span style={{
                          fontSize: "0.75rem", fontWeight: 700, color: "white",
                          background: "var(--primary)", padding: "0.125rem 0.5rem", borderRadius: "var(--radius-full)",
                        }}>
                          #{i + 1}
                        </span>
                        <span className={`badge`}
                          style={{
                            background: isEligible ? "rgba(16,185,129,0.1)" : "rgba(239,68,68,0.1)",
                            color: isEligible ? "var(--success)" : "var(--error)",
                            fontWeight: 700, fontSize: "0.6875rem",
                          }}>
                          {isEligible ? "✅ ELIGIBLE" : "❌ NOT ELIGIBLE"}
                        </span>
                        <span className={`badge ${rec.scheme.level === "Central" ? "badge-primary" : "badge-accent"}`}>
                          {rec.scheme.level}
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
                    <div style={{ textAlign: "center", minWidth: "100px" }}>
                      <div style={{
                        width: "80px", height: "80px", borderRadius: "50%",
                        display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center",
                        border: `3px solid ${rec.eligibility_probability >= 0.7 ? "var(--success)" : rec.eligibility_probability >= 0.4 ? "var(--warning)" : "var(--error)"}`,
                      }}>
                        <div style={{
                          fontSize: "1.5rem", fontWeight: 800,
                          color: rec.eligibility_probability >= 0.7 ? "var(--success)" : rec.eligibility_probability >= 0.4 ? "var(--warning)" : "var(--error)",
                        }}>
                          {Math.round(rec.eligibility_probability * 100)}%
                        </div>
                      </div>
                      <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginTop: "0.375rem" }}>
                        Match Score
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
                      <strong style={{ fontSize: "0.8125rem" }}>🎁 Benefits: </strong>
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
                          <strong style={{ fontSize: "0.875rem", color: "var(--success)" }}>Matched Conditions:</strong>
                          {rec.matched_conditions.map((c, ci) => (
                            <div key={ci} style={{ fontSize: "0.8125rem", color: "var(--text-secondary)", paddingLeft: "1rem" }}>• {c}</div>
                          ))}
                        </div>
                      )}
                      {rec.failed_conditions.length > 0 && (
                        <div>
                          <strong style={{ fontSize: "0.875rem", color: "var(--error)" }}>Failed Conditions:</strong>
                          {rec.failed_conditions.map((c, ci) => (
                            <div key={ci} style={{ fontSize: "0.8125rem", color: "var(--text-secondary)", paddingLeft: "1rem" }}>• {c}</div>
                          ))}
                        </div>
                      )}
                      <div style={{ marginTop: "0.75rem", fontSize: "0.8125rem", color: "var(--text-muted)" }}>
                        Confidence: {Math.round(rec.confidence * 100)}% • Score: {rec.score.toFixed(3)}
                      </div>
                    </div>
                  )}

                  {/* Actions */}
                  <div style={{ marginTop: "1rem", display: "flex", gap: "0.75rem", alignItems: "center", flexWrap: "wrap" }}>
                    <Link href={`/schemes/${rec.scheme.slug}`} className="btn btn-primary btn-sm">View Details</Link>
                    <button onClick={() => toggleExpand(i)} className="btn btn-ghost btn-sm">
                      {expanded ? "Show less ↑" : "Explain why ↓"}
                    </button>
                    {rec.scheme.application_link && (
                      <a href={rec.scheme.application_link} target="_blank" rel="noopener noreferrer" className="btn btn-accent btn-sm">
                        Apply →
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
