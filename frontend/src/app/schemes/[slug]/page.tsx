"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import api from "@/lib/api";
import Navbar from "@/components/Navbar";
import { useLanguage } from "@/context/LanguageContext";

interface SchemeDetail {
  id: number;
  scheme_name: string;
  slug: string;
  details: string;
  benefits: string;
  eligibility: string;
  application_process: string;
  documents_required: string;
  level: string;
  scheme_category: string;
  official_website: string;
  application_link: string;
  version: number;
  view_count: number;
}

interface EligibilityResult {
  status: string;
  score: number;
  matched_criteria: string[];
  failed_criteria: (string | { criterion?: string; reason?: string })[];
  missing_documents: string[];
  suggestions: string[];
  explanation: string;
}

export default function SchemeDetailPage() {
  const params = useParams();
  const slug = params.slug as string;
  const { t } = useLanguage();
  const [scheme, setScheme] = useState<SchemeDetail | null>(null);
  const [eligibility, setEligibility] = useState<EligibilityResult | null>(null);
  const [checkingEligibility, setCheckingEligibility] = useState(false);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState("details");
  const [isLoggedIn, setIsLoggedIn] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem("access_token");
    setIsLoggedIn(!!token);
    loadScheme();
  }, [slug]);

  const loadScheme = async () => {
    try {
      const data = (await api.getScheme(slug)) as SchemeDetail;
      setScheme(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const checkEligibility = async () => {
    if (!scheme) return;
    setCheckingEligibility(true);
    try {
      const result = (await api.checkEligibility(scheme.id)) as EligibilityResult;
      setEligibility(result);
      setActiveTab("eligibility");
    } catch (err) {
      console.error(err);
    } finally {
      setCheckingEligibility(false);
    }
  };

  const saveScheme = async () => {
    if (!scheme) return;
    setSaving(true);
    try {
      await api.saveScheme(scheme.id);
      setSaved(true);
    } catch {
      // may already be saved
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div style={{ minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center" }}>
        <p style={{ color: "var(--text-muted)" }}>{t("common.loading", "Loading scheme...")}</p>
      </div>
    );
  }

  if (!scheme) {
    return (
      <div>
        <Navbar />
        <div className="container page" style={{ textAlign: "center" }}>
          <h2>{t("schemes.noSchemesFound", "Scheme not found")}</h2>
          <Link href="/schemes" className="btn btn-primary" style={{ marginTop: "1rem" }}>
            {t("nav.schemes", "Browse Schemes")}
          </Link>
        </div>
      </div>
    );
  }

  const tabs = [
    { id: "details", label: `📋 ${t("schemes.details", "Details")}` },
    { id: "eligibility", label: `✅ ${t("schemes.eligibility", "Eligibility")}` },
    { id: "benefits", label: `🎁 ${t("schemes.benefits", "Benefits")}` },
    { id: "application", label: `📝 ${t("schemes.howToApply", "How to Apply")}` },
    { id: "documents", label: `📄 ${t("schemes.documentsRequired", "Documents")}` },
  ];

  return (
    <div>
      <Navbar />

      <div className="container page">
        {/* Scheme Header */}
        <div
          className="card animate-slide-up"
          style={{
            marginBottom: "2rem",
            border: "none",
            background: "linear-gradient(135deg, #1a365d, #2b6cb0)",
            color: "white",
            padding: "2.5rem",
          }}
        >
          <div style={{ display: "flex", gap: "0.5rem", marginBottom: "1rem", flexWrap: "wrap" }}>
            <span className="badge" style={{ background: "rgba(255,255,255,0.2)", color: "white" }}>
              {scheme.level === "Central" ? t("schemes.centralLevel", "Central") : t("schemes.stateLevel", "State")}
            </span>
            {scheme.scheme_category && (
              <span className="badge" style={{ background: "rgba(255,255,255,0.15)", color: "white" }}>
                {scheme.scheme_category.split(",")[0].trim()}
              </span>
            )}
            <span className="badge" style={{ background: "rgba(255,255,255,0.1)", color: "white" }}>
              v{scheme.version}
            </span>
          </div>
          <h1 style={{ fontSize: "1.150rem", lineHeight: 1.3, marginBottom: "1rem" }}>{scheme.scheme_name}</h1>
          <div style={{ display: "flex", gap: "0.150rem", flexWrap: "wrap" }}>
            {isLoggedIn && (
              <>
                <button
                  onClick={checkEligibility}
                  className="btn btn-lg"
                  style={{ background: "white", color: "var(--primary)" }}
                  disabled={checkingEligibility}
                >
                  {checkingEligibility ? t("common.loading", "Checking...") : `✅ ${t("schemes.checkEligibility", "Check Eligibility")}`}
                </button>
                <button
                  onClick={saveScheme}
                  className="btn btn-lg"
                  style={{ background: "rgba(255,255,255,0.2)", color: "white" }}
                  disabled={saving || saved}
                >
                  {saved ? `❤️ ${t("schemes.savedScheme", "Saved")}` : saving ? "Saving..." : `🤍 ${t("schemes.saveScheme", "Save Scheme")}`}
                </button>
              </>
            )}
            {scheme.application_link && (
              <a
                href={scheme.application_link}
                target="_blank"
                rel="noopener noreferrer"
                className="btn btn-lg"
                style={{ background: "var(--accent)", color: "white" }}
              >
                {t("schemes.applyNow", "Apply Now →")}
              </a>
            )}
          </div>
        </div>

        {/* Eligibility Result */}
        {eligibility && (
          <div
            className="card animate-fade-in"
            style={{
              marginBottom: "2rem",
              borderLeft: `4px solid ${
                eligibility.status === "eligible"
                  ? "var(--success)"
                  : eligibility.status === "partially_eligible"
                    ? "var(--warning)"
                    : "var(--error)"
              }`,
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: "1rem", marginBottom: "1rem" }}>
              <div
                style={{
                  fontSize: "2rem",
                  width: "56px",
                  height: "56px",
                  borderRadius: "50%",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  background:
                    eligibility.status === "eligible"
                      ? "#ecfdf5"
                      : eligibility.status === "partially_eligible"
                        ? "#fffbeb"
                        : "#fef2f2",
                }}
              >
                {eligibility.status === "eligible" ? "✅" : eligibility.status === "partially_eligible" ? "⚠️" : "❌"}
              </div>
              <div>
                <h3
                  className={`status-${
                    eligibility.status === "eligible"
                      ? "eligible"
                      : eligibility.status === "partially_eligible"
                        ? "partial"
                        : "not-eligible"
                  }`}
                >
                  {eligibility.status === "eligible"
                    ? t("schemes.eligibleMsg", "You are Eligible!")
                    : eligibility.status === "partially_eligible"
                      ? t("common.partiallyEligible", "Partially Eligible")
                      : t("common.notEligible", "Not Eligible")}
                </h3>
                <div style={{ display: "flex", alignItems: "center", gap: "1rem", marginTop: "0.25rem" }}>
                  <span style={{ fontSize: "0.8150rem", color: "var(--text-muted)" }}>
                    {t("recommendations.score", "Score")}:{" "}
                    {eligibility.status === "not_eligible" ? 0 : Math.round(eligibility.score * 100)}%
                  </span>
                  <div className="progress-bar" style={{ width: "100px" }}>
                    <div
                      className={`progress-bar-fill ${
                        eligibility.status === "eligible"
                          ? "eligible"
                          : eligibility.status === "partially_eligible"
                            ? "partial"
                            : "not-eligible"
                      }`}
                      style={{
                        width: `${eligibility.status === "not_eligible" ? 0 : eligibility.score * 100}%`,
                      }}
                    />
                  </div>
                </div>
              </div>
            </div>

            {eligibility.matched_criteria.length > 0 && (
              <div style={{ marginBottom: "1rem" }}>
                <h4 style={{ fontSize: "0.8150rem", color: "var(--success)", marginBottom: "0.5rem" }}>
                  ✓ {t("recommendations.matchedCriteria", "Matched Criteria")}
                </h4>
                {eligibility.matched_criteria.map((c, i) => (
                  <div
                    key={i}
                    style={{
                      fontSize: "0.8150rem",
                      color: "var(--text-secondary)",
                      paddingLeft: "1rem",
                      marginBottom: "0.25rem",
                    }}
                  >
                    • {c}
                  </div>
                ))}
              </div>
            )}
            {eligibility.failed_criteria.length > 0 && (
              <div style={{ marginBottom: "1rem" }}>
                <h4 style={{ fontSize: "0.8150rem", color: "var(--error)", marginBottom: "0.5rem" }}>
                  ✗ {t("recommendations.failedCriteria", "Failed Criteria")}
                </h4>
                {eligibility.failed_criteria.map((c, i) => {
                  const text = typeof c === "object" && c !== null ? (c as { reason?: string }).reason || JSON.stringify(c) : String(c);
                  return (
                    <div
                      key={i}
                      style={{
                        fontSize: "0.8150rem",
                        color: "var(--text-secondary)",
                        paddingLeft: "1rem",
                        marginBottom: "0.25rem",
                      }}
                    >
                      • {text}
                    </div>
                  );
                })}
              </div>
            )}
            {eligibility.missing_documents.length > 0 && (
              <div>
                <h4 style={{ fontSize: "0.8150rem", color: "var(--warning)", marginBottom: "0.5rem" }}>
                  📄 {t("schemes.missingDocuments", "Missing Documents")}
                </h4>
                {eligibility.missing_documents.map((d, i) => (
                  <div
                    key={i}
                    style={{
                      fontSize: "0.8150rem",
                      color: "var(--text-secondary)",
                      paddingLeft: "1rem",
                      marginBottom: "0.25rem",
                    }}
                  >
                    • {d}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Tabs */}
        <div
          style={{
            display: "flex",
            gap: "0.25rem",
            borderBottom: "2px solid var(--border)",
            marginBottom: "1.5rem",
            overflowX: "auto",
          }}
        >
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`btn btn-ghost`}
              style={{
                borderBottom: activeTab === tab.id ? "2px solid var(--primary)" : "2px solid transparent",
                borderRadius: 0,
                color: activeTab === tab.id ? "var(--primary)" : "var(--text-muted)",
                fontWeight: activeTab === tab.id ? 700 : 500,
                whiteSpace: "nowrap",
              }}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Tab Content */}
        <div className="card animate-fade-in" style={{ minHeight: "200px" }}>
          {activeTab === "details" && (
            <div>
              <h3 style={{ marginBottom: "1rem" }}>{t("schemes.details", "Scheme Details")}</h3>
              <div style={{ whiteSpace: "pre-wrap", color: "var(--text-secondary)", lineHeight: 1.8 }}>
                {scheme.details || "No details available."}
              </div>
            </div>
          )}
          {activeTab === "eligibility" && (
            <div>
              <h3 style={{ marginBottom: "1rem" }}>{t("schemes.eligibility", "Eligibility Criteria")}</h3>
              <div style={{ whiteSpace: "pre-wrap", color: "var(--text-secondary)", lineHeight: 1.8 }}>
                {scheme.eligibility || "No eligibility criteria specified."}
              </div>
            </div>
          )}
          {activeTab === "benefits" && (
            <div>
              <h3 style={{ marginBottom: "1rem" }}>{t("schemes.benefits", "Benefits")}</h3>
              <div style={{ whiteSpace: "pre-wrap", color: "var(--text-secondary)", lineHeight: 1.8 }}>
                {scheme.benefits || "No benefits information available."}
              </div>
            </div>
          )}
          {activeTab === "application" && (
            <div>
              <h3 style={{ marginBottom: "1rem" }}>{t("schemes.howToApply", "How to Apply")}</h3>
              <div style={{ whiteSpace: "pre-wrap", color: "var(--text-secondary)", lineHeight: 1.8 }}>
                {scheme.application_process || "No application process information available."}
              </div>
              {scheme.official_website && (
                <div style={{ marginTop: "1.5rem" }}>
                  <a
                    href={scheme.official_website}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="btn btn-primary"
                  >
                    {t("schemes.officialWebsite", "Visit Official Website →")}
                  </a>
                </div>
              )}
            </div>
          )}
          {activeTab === "documents" && (
            <div>
              <h3 style={{ marginBottom: "1rem" }}>{t("schemes.documentsRequired", "Required Documents")}</h3>
              <div style={{ whiteSpace: "pre-wrap", color: "var(--text-secondary)", lineHeight: 1.8 }}>
                {scheme.documents_required || "No document requirements specified."}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
