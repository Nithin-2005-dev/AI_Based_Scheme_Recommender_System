"use client";

import { useState, useEffect, Suspense } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import api from "@/lib/api";
import Navbar from "@/components/Navbar";
import { useLanguage } from "@/context/LanguageContext";

interface SearchResult {
  id: number;
  scheme_name: string;
  slug: string;
  details: string;
  benefits: string;
  level: string;
  scheme_category: string;
  view_count: number;
}

function SearchContent() {
  const searchParams = useSearchParams();
  const { t } = useLanguage();
  const [query, setQuery] = useState(searchParams.get("q") || "");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(false);
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [autocompleteResults, setAutocompleteResults] = useState<string[]>([]);
  const [showAutocomplete, setShowAutocomplete] = useState(false);
  const [category, setCategory] = useState("");
  const [level, setLevel] = useState("");

  useEffect(() => {
    const q = searchParams.get("q");
    if (q) {
      setQuery(q);
      doSearch(q, 1);
    }
  }, [searchParams]);

  const doSearch = async (q: string, p: number) => {
    setLoading(true);
    try {
      const data = (await api.search({ q, page: p, page_size: 12, category, level })) as {
        results: SearchResult[];
        total: number;
        suggestions: string[];
      };
      setResults(data.results || []);
      setTotal(data.total || 0);
      setSuggestions(data.suggestions || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    setShowAutocomplete(false);
    doSearch(query, 1);
  };

  const handleAutocomplete = async (value: string) => {
    setQuery(value);
    if (value.length >= 2) {
      try {
        const res = (await api.autocomplete(value)) as string[];
        setAutocompleteResults(res);
        setShowAutocomplete(res.length > 0);
      } catch {
        setShowAutocomplete(false);
      }
    } else {
      setShowAutocomplete(false);
    }
  };

  return (
    <div>
      <Navbar />

      <div className="container page">
        <div style={{ textAlign: "center", marginBottom: "3rem" }}>
          <h1 style={{ marginBottom: "0.150rem" }}>🔍 {t("search.title", "Search Government Schemes")}</h1>
          <p style={{ color: "var(--text-secondary)", maxWidth: "500px", margin: "0 auto" }}>
            {t("search.subtitle", "Search across 300+ schemes by keyword, category, or state")}
          </p>
        </div>

        {/* Search Bar */}
        <form onSubmit={handleSearch} style={{ maxWidth: "700px", margin: "0 auto 2rem", position: "relative" }}>
          <div style={{ display: "flex", gap: "0.150rem" }}>
            <div style={{ flex: 1, position: "relative" }}>
              <input
                className="input"
                style={{ padding: "1rem 1.25rem", fontSize: "1rem" }}
                placeholder={t("search.placeholder", "e.g., farmer schemes, scholarships for SC students...")}
                value={query}
                onChange={(e) => handleAutocomplete(e.target.value)}
                onBlur={() => setTimeout(() => setShowAutocomplete(false), 200)}
              />
              {showAutocomplete && (
                <div
                  style={{
                    position: "absolute",
                    top: "100%",
                    left: 0,
                    right: 0,
                    background: "var(--bg-card)",
                    border: "1px solid var(--border)",
                    borderRadius: "var(--radius-sm)",
                    marginTop: "4px",
                    boxShadow: "var(--shadow-lg)",
                    zIndex: 50,
                    maxHeight: "200px",
                    overflow: "auto",
                  }}
                >
                  {autocompleteResults.map((item, i) => (
                    <div
                      key={i}
                      onClick={() => {
                        setQuery(item);
                        setShowAutocomplete(false);
                        doSearch(item, 1);
                      }}
                      style={{
                        padding: "0.150rem 1rem",
                        cursor: "pointer",
                        fontSize: "0.93150rem",
                        borderBottom: "1px solid var(--border)",
                      }}
                      onMouseEnter={(e) => (e.currentTarget.style.background = "var(--bg-sidebar)")}
                      onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}
                    >
                      {item}
                    </div>
                  ))}
                </div>
              )}
            </div>
            <button type="submit" className="btn btn-primary btn-lg">
              {t("common.search", "Search")}
            </button>
          </div>

          <div style={{ display: "flex", gap: "0.150rem", marginTop: "0.150rem", flexWrap: "wrap" }}>
            <select
              className="select"
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              style={{ maxWidth: "200px" }}
            >
              <option value="">{t("schemes.allCategories", "All Categories")}</option>
              <option value="Agriculture">{t("categories.agriculture", "Agriculture")}</option>
              <option value="Education">{t("categories.education", "Education")}</option>
              <option value="Health">{t("categories.health", "Health")}</option>
              <option value="Business">{t("categories.business", "Business")}</option>
              <option value="Women">{t("categories.womenChild", "Women")}</option>
              <option value="Housing">{t("categories.housing", "Housing")}</option>
            </select>
            <select
              className="select"
              value={level}
              onChange={(e) => setLevel(e.target.value)}
              style={{ maxWidth: "300px" }}
            >
              <option value="">{t("schemes.allLevels", "All Levels")}</option>
              <option value="Central">{t("schemes.centralLevel", "Central")}</option>
              <option value="State">{t("schemes.stateLevel", "State")}</option>
            </select>
          </div>
        </form>

        {/* Suggestions */}
        {suggestions.length > 0 && (
          <div style={{ maxWidth: "700px", margin: "0 auto 2rem", display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
            <span style={{ fontSize: "0.8150rem", color: "var(--text-muted)" }}>
              {t("search.suggestions", "Suggestions")}:
            </span>
            {suggestions.map((s, i) => (
              <button
                key={i}
                className="btn btn-ghost btn-sm"
                onClick={() => {
                  setQuery(s);
                  doSearch(s, 1);
                }}
                style={{ fontSize: "0.8125rem" }}
              >
                {s}
              </button>
            ))}
          </div>
        )}

        {/* Results */}
        {loading ? (
          <div className="grid-cards">
            {[...Array(6)].map((_, i) => (
              <div key={i} className="skeleton" style={{ height: "180px" }} />
            ))}
          </div>
        ) : results.length > 0 ? (
          <>
            <p style={{ color: "var(--text-muted)", marginBottom: "1.5rem" }}>
              {t("search.resultsCount", `${total} result${total !== 1 ? "s" : ""} found`, { count: total })}
            </p>
            <div className="grid-cards">
              {results.map((scheme, i) => (
                <Link key={scheme.id} href={`/schemes/${scheme.slug}`} style={{ textDecoration: "none" }}>
                  <div
                    className="card animate-fade-in"
                    style={{ height: "100%", cursor: "pointer", animationDelay: `${i * 0.05}s` }}
                  >
                    <div style={{ display: "flex", gap: "0.5rem", marginBottom: "0.150rem" }}>
                      <span className={`badge ${scheme.level === "Central" ? "badge-primary" : "badge-accent"}`}>
                        {scheme.level === "Central" ? t("schemes.centralLevel", "Central") : t("schemes.stateLevel", "State")}
                      </span>
                      {scheme.scheme_category && (
                        <span className="badge badge-warning" style={{ fontSize: "0.68150rem" }}>
                          {scheme.scheme_category.split(",")[0].trim().substring(0, 20)}
                        </span>
                      )}
                    </div>
                    <h4 style={{ marginBottom: "0.150rem", color: "var(--text)", fontSize: "0.93150rem" }}>
                      {scheme.scheme_name}
                    </h4>
                    <p
                      style={{
                        color: "var(--text-secondary)",
                        fontSize: "0.8125rem",
                        lineHeight: 1.5,
                        display: "-webkit-box",
                        WebkitLineClamp: 3,
                        WebkitBoxOrient: "vertical",
                        overflow: "hidden",
                      }}
                    >
                      {scheme.details?.substring(0, 200) || scheme.benefits?.substring(0, 200) || t("schemes.viewDetails", "View scheme details →")}
                    </p>
                  </div>
                </Link>
              ))}
            </div>
          </>
        ) : query ? (
          <div style={{ textAlign: "center", padding: "3rem" }}>
            <div style={{ fontSize: "3rem", marginBottom: "1rem" }}>🔍</div>
            <h3>
              {t("search.noResults", `No results found for "${query}"`, { query })}
            </h3>
            <p style={{ color: "var(--text-muted)", marginTop: "0.5rem" }}>
              {t("schemes.noSchemesDesc", "Try different keywords or browse by category")}
            </p>
          </div>
        ) : null}
      </div>
    </div>
  );
}

export default function SearchPage() {
  return (
    <Suspense
      fallback={
        <div style={{ minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center" }}>
          Loading...
        </div>
      }
    >
      <SearchContent />
    </Suspense>
  );
}
