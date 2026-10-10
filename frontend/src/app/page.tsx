"use client";

import { useState } from "react";
import Link from "next/link";
import Navbar from "@/components/Navbar";
import { useLanguage } from "@/context/LanguageContext";

const CATEGORIES = [
  { name: "Agriculture", icon: "🌾", color: "#059669", key: "categories.agriculture" },
  { name: "Education & Learning", icon: "🎓", color: "#7c3aed", key: "categories.education" },
  { name: "Health & Wellness", icon: "🏥", color: "#dc2626", key: "categories.health" },
  { name: "Business & Entrepreneurship", icon: "💼", color: "#2563eb", key: "categories.business" },
  { name: "Social welfare & Empowerment", icon: "🤝", color: "#d97706", key: "categories.socialWelfare" },
  { name: "Women and Child", icon: "👩", color: "#ec4899", key: "categories.womenChild" },
  { name: "Housing & Shelter", icon: "🏠", color: "#0891b2", key: "categories.housing" },
  { name: "Skills & Employment", icon: "⚡", color: "#7c3aed", key: "categories.skillsEmployment" },
];

const STATS = [
  { value: "300", labelKey: "schemes.schemesAvailable", defaultLabel: "Government Schemes" },
  { value: "150", labelKey: "schemes.centralLevel", defaultLabel: "Central Schemes" },
  { value: "150", labelKey: "schemes.stateLevel", defaultLabel: "State Schemes" },
  { value: "10", labelKey: "nav.logoText", defaultLabel: "Languages Supported" },
];

export default function HomePage() {
  const { t } = useLanguage();
  const [searchQuery, setSearchQuery] = useState("");

  return (
    <div>
      <Navbar />

      {/* Hero Section */}
      <section className="hero-gradient" style={{ padding: "5rem 1.5rem", textAlign: "center" }}>
        <div className="container" style={{ maxWidth: "800px" }}>
          <div className="animate-slide-up">
            <span
              className="badge"
              style={{
                background: "rgba(255,255,255,0.15)",
                color: "white",
                marginBottom: "1.5rem",
                display: "inline-flex",
              }}
            >
              🇮🇳 Empowering Every Indian Citizen
            </span>
            <h1 style={{ fontSize: "3rem", fontWeight: 800, marginBottom: "1.5rem", lineHeight: 1.1 }}>
              {t("search.title", "Discover Government Schemes")}
              <span style={{ display: "block", color: "#fbbf24", marginTop: "0.5rem" }}>
                {t("recommendations.title", "Tailored for You")}
              </span>
            </h1>
            <p style={{ fontSize: "1.125rem", opacity: 0.9, marginBottom: "2.5rem", lineHeight: 1.7 }}>
              {t(
                "search.subtitle",
                "AI-powered platform to explore 3,300+ Central & State government schemes. Check eligibility, get personalized recommendations, and apply — in your language."
              )}
            </p>

            {/* Search Bar */}
            <div
              style={{
                display: "flex",
                gap: "0.150rem",
                maxWidth: "600px",
                margin: "0 auto",
                background: "rgba(255,255,255,0.15)",
                backdropFilter: "blur(8px)",
                padding: "0.5rem",
                borderRadius: "var(--radius)",
                border: "1px solid rgba(255,255,255,0.2)",
              }}
            >
              <input
                type="text"
                placeholder={t("schemes.searchPlaceholder", "Search for schemes, scholarships, benefits...")}
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && searchQuery) window.location.href = `/search?q=${searchQuery}`;
                }}
                style={{
                  flex: 1,
                  padding: "0.8150rem 1.25rem",
                  borderRadius: "var(--radius-sm)",
                  border: "none",
                  fontSize: "1rem",
                  background: "rgba(255,255,255,0.95)",
                  color: "#0f172a",
                  outline: "none",
                }}
              />
              <Link href={searchQuery ? `/search?q=${searchQuery}` : "/search"} className="btn btn-accent btn-lg">
                🔍 {t("common.search", "Search")}
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
              <div
                key={i}
                className="card-glass animate-fade-in"
                style={{
                  textAlign: "center",
                  padding: "1.5rem",
                  animationDelay: `${i * 0.1}s`,
                }}
              >
                <div style={{ fontSize: "2rem", fontWeight: 800, color: "var(--primary)" }}>{stat.value}</div>
                <div style={{ fontSize: "0.8150rem", color: "var(--text-muted)", fontWeight: 500 }}>
                  {t(stat.labelKey, stat.defaultLabel)}
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
            <h2 style={{ marginBottom: "0.150rem" }}>{t("schemes.allCategories", "Browse by Category")}</h2>
            <p style={{ color: "var(--text-secondary)", maxWidth: "600px", margin: "0 auto" }}>
              Explore schemes across major categories designed for farmers, students, women, businesses, and more.
            </p>
          </div>
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fill, minmax(240px, 1fr))",
              gap: "1rem",
              maxWidth: "1000px",
              margin: "0 auto",
            }}
          >
            {CATEGORIES.map((cat, i) => (
              <Link
                key={i}
                href={`/schemes?category=${encodeURIComponent(cat.name)}`}
                style={{ textDecoration: "none" }}
              >
                <div
                  className="card animate-fade-in"
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: "1rem",
                    cursor: "pointer",
                    animationDelay: `${i * 0.05}s`,
                  }}
                >
                  <div
                    style={{
                      width: "48px",
                      height: "48px",
                      borderRadius: "12px",
                      background: `${cat.color}15`,
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      fontSize: "1.5rem",
                      flexShrink: 0,
                    }}
                  >
                    {cat.icon}
                  </div>
                  <div>
                    <div style={{ fontWeight: 600, color: "var(--text)" }}>{t(cat.key, cat.name)}</div>
                    <div style={{ fontSize: "0.8125rem", color: "var(--text-muted)" }}>
                      {t("schemes.viewDetails", "Explore schemes →")}
                    </div>
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
            <h2 style={{ marginBottom: "0.150rem" }}>Powered by AI</h2>
            <p style={{ color: "var(--text-secondary)" }}>Smart features that make scheme discovery effortless</p>
          </div>
          <div className="grid-cards" style={{ maxWidth: "1100px", margin: "0 auto" }}>
            {[
              {
                icon: "🎯",
                title: t("recommendations.title", "Top 5 Recommendations"),
                desc: "AI evaluates strict eligibility gates to recommend only schemes you qualify for.",
              },
              {
                icon: "✅",
                title: t("eligibility.title", "Eligibility Checker"),
                desc: "Check if you qualify with strict hard constraints (SC/ST, State, Gender, Age, Income).",
              },
              {
                icon: "🤖",
                title: t("nav.aiChat", "Multilingual AI Chatbot"),
                desc: "Ask questions in English, Telugu, or Hindi. The chatbot auto-detects language and replies natively.",
              },
              {
                icon: "🔔",
                title: t("notifications.title", "Smart Notifications"),
                desc: "Get alerted when scheme rules change, deadlines approach, or new schemes match your profile.",
              },
              {
                icon: "🌐",
                title: "Multilingual Support",
                desc: "Complete dashboard localization in English, Telugu, and Hindi.",
              },
              {
                icon: "📊",
                title: "Zero False-Positives",
                desc: "Ineligible applicants always receive 0%, never 100% or misleading percentages.",
              },
            ].map((feature, i) => (
              <div key={i} className="card animate-fade-in" style={{ animationDelay: `${i * 0.08}s` }}>
                <div style={{ fontSize: "2rem", marginBottom: "1rem" }}>{feature.icon}</div>
                <h4 style={{ marginBottom: "0.5rem" }}>{feature.title}</h4>
                <p style={{ color: "var(--text-secondary)", fontSize: "0.93150rem", lineHeight: 1.6 }}>
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
              {t("auth.signup", "Get Started Free →")}
            </Link>
            <Link href="/schemes" className="btn btn-outline btn-lg">
              {t("nav.schemes", "Browse All Schemes")}
            </Link>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer style={{ background: "var(--primary-dark)", color: "white", padding: "3rem 1.5rem" }}>
        <div className="container">
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))",
              gap: "2rem",
              marginBottom: "2rem",
            }}
          >
            <div>
              <div
                style={{
                  fontSize: "1.25rem",
                  fontWeight: 800,
                  marginBottom: "1rem",
                  display: "flex",
                  alignItems: "center",
                  gap: "0.5rem",
                }}
              >
                🏛️ GovScheme AI
              </div>
              <p style={{ opacity: 0.7, fontSize: "0.8150rem", lineHeight: 1.6 }}>
                AI-powered platform to help Indian citizens discover and access government schemes.
              </p>
            </div>
            <div>
              <h4
                style={{
                  marginBottom: "1rem",
                  fontSize: "0.8150rem",
                  textTransform: "uppercase",
                  letterSpacing: "0.05em",
                }}
              >
                Platform
              </h4>
              <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
                <Link
                  href="/schemes"
                  style={{ color: "rgba(255,255,255,0.7)", textDecoration: "none", fontSize: "0.8150rem" }}
                >
                  {t("nav.schemes", "Browse Schemes")}
                </Link>
                <Link
                  href="/search"
                  style={{ color: "rgba(255,255,255,0.7)", textDecoration: "none", fontSize: "0.8150rem" }}
                >
                  {t("nav.search", "Search")}
                </Link>
                <Link
                  href="/chatbot"
                  style={{ color: "rgba(255,255,255,0.7)", textDecoration: "none", fontSize: "0.8150rem" }}
                >
                  {t("nav.aiChat", "AI Chatbot")}
                </Link>
              </div>
            </div>
            <div>
              <h4
                style={{
                  marginBottom: "1rem",
                  fontSize: "0.8150rem",
                  textTransform: "uppercase",
                  letterSpacing: "0.05em",
                }}
              >
                Categories
              </h4>
              <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
                <Link
                  href="/schemes?category=Education"
                  style={{ color: "rgba(255,255,255,0.7)", textDecoration: "none", fontSize: "0.8150rem" }}
                >
                  {t("categories.education", "Education")}
                </Link>
                <Link
                  href="/schemes?category=Agriculture"
                  style={{ color: "rgba(255,255,255,0.7)", textDecoration: "none", fontSize: "0.8150rem" }}
                >
                  {t("categories.agriculture", "Agriculture")}
                </Link>
                <Link
                  href="/schemes?category=Health"
                  style={{ color: "rgba(255,255,255,0.7)", textDecoration: "none", fontSize: "0.8150rem" }}
                >
                  {t("categories.health", "Health")}
                </Link>
                <Link
                  href="/schemes?category=Women"
                  style={{ color: "rgba(255,255,255,0.7)", textDecoration: "none", fontSize: "0.8150rem" }}
                >
                  {t("categories.womenChild", "Women")}
                </Link>
              </div>
            </div>
          </div>
          <div
            style={{
              borderTop: "1px solid rgba(255,255,255,0.1)",
              paddingTop: "1.5rem",
              textAlign: "center",
              opacity: 0.5,
              fontSize: "0.8125rem",
            }}
          >
            © {new Date().getFullYear()} GovScheme AI. All rights reserved. Made for Indian citizens 🇮🇳
          </div>
        </div>
      </footer>
    </div>
  );
}
