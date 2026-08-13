"use client";

import { useState, useEffect, Suspense } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import api from "@/lib/api";

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
      const data = await api.search({ q, page: p, page_size: 12, category, level }) as {
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
        const results = await api.autocomplete(value) as string[];
        setAutocompleteResults(results);
        setShowAutocomplete(results.length > 0);
      } catch {
        setShowAutocomplete(false);
      }
    } else {
      setShowAutocomplete(false);
    }
  };

  return (
    <div>
      <nav className="nav">
        <div className="nav-inner">
          <Link href="/" className="nav-logo"><span style={{ fontSize: "1.5rem" }}>🏛️</span><span>GovScheme AI</span></Link>
          <div className="nav-links">
            <Link href="/schemes" className="nav-link">Schemes</Link>
            <Link href="/search" className="nav-link active">Search</Link>
            <Link href="/dashboard" className="nav-link">Dashboard</Link>
          </div>
        </div>
      </nav>

      <div className="container page">
        <div style={{ textAlign: "center", marginBottom: "3rem" }}>
          <h1 style={{ marginBottom: "0.75rem" }}>🔍 Search Government Schemes</h1>
          <p style={{ color: "var(--text-secondary)", maxWidth: "500px", margin: "0 auto" }}>
            Search across 3,400+ schemes by keyword, category, or state
          </p>
        </div>

        {/* Search Bar */}
        <form onSubmit={handleSearch} style={{ maxWidth: "700px", margin: "0 auto 2rem", position: "relative" }}>
          <div style={{ display: "flex", gap: "0.75rem" }}>
            <div style={{ flex: 1, position: "relative" }}>
              <input
                className="input"
                style={{ padding: "1rem 1.25rem", fontSize: "1rem" }}
                placeholder="e.g., farmer schemes in Maharashtra, scholarships for SC students..."
                value={query}
                onChange={(e) => handleAutocomplete(e.target.value)}
                onBlur={() => setTimeout(() => setShowAutocomplete(false), 200)}
              />
              {showAutocomplete && (
                <div style={{
                  position: "absolute", top: "100%", left: 0, right: 0, background: "var(--bg-card)",
                  border: "1px solid var(--border)", borderRadius: "var(--radius-sm)", marginTop: "4px",
                  boxShadow: "var(--shadow-lg)", zIndex: 50, maxHeight: "200px", overflow: "auto",
                }}>
                  {autocompleteResults.map((item, i) => (
                    <div key={i} onClick={() => { setQuery(item); setShowAutocomplete(false); doSearch(item, 1); }}
                      style={{
                        padding: "0.75rem 1rem", cursor: "pointer", fontSize: "0.9375rem",
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
            <button type="submit" className="btn btn-primary btn-lg">Search</button>
          </div>

          <div style={{ display: "flex", gap: "0.75rem", marginTop: "0.75rem" }}>
            <select className="select" value={category} onChange={(e) => setCategory(e.target.value)} style={{ maxWidth: "200px" }}>
              <option value="">All Categories</option>
              <option value="Agriculture">Agriculture</option>
              <option value="Education">Education</option>
              <option value="Health">Health</option>
              <option value="Business">Business</option>
              <option value="Women">Women</option>
              <option value="Housing">Housing</option>
            </select>
            <select className="select" value={level} onChange={(e) => setLevel(e.target.value)} style={{ maxWidth: "150px" }}>
              <option value="">All Levels</option>
              <option value="Central">Central</option>
              <option value="State">State</option>
            </select>
          </div>
        </form>

        {/* Suggestions */}
        {suggestions.length > 0 && (
          <div style={{ maxWidth: "700px", margin: "0 auto 2rem", display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
            <span style={{ fontSize: "0.875rem", color: "var(--text-muted)" }}>Suggestions:</span>
            {suggestions.map((s, i) => (
              <button key={i} className="btn btn-ghost btn-sm" onClick={() => { setQuery(s); doSearch(s, 1); }}
                style={{ fontSize: "0.8125rem" }}>
                {s}
              </button>
            ))}
          </div>
        )}

        {/* Results */}
        {loading ? (
          <div className="grid-cards">
            {[...Array(6)].map((_, i) => <div key={i} className="skeleton" style={{ height: "180px" }} />)}
          </div>
        ) : results.length > 0 ? (
          <>
            <p style={{ color: "var(--text-muted)", marginBottom: "1.5rem" }}>
              {total} result{total !== 1 ? "s" : ""} found
            </p>
            <div className="grid-cards">
              {results.map((scheme, i) => (
                <Link key={scheme.id} href={`/schemes/${scheme.slug}`} style={{ textDecoration: "none" }}>
                  <div className="card animate-fade-in" style={{ height: "100%", cursor: "pointer", animationDelay: `${i * 0.05}s` }}>
                    <div style={{ display: "flex", gap: "0.5rem", marginBottom: "0.75rem" }}>
                      <span className={`badge ${scheme.level === "Central" ? "badge-primary" : "badge-accent"}`}>{scheme.level}</span>
                      {scheme.scheme_category && (
                        <span className="badge badge-warning" style={{ fontSize: "0.6875rem" }}>
                          {scheme.scheme_category.split(",")[0].trim().substring(0, 20)}
                        </span>
                      )}
                    </div>
                    <h4 style={{ marginBottom: "0.75rem", color: "var(--text)", fontSize: "0.9375rem" }}>{scheme.scheme_name}</h4>
                    <p style={{
                      color: "var(--text-secondary)", fontSize: "0.8125rem", lineHeight: 1.5,
                      display: "-webkit-box", WebkitLineClamp: 3, WebkitBoxOrient: "vertical", overflow: "hidden",
                    }}>
                      {scheme.details?.substring(0, 200) || scheme.benefits?.substring(0, 200) || "View scheme details →"}
                    </p>
                  </div>
                </Link>
              ))}
            </div>
          </>
        ) : query ? (
          <div style={{ textAlign: "center", padding: "3rem" }}>
            <div style={{ fontSize: "3rem", marginBottom: "1rem" }}>🔍</div>
            <h3>No results found for &quot;{query}&quot;</h3>
            <p style={{ color: "var(--text-muted)", marginTop: "0.5rem" }}>Try different keywords or browse by category</p>
          </div>
        ) : null}
      </div>
    </div>
  );
}

export default function SearchPage() {
  return (
    <Suspense fallback={<div style={{ minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center" }}>Loading...</div>}>
      <SearchContent />
    </Suspense>
  );
}
