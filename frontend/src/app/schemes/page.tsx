"use client";

import { useState, useEffect, Suspense } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import api from "@/lib/api";

interface Scheme {
  id: number;
  scheme_name: string;
  slug: string;
  details: string;
  benefits: string;
  level: string;
  scheme_category: string;
  view_count: number;
}

function SchemesContent() {
  const searchParams = useSearchParams();
  const [schemes, setSchemes] = useState<Scheme[]>([]);
  const [categories, setCategories] = useState<{ name: string; count: number }[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [loading, setLoading] = useState(true);
  const [selectedCategory, setSelectedCategory] = useState(searchParams.get("category") || "");
  const [selectedLevel, setSelectedLevel] = useState("");
  const [searchQuery, setSearchQuery] = useState("");

  useEffect(() => {
    loadSchemes();
    loadCategories();
  }, [page, selectedCategory, selectedLevel]);

  const loadSchemes = async () => {
    setLoading(true);
    try {
      const data = await api.getSchemes({
        page,
        page_size: 12,
        category: selectedCategory,
        level: selectedLevel,
        search: searchQuery,
      }) as { schemes: Scheme[]; total: number; total_pages: number };
      setSchemes(data.schemes || []);
      setTotal(data.total || 0);
      setTotalPages(data.total_pages || 1);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const loadCategories = async () => {
    try {
      const cats = await api.getCategories() as { name: string; count: number }[];
      setCategories(cats.slice(0, 15));
    } catch (err) {
      console.error(err);
    }
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    loadSchemes();
  };

  return (
    <div>
      <nav className="nav">
        <div className="nav-inner">
          <Link href="/" className="nav-logo">
            <span style={{ fontSize: "1.5rem" }}>🏛️</span>
            <span>GovScheme AI</span>
          </Link>
          <div className="nav-links">
            <Link href="/dashboard" className="nav-link">Dashboard</Link>
            <Link href="/schemes" className="nav-link active">Schemes</Link>
            <Link href="/search" className="nav-link">Search</Link>
            <Link href="/recommendations" className="nav-link">For You</Link>
            <Link href="/chatbot" className="nav-link">AI Chat</Link>
          </div>
        </div>
      </nav>

      <div className="container page">
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "2rem", flexWrap: "wrap", gap: "1rem" }}>
          <div>
            <h1>Government Schemes</h1>
            <p style={{ color: "var(--text-secondary)" }}>{total.toLocaleString()} schemes available</p>
          </div>
        </div>

        {/* Filters */}
        <div className="card" style={{ marginBottom: "2rem", display: "flex", gap: "1rem", flexWrap: "wrap", alignItems: "flex-end" }}>
          <form onSubmit={handleSearch} style={{ flex: 1, minWidth: "200px" }}>
            <label className="label">Search</label>
            <div style={{ display: "flex", gap: "0.5rem" }}>
              <input className="input" placeholder="Search schemes..." value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)} />
              <button type="submit" className="btn btn-primary">Search</button>
            </div>
          </form>
          <div style={{ minWidth: "180px" }}>
            <label className="label">Category</label>
            <select className="select" value={selectedCategory} onChange={(e) => { setSelectedCategory(e.target.value); setPage(1); }}>
              <option value="">All Categories</option>
              {categories.map((cat) => (
                <option key={cat.name} value={cat.name}>{cat.name} ({cat.count})</option>
              ))}
            </select>
          </div>
          <div style={{ minWidth: "140px" }}>
            <label className="label">Level</label>
            <select className="select" value={selectedLevel} onChange={(e) => { setSelectedLevel(e.target.value); setPage(1); }}>
              <option value="">All</option>
              <option value="Central">Central</option>
              <option value="State">State</option>
            </select>
          </div>
        </div>

        {/* Scheme List */}
        {loading ? (
          <div className="grid-cards">
            {[...Array(6)].map((_, i) => (
              <div key={i} className="skeleton" style={{ height: "200px" }} />
            ))}
          </div>
        ) : schemes.length === 0 ? (
          <div className="card" style={{ textAlign: "center", padding: "3rem" }}>
            <div style={{ fontSize: "3rem", marginBottom: "1rem" }}>🔍</div>
            <h3 style={{ marginBottom: "0.5rem" }}>No schemes found</h3>
            <p style={{ color: "var(--text-muted)" }}>Try adjusting your filters or search query</p>
          </div>
        ) : (
          <>
            <div className="grid-cards">
              {schemes.map((scheme, i) => (
                <Link key={scheme.id} href={`/schemes/${scheme.slug}`} style={{ textDecoration: "none" }}>
                  <div className="card animate-fade-in" style={{
                    height: "100%", cursor: "pointer", animationDelay: `${i * 0.05}s`,
                  }}>
                    <div style={{ display: "flex", gap: "0.5rem", marginBottom: "0.75rem" }}>
                      <span className={`badge ${scheme.level === "Central" ? "badge-primary" : "badge-accent"}`}>
                        {scheme.level}
                      </span>
                      {scheme.scheme_category && (
                        <span className="badge badge-warning" style={{ fontSize: "0.6875rem" }}>
                          {scheme.scheme_category.split(",")[0].trim().substring(0, 25)}
                        </span>
                      )}
                    </div>
                    <h4 style={{ marginBottom: "0.75rem", color: "var(--text)", lineHeight: 1.3, fontSize: "0.9375rem" }}>
                      {scheme.scheme_name}
                    </h4>
                    <p style={{
                      color: "var(--text-secondary)", fontSize: "0.8125rem", lineHeight: 1.5,
                      display: "-webkit-box", WebkitLineClamp: 3, WebkitBoxOrient: "vertical", overflow: "hidden",
                    }}>
                      {scheme.details?.substring(0, 200) || "View scheme details →"}
                    </p>
                    <div style={{ marginTop: "auto", paddingTop: "0.75rem", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                      <span style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
                        👁️ {scheme.view_count} views
                      </span>
                      <span style={{ color: "var(--primary-light)", fontSize: "0.8125rem", fontWeight: 600 }}>
                        View Details →
                      </span>
                    </div>
                  </div>
                </Link>
              ))}
            </div>

            {/* Pagination */}
            <div style={{ display: "flex", justifyContent: "center", gap: "0.5rem", marginTop: "2rem" }}>
              <button className="btn btn-outline btn-sm" disabled={page <= 1} onClick={() => setPage(page - 1)}>
                ← Previous
              </button>
              <span style={{ display: "flex", alignItems: "center", padding: "0 1rem", color: "var(--text-muted)", fontSize: "0.875rem" }}>
                Page {page} of {totalPages}
              </span>
              <button className="btn btn-outline btn-sm" disabled={page >= totalPages} onClick={() => setPage(page + 1)}>
                Next →
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

export default function SchemesPage() {
  return (
    <Suspense fallback={<div style={{ minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center" }}>Loading...</div>}>
      <SchemesContent />
    </Suspense>
  );
}
