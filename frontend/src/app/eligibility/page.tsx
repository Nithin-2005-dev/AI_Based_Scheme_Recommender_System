"use client";

import { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import api from "@/lib/api";
import Navbar from "@/components/Navbar";
import { useLanguage } from "@/context/LanguageContext";

interface EligibilityScheme {
  scheme_id: number;
  scheme_name: string;
  slug: string;
  level: string;
  scheme_category: string;
  is_eligible: boolean;
  status: string;
  confidence: number;
  score: number;
  matched_criteria: string[];
  failed_criteria: (string | { criterion?: string; reason?: string })[];
  missing_info: string[];
  missing_documents: string[];
  documents_required: string;
  benefits: string;
  explanation: string;
  application_link: string | null;
}

interface EligibilityData {
  schemes: EligibilityScheme[];
  total: number;
  page: number;
  page_size: number;
  eligible_count: number;
  ineligible_count: number;
}

export default function EligibilityPage() {
  const router = useRouter();
  const { t } = useLanguage();
  const [data, setData] = useState<EligibilityData | null>(null);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState<"eligible" | "ineligible">("eligible");
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("");
  const [stateFilter, setStateFilter] = useState("");
  const [page, setPage] = useState(1);
  const [expandedCards, setExpandedCards] = useState<Set<number>>(new Set());
  const [unreadCount, setUnreadCount] = useState(0);

  useEffect(() => {
    const token = localStorage.getItem("access_token");
    if (!token) {
      router.push("/auth/login");
      return;
    }
    api.getUnreadCount().then((d) => setUnreadCount(d.unread_count)).catch(() => {});
  }, [router]);

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const params: Record<string, string | number> = { page, page_size: 30 };
      if (search) params.search = search;
      if (category) params.category = category;
      if (stateFilter) params.state = stateFilter;

      let result: EligibilityData;
      if (tab === "eligible") {
        result = (await api.getEligibleSchemes(params)) as EligibilityData;
      } else {
        result = (await api.getIneligibleSchemes(params)) as EligibilityData;
      }
      setData(result);
    } catch (err) {
      console.error("Error loading eligibility data:", err);
    } finally {
      setLoading(false);
    }
  }, [tab, page, search, category, stateFilter]);

  useEffect(() => {
    const token = localStorage.getItem("access_token");
    if (token) loadData();
  }, [loadData]);

  const toggleExpand = (id: number) => {
    const newSet = new Set(expandedCards);
    if (newSet.has(id)) newSet.delete(id);
    else newSet.add(id);
    setExpandedCards(newSet);
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    loadData();
  };

  return (
    <div>
      <Navbar unreadCount={unreadCount} />

      <div className="container page">
        {/* Header */}
        <div style={{ marginBottom: "2rem" }}>
          <h1 style={{ marginBottom: "0.5rem" }}>📊 {t("eligibility.title", "Scheme Eligibility")}</h1>
          <p style={{ color: "var(--text-secondary)" }}>
            {t("eligibility.subtitle", "Your profile is evaluated against all available government schemes")}
          </p>
        </div>

        {/* Summary Cards */}
        <div className="grid-stats" style={{ marginBottom: "2rem", maxWidth: "600px" }}>
          <div
            className="stat-card"
            style={{
              cursor: "pointer",
              border: tab === "eligible" ? "2px solid var(--success)" : undefined,
              background: tab === "eligible" ? "rgba(16, 185, 129, 0.05)" : undefined,
            }}
            onClick={() => {
              setTab("eligible");
              setPage(1);
            }}
          >
            <div className="stat-value" style={{ color: "var(--success)" }}>
              {data?.eligible_count ?? "—"}
            </div>
            <div className="stat-label">{t("eligibility.eligibleCount", "Eligible Schemes")}</div>
          </div>
          <div
            className="stat-card"
            style={{
              cursor: "pointer",
              border: tab === "ineligible" ? "2px solid var(--error)" : undefined,
              background: tab === "ineligible" ? "rgba(239, 68, 68, 0.05)" : undefined,
            }}
            onClick={() => {
              setTab("ineligible");
              setPage(1);
            }}
          >
            <div className="stat-value" style={{ color: "var(--error)" }}>
              {data?.ineligible_count ?? "—"}
            </div>
            <div className="stat-label">{t("eligibility.ineligibleCount", "Not Eligible")}</div>
          </div>
        </div>

        {/* Filters */}
        <form
          onSubmit={handleSearch}
          style={{
            display: "flex",
            gap: "0.75rem",
            marginBottom: "1.5rem",
            flexWrap: "wrap",
          }}
        >
          <input
            className="input"
            placeholder={t("schemes.searchPlaceholder", "Search schemes...")}
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            style={{ flex: "1", minWidth: "200px" }}
          />
          <select
            className="select"
            value={category}
            onChange={(e) => {
              setCategory(e.target.value);
              setPage(1);
            }}
            style={{ minWidth: "160px" }}
          >
            <option value="">{t("schemes.allCategories", "All Categories")}</option>
            <option value="Agriculture">{t("categories.agriculture", "Agriculture")}</option>
            <option value="Education">{t("categories.education", "Education")}</option>
            <option value="Health">{t("categories.health", "Health")}</option>
            <option value="Business">{t("categories.business", "Business")}</option>
            <option value="Social welfare">{t("categories.socialWelfare", "Social Welfare")}</option>
            <option value="Women">{t("categories.womenChild", "Women & Child")}</option>
            <option value="Housing">{t("categories.housing", "Housing")}</option>
            <option value="Skills">{t("categories.skillsEmployment", "Skills & Employment")}</option>
          </select>
          <select
            className="select"
            value={stateFilter}
            onChange={(e) => {
              setStateFilter(e.target.value);
              setPage(1);
            }}
            style={{ minWidth: "140px" }}
          >
            <option value="">{t("schemes.allStates", "All States")}</option>
            <option value="Telangana">Telangana</option>
            <option value="Andhra Pradesh">Andhra Pradesh</option>
            <option value="Karnataka">Karnataka</option>
            <option value="Tamil Nadu">Tamil Nadu</option>
            <option value="Maharashtra">Maharashtra</option>
            <option value="Delhi">Delhi</option>
            <option value="Uttar Pradesh">Uttar Pradesh</option>
            <option value="Rajasthan">Rajasthan</option>
          </select>
          <button type="submit" className="btn btn-primary">
            🔍 {t("common.search", "Search")}
          </button>
        </form>

        {/* Tab Toggle */}
        <div
          style={{
            display: "flex",
            gap: "0.25rem",
            background: "var(--bg-sidebar)",
            borderRadius: "var(--radius-sm)",
            padding: "0.25rem",
            marginBottom: "1.5rem",
            maxWidth: "320px",
          }}
        >
          <button
            className={`btn btn-sm ${tab === "eligible" ? "btn-primary" : "btn-ghost"}`}
            onClick={() => {
              setTab("eligible");
              setPage(1);
            }}
            style={{ flex: 1 }}
          >
            ✅ {t("eligibility.eligibleTab", "Eligible")}
          </button>
          <button
            className={`btn btn-sm ${tab === "ineligible" ? "btn-primary" : "btn-ghost"}`}
            onClick={() => {
              setTab("ineligible");
              setPage(1);
            }}
            style={{ flex: 1 }}
          >
            ❌ {t("eligibility.ineligibleTab", "Not Eligible")}
          </button>
        </div>

        {/* Scheme List */}
        {loading ? (
          <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
            {[...Array(5)].map((_, i) => (
              <div key={i} className="skeleton" style={{ height: "140px" }} />
            ))}
          </div>
        ) : !data || data.schemes.length === 0 ? (
          <div className="card" style={{ textAlign: "center", padding: "3rem" }}>
            <div style={{ fontSize: "3rem", marginBottom: "1rem" }}>{tab === "eligible" ? "✅" : "❌"}</div>
            <h3>
              {tab === "eligible"
                ? t("eligibility.emptyEligible", "No eligible schemes found")
                : t("eligibility.emptyIneligible", "No ineligible schemes found")}
            </h3>
            <p style={{ color: "var(--text-muted)", marginTop: "0.5rem" }}>
              {search || category
                ? t("schemes.noSchemesDesc", "Try adjusting your filters")
                : t("dashboard.noRecs", "Complete your profile for better results")}
            </p>
            <Link href="/profile" className="btn btn-primary" style={{ marginTop: "1rem" }}>
              {t("profile.saveChanges", "Update Profile")}
            </Link>
          </div>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
            {data.schemes.map((scheme, i) => {
              const expanded = expandedCards.has(scheme.scheme_id);
              // Invariant: Ineligible schemes MUST show 0%, never 100%
              const percentage = scheme.is_eligible ? Math.round(scheme.confidence * 100) : 0;

              return (
                <div key={scheme.scheme_id} className="card animate-fade-in" style={{ animationDelay: `${i * 0.04}s` }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: "1.5rem" }}>
                    <div style={{ flex: 1 }}>
                      <div style={{ display: "flex", gap: "0.5rem", marginBottom: "0.5rem", flexWrap: "wrap", alignItems: "center" }}>
                        <span
                          className={`badge ${scheme.is_eligible ? "badge-success" : "badge-error"}`}
                          style={{
                            background: scheme.is_eligible ? "rgba(16,185,129,0.1)" : "rgba(239,68,68,0.1)",
                            color: scheme.is_eligible ? "var(--success)" : "var(--error)",
                            fontWeight: 700,
                          }}
                        >
                          {scheme.is_eligible
                            ? `✅ ${t("common.eligible", "ELIGIBLE")}`
                            : `❌ ${t("common.notEligible", "NOT ELIGIBLE")}`}
                        </span>
                        <span className={`badge ${scheme.level === "Central" ? "badge-primary" : "badge-accent"}`}>
                          {scheme.level === "Central" ? t("schemes.centralLevel", "Central") : t("schemes.stateLevel", "State")}
                        </span>
                        {scheme.scheme_category && (
                          <span className="badge badge-warning">{scheme.scheme_category.split(",")[0].trim()}</span>
                        )}
                      </div>
                      <Link href={`/schemes/${scheme.slug}`} style={{ textDecoration: "none" }}>
                        <h3 style={{ color: "var(--text)", marginBottom: "0.5rem", fontSize: "1.0625rem" }}>
                          {scheme.scheme_name}
                        </h3>
                      </Link>

                      {/* Matched criteria */}
                      {scheme.matched_criteria.length > 0 && (
                        <div style={{ marginTop: "0.5rem" }}>
                          {scheme.matched_criteria.slice(0, expanded ? undefined : 2).map((c, ci) => (
                            <div
                              key={ci}
                              style={{
                                fontSize: "0.875rem",
                                color: "var(--success)",
                                display: "flex",
                                gap: "0.375rem",
                                marginBottom: "0.25rem",
                              }}
                            >
                              <span>✓</span>
                              <span>{c}</span>
                            </div>
                          ))}
                        </div>
                      )}

                      {/* Failed criteria */}
                      {scheme.failed_criteria.length > 0 && (
                        <div style={{ marginTop: "0.375rem" }}>
                          {scheme.failed_criteria.slice(0, expanded ? undefined : 2).map((c, ci) => {
                            const reasonText = typeof c === "object" && c !== null ? (c as { reason?: string }).reason || JSON.stringify(c) : String(c);
                            return (
                              <div
                                key={ci}
                                style={{
                                  fontSize: "0.875rem",
                                  color: "var(--error)",
                                  display: "flex",
                                  gap: "0.375rem",
                                  marginBottom: "0.25rem",
                                }}
                              >
                                <span>✗</span>
                                <span>{reasonText}</span>
                              </div>
                            );
                          })}
                        </div>
                      )}

                      {/* Missing info */}
                      {expanded && scheme.missing_info.length > 0 && (
                        <div style={{ marginTop: "0.375rem" }}>
                          {scheme.missing_info.map((c, ci) => (
                            <div
                              key={ci}
                              style={{
                                fontSize: "0.875rem",
                                color: "var(--warning)",
                                display: "flex",
                                gap: "0.375rem",
                                marginBottom: "0.25rem",
                              }}
                            >
                              <span>⚠</span>
                              <span>{c}</span>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>

                    {/* Confidence Circle */}
                    <div style={{ textAlign: "center", minWidth: "90px", flexShrink: 0 }}>
                      <div
                        style={{
                          width: "68px",
                          height: "68px",
                          borderRadius: "50%",
                          margin: "0 auto",
                          display: "flex",
                          flexDirection: "column",
                          alignItems: "center",
                          justifyContent: "center",
                          border: `3px solid ${scheme.is_eligible ? "var(--success)" : "var(--error)"}`,
                        }}
                      >
                        <div
                          style={{
                            fontSize: "1.25rem",
                            fontWeight: 800,
                            color: scheme.is_eligible ? "var(--success)" : "var(--error)",
                          }}
                        >
                          {percentage}%
                        </div>
                      </div>
                      <div style={{ fontSize: "0.6875rem", color: "var(--text-muted)", marginTop: "0.25rem" }}>
                        {scheme.is_eligible ? t("eligibility.confidenceLabel", "confidence") : t("common.notEligible", "Not Eligible")}
                      </div>
                    </div>
                  </div>

                  {/* Expanded Details */}
                  {expanded && (
                    <div style={{ marginTop: "1rem", paddingTop: "1rem", borderTop: "1px solid var(--border)" }}>
                      {scheme.missing_documents.length > 0 && (
                        <div style={{ marginBottom: "0.75rem" }}>
                          <strong style={{ fontSize: "0.875rem" }}>📄 {t("schemes.missingDocuments", "Missing Documents")}:</strong>
                          {scheme.missing_documents.map((d, di) => (
                            <div key={di} style={{ fontSize: "0.8125rem", color: "var(--text-secondary)", paddingLeft: "1rem" }}>
                              • {d}
                            </div>
                          ))}
                        </div>
                      )}
                      {scheme.documents_required && (
                        <div style={{ marginBottom: "0.75rem" }}>
                          <strong style={{ fontSize: "0.875rem" }}>📋 {t("schemes.documentsRequired", "Required Documents")}:</strong>
                          <p style={{ fontSize: "0.8125rem", color: "var(--text-secondary)", marginTop: "0.25rem" }}>
                            {scheme.documents_required}
                          </p>
                        </div>
                      )}
                      {scheme.benefits && (
                        <div style={{ marginBottom: "0.75rem" }}>
                          <strong style={{ fontSize: "0.875rem" }}>🎁 {t("schemes.benefits", "Benefits")}:</strong>
                          <p style={{ fontSize: "0.8125rem", color: "var(--text-secondary)", marginTop: "0.25rem" }}>
                            {scheme.benefits}
                          </p>
                        </div>
                      )}
                      <div style={{ fontSize: "0.8125rem", color: "var(--text-muted)", marginTop: "0.5rem", whiteSpace: "pre-wrap" }}>
                        {scheme.explanation}
                      </div>
                    </div>
                  )}

                  {/* Actions */}
                  <div style={{ marginTop: "0.75rem", display: "flex", gap: "0.75rem", alignItems: "center", flexWrap: "wrap" }}>
                    <Link href={`/schemes/${scheme.slug}`} className="btn btn-primary btn-sm">
                      {t("schemes.viewDetails", "View Details")}
                    </Link>
                    <button onClick={() => toggleExpand(scheme.scheme_id)} className="btn btn-ghost btn-sm">
                      {expanded ? t("recommendations.showLess", "Show less ↑") : t("eligibility.showDetails", "Show details ↓")}
                    </button>
                    {scheme.application_link && (
                      <a href={scheme.application_link} target="_blank" rel="noopener noreferrer" className="btn btn-accent btn-sm">
                        {t("schemes.applyNow", "Apply →")}
                      </a>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {/* Pagination */}
        {data && data.total > 30 && (
          <div style={{ display: "flex", justifyContent: "center", gap: "0.75rem", marginTop: "2rem" }}>
            <button
              className="btn btn-outline btn-sm"
              disabled={page <= 1}
              onClick={() => setPage((p) => Math.max(1, p - 1))}
            >
              {t("schemes.prevPage", "← Previous")}
            </button>
            <span style={{ padding: "0.5rem 1rem", fontSize: "0.875rem", color: "var(--text-muted)" }}>
              {t("schemes.pageOf", `Page ${data.page} of ${Math.ceil(data.total / 30)}`, { current: data.page, total: Math.ceil(data.total / 30) })}
            </span>
            <button
              className="btn btn-outline btn-sm"
              disabled={page * 30 >= data.total}
              onClick={() => setPage((p) => p + 1)}
            >
              {t("schemes.nextPage", "Next →")}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
