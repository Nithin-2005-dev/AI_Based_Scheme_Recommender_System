"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import api from "@/lib/api";

const CATEGORIES = [
  { name: "Agriculture", icon: "🌾", color: "#059669" },
  { name: "Education & Learning", icon: "🎓", color: "#7c3aed" },
  { name: "Health & Wellness", icon: "🏥", color: "#dc2626" },
  { name: "Business & Entrepreneurship", icon: "💼", color: "#2563eb" },
  { name: "Social welfare & Empowerment", icon: "🤝", color: "#d97706" },
  { name: "Women and Child", icon: "👩", color: "#ec4899" },
  { name: "Housing & Shelter", icon: "🏠", color: "#0891b2" },
  { name: "Skills & Employment", icon: "⚡", color: "#7c3aed" },
];

const STATS = [
  { value: "3,400+", label: "Government Schemes" },
  { value: "541", label: "Central Schemes" },
  { value: "2,859", label: "State Schemes" },
  { value: "10", label: "Languages" },
];

export default function HomePage() {
  const [searchQuery, setSearchQuery] = useState("");
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [darkMode, setDarkMode] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem("access_token");
    setIsLoggedIn(!!token);
    const theme = localStorage.getItem("theme");
    if (theme === "dark") {
      setDarkMode(true);
      document.documentElement.setAttribute("data-theme", "dark");
    }
  }, []);

  const toggleDarkMode = () => {
    const newMode = !darkMode;
    setDarkMode(newMode);
    document.documentElement.setAttribute("data-theme", newMode ? "dark" : "light");
    localStorage.setItem("theme", newMode ? "dark" : "light");
  };

  return (
    <div>
      {/* Navigation */}
      <nav className="nav">
        <div className="nav-inner">
          <Link href="/" className="nav-logo">
            <span style={{ fontSize: "1.75rem" }}>🏛️</span>
            <span>GovScheme AI</span>
          </Link>
          <div className="nav-links">
            <Link href="/schemes" className="nav-link">Schemes</Link>
            <Link href="/search" className="nav-link">Search</Link>
            {isLoggedIn ? (
              <>
                <Link href="/dashboard" className="nav-link">Dashboard</Link>
                <Link href="/eligibility" className="nav-link">Eligibility</Link>
                <Link href="/recommendations" className="nav-link">For You</Link>
                <Link href="/chatbot" className="nav-link">AI Chat</Link>
                <Link href="/notifications" className="nav-link" style={{ position: "relative" }}>
                  🔔
                </Link>
                <Link href="/profile" className="nav-link">Profile</Link>
              </>
            ) : (
              <>
                <Link href="/auth/login" className="btn btn-outline btn-sm">Login</Link>
                <Link href="/auth/signup" className="btn btn-primary btn-sm">Sign Up</Link>
              </>
            )}
            <button onClick={toggleDarkMode} className="btn btn-ghost btn-sm" aria-label="Toggle dark mode">
              {darkMode ? "☀️" : "🌙"}
            </button>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="hero-gradient" style={{ padding: "5rem 1.5rem", textAlign: "center" }}>
        <div className="container" style={{ maxWidth: "800px" }}>
          <div className="animate-slide-up">
            <span className="badge" style={{ background: "rgba(255,255,255,0.15)", color: "white", marginBottom: "1.5rem", display: "inline-flex" }}>
              🇮🇳 Empowering Every Indian Citizen
            </span>
            <h1 style={{ fontSize: "3rem", fontWeight: 800, marginBottom: "1.5rem", lineHeight: 1.1 }}>
              Discover Government Schemes
              <span style={{ display: "block", color: "#fbbf24", marginTop: "0.5rem" }}>
                Tailored for You
              </span>
            </h1>
            <p style={{ fontSize: "1.125rem", opacity: 0.9, marginBottom: "2.5rem", lineHeight: 1.7 }}>
              AI-powered platform to explore 3,400+ Central & State government schemes.
              Check eligibility, get personalized recommendations, and apply — in your language.
            </p>

            {/* Search Bar */}
            <div style={{
              display: "flex", gap: "0.75rem", maxWidth: "600px", margin: "0 auto",
              background: "rgba(255,255,255,0.15)", backdropFilter: "blur(8px)",
              padding: "0.5rem", borderRadius: "var(--radius)", border: "1px solid rgba(255,255,255,0.2)",
            }}>
              <input
                type="text"
                placeholder="Search for schemes, scholarships, benefits..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyDown={(e) => { if (e.key === "Enter" && searchQuery) window.location.href = `/search?q=${searchQuery}`; }}
                style={{
                  flex: 1, padding: "0.875rem 1.25rem", borderRadius: "var(--radius-sm)",
                  border: "none", fontSize: "1rem", background: "rgba(255,255,255,0.95)",
                  color: "#0f172a", outline: "none",
                }}
              />
              <Link
                href={searchQuery ? `/search?q=${searchQuery}` : "/search"}
                className="btn btn-accent btn-lg"
              >
                🔍 Search
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Stats */}
      <section style={{ padding: "3rem 1.5rem", marginTop: "-2rem" }}>
        <div className="container">
          <div className="grid-stats" style={{ maxWidth: "900px", margin: "0 auto" }}>
            {STATS.map((stat, i) => (
              <div key={i} className="card-glass animate-fade-in" style={{
                textAlign: "center", padding: "1.5rem", animationDelay: `${i * 0.1}s`,
              }}>
                <div style={{ fontSize: "2rem", fontWeight: 800, color: "var(--primary)" }}>
                  {stat.value}
                </div>
                <div style={{ fontSize: "0.875rem", color: "var(--text-muted)", fontWeight: 500 }}>
                  {stat.label}
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Categories */}
      <section style={{ padding: "4rem 1.5rem" }}>
        <div className="container">
          <div style={{ textAlign: "center", marginBottom: "3rem" }}>
            <h2 style={{ marginBottom: "0.75rem" }}>Browse by Category</h2>
            <p style={{ color: "var(--text-secondary)", maxWidth: "600px", margin: "0 auto" }}>
              Explore schemes across 18+ categories designed for farmers, students, women, businesses, and more.
            </p>
          </div>
          <div style={{
            display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(240px, 1fr))",
            gap: "1rem", maxWidth: "1000px", margin: "0 auto",
          }}>
            {CATEGORIES.map((cat, i) => (
              <Link key={i} href={`/schemes?category=${encodeURIComponent(cat.name)}`} style={{ textDecoration: "none" }}>
                <div className="card animate-fade-in" style={{
                  display: "flex", alignItems: "center", gap: "1rem",
                  cursor: "pointer", animationDelay: `${i * 0.05}s`,
                }}>
                  <div style={{
                    width: "48px", height: "48px", borderRadius: "12px",
                    background: `${cat.color}15`, display: "flex",
                    alignItems: "center", justifyContent: "center", fontSize: "1.5rem", flexShrink: 0,
                  }}>
                    {cat.icon}
                  </div>
                  <div>
                    <div style={{ fontWeight: 600, color: "var(--text)" }}>{cat.name}</div>
                    <div style={{ fontSize: "0.8125rem", color: "var(--text-muted)" }}>Explore schemes →</div>
                  </div>
                </div>
              </Link>
            ))}
          </div>
        </div>
      </section>

      {/* Features */}
      <section style={{ padding: "4rem 1.5rem", background: "var(--bg-sidebar)" }}>
        <div className="container">
          <div style={{ textAlign: "center", marginBottom: "3rem" }}>
            <h2 style={{ marginBottom: "0.75rem" }}>Powered by AI</h2>
            <p style={{ color: "var(--text-secondary)" }}>Smart features that make scheme discovery effortless</p>
          </div>
          <div className="grid-cards" style={{ maxWidth: "1100px", margin: "0 auto" }}>
            {[
              { icon: "🎯", title: "Personalized Recommendations", desc: "AI analyzes your profile to recommend the top 5 schemes you're most likely eligible for." },
              { icon: "✅", title: "Eligibility Checker", desc: "Instantly check if you qualify for any scheme with detailed condition matching." },
              { icon: "🤖", title: "AI Chatbot", desc: "Ask questions in plain language. Get answers from official scheme documents with citations." },
              { icon: "🔔", title: "Smart Notifications", desc: "Get alerted when scheme rules change, deadlines approach, or new schemes match your profile." },
              { icon: "🌐", title: "10 Languages", desc: "Access everything in English, Hindi, Telugu, Tamil, Kannada, Malayalam, Marathi, Bengali, Gujarati, or Punjabi." },
              { icon: "📊", title: "Explainable AI", desc: "Every recommendation explains why it was suggested and which conditions matched or failed." },
            ].map((feature, i) => (
              <div key={i} className="card animate-fade-in" style={{ animationDelay: `${i * 0.08}s` }}>
                <div style={{ fontSize: "2rem", marginBottom: "1rem" }}>{feature.icon}</div>
                <h4 style={{ marginBottom: "0.5rem" }}>{feature.title}</h4>
                <p style={{ color: "var(--text-secondary)", fontSize: "0.9375rem", lineHeight: 1.6 }}>
                  {feature.desc}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section style={{ padding: "5rem 1.5rem", textAlign: "center" }}>
        <div className="container" style={{ maxWidth: "600px" }}>
          <h2 style={{ marginBottom: "1rem" }}>Ready to Discover Your Benefits?</h2>
          <p style={{ color: "var(--text-secondary)", marginBottom: "2rem" }}>
            Create your profile and let AI find the best government schemes for you.
          </p>
          <div style={{ display: "flex", gap: "1rem", justifyContent: "center", flexWrap: "wrap" }}>
            <Link href="/auth/signup" className="btn btn-primary btn-lg">
              Get Started Free →
            </Link>
            <Link href="/schemes" className="btn btn-outline btn-lg">
              Browse All Schemes
            </Link>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer style={{
        background: "var(--primary-dark)", color: "white", padding: "3rem 1.5rem",
      }}>
        <div className="container">
          <div style={{
            display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))",
            gap: "2rem", marginBottom: "2rem",
          }}>
            <div>
              <div style={{ fontSize: "1.25rem", fontWeight: 800, marginBottom: "1rem", display: "flex", alignItems: "center", gap: "0.5rem" }}>
                🏛️ GovScheme AI
              </div>
              <p style={{ opacity: 0.7, fontSize: "0.875rem", lineHeight: 1.6 }}>
                AI-powered platform to help Indian citizens discover and access government schemes.
              </p>
            </div>
            <div>
              <h4 style={{ marginBottom: "1rem", fontSize: "0.875rem", textTransform: "uppercase", letterSpacing: "0.05em" }}>Platform</h4>
              <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
                <Link href="/schemes" style={{ color: "rgba(255,255,255,0.7)", textDecoration: "none", fontSize: "0.875rem" }}>Browse Schemes</Link>
                <Link href="/search" style={{ color: "rgba(255,255,255,0.7)", textDecoration: "none", fontSize: "0.875rem" }}>Search</Link>
                <Link href="/chatbot" style={{ color: "rgba(255,255,255,0.7)", textDecoration: "none", fontSize: "0.875rem" }}>AI Chatbot</Link>
              </div>
            </div>
            <div>
              <h4 style={{ marginBottom: "1rem", fontSize: "0.875rem", textTransform: "uppercase", letterSpacing: "0.05em" }}>Categories</h4>
              <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
                <Link href="/schemes?category=Education" style={{ color: "rgba(255,255,255,0.7)", textDecoration: "none", fontSize: "0.875rem" }}>Education</Link>
                <Link href="/schemes?category=Agriculture" style={{ color: "rgba(255,255,255,0.7)", textDecoration: "none", fontSize: "0.875rem" }}>Agriculture</Link>
                <Link href="/schemes?category=Health" style={{ color: "rgba(255,255,255,0.7)", textDecoration: "none", fontSize: "0.875rem" }}>Health</Link>
                <Link href="/schemes?category=Women" style={{ color: "rgba(255,255,255,0.7)", textDecoration: "none", fontSize: "0.875rem" }}>Women</Link>
              </div>
            </div>
            <div>
              <h4 style={{ marginBottom: "1rem", fontSize: "0.875rem", textTransform: "uppercase", letterSpacing: "0.05em" }}>Legal</h4>
              <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
                <span style={{ color: "rgba(255,255,255,0.7)", fontSize: "0.875rem" }}>Privacy Policy</span>
                <span style={{ color: "rgba(255,255,255,0.7)", fontSize: "0.875rem" }}>Terms of Service</span>
                <span style={{ color: "rgba(255,255,255,0.7)", fontSize: "0.875rem" }}>Accessibility</span>
              </div>
            </div>
          </div>
          <div style={{ borderTop: "1px solid rgba(255,255,255,0.1)", paddingTop: "1.5rem", textAlign: "center", opacity: 0.5, fontSize: "0.8125rem" }}>
            © {new Date().getFullYear()} GovScheme AI. All rights reserved. Made for Indian citizens 🇮🇳
          </div>
        </div>
      </footer>
    </div>
  );
}
