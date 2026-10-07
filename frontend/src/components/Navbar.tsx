"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useLanguage } from "@/context/LanguageContext";
import { SupportedLanguage } from "@/locales";
import api from "@/lib/api";

interface NavbarProps {
  unreadCount?: number;
}

export default function Navbar({ unreadCount = 0 }: NavbarProps) {
  const pathname = usePathname();
  const router = useRouter();
  const { language, setLanguage, t, supportedLanguages } = useLanguage();
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [unread, setUnread] = useState(unreadCount);
  const [darkMode, setDarkMode] = useState(false);
  const [langMenuOpen, setLangMenuOpen] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem("access_token");
    setIsLoggedIn(!!token);

    const theme = localStorage.getItem("theme");
    if (theme === "dark") {
      setDarkMode(true);
      document.documentElement.setAttribute("data-theme", "dark");
    }

    if (token) {
      api.getUnreadCount()
        .then((data) => setUnread(data.unread_count || 0))
        .catch(() => {});
    }
  }, []);

  const toggleDarkMode = () => {
    const next = !darkMode;
    setDarkMode(next);
    document.documentElement.setAttribute("data-theme", next ? "dark" : "light");
    localStorage.setItem("theme", next ? "dark" : "light");
  };

  const handleLogout = async () => {
    try {
      await api.logout();
    } catch {
      // ignore
    } finally {
      setIsLoggedIn(false);
      router.push("/auth/login");
    }
  };

  return (
    <nav className="nav" style={{ position: "sticky", top: 0, zIndex: 100 }}>
      <div className="nav-inner" style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        {/* Logo */}
        <Link href="/" className="nav-logo" style={{ display: "flex", alignItems: "center", gap: "0.5rem", textDecoration: "none" }}>
          <span style={{ fontSize: "1.75rem" }}>🏛️</span>
          <span style={{ fontWeight: 800, fontSize: "1.25rem", color: "var(--primary)" }}>{t("nav.logoText", "GovScheme AI")}</span>
        </Link>

        {/* Links */}
        <div className="nav-links" style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
          <Link href="/schemes" className={`nav-link ${pathname === "/schemes" ? "active" : ""}`}>
            {t("nav.schemes", "Schemes")}
          </Link>
          <Link href="/search" className={`nav-link ${pathname === "/search" ? "active" : ""}`}>
            {t("nav.search", "Search")}
          </Link>

          {isLoggedIn ? (
            <>
              <Link href="/dashboard" className={`nav-link ${pathname === "/dashboard" ? "active" : ""}`}>
                {t("nav.dashboard", "Dashboard")}
              </Link>
              <Link href="/eligibility" className={`nav-link ${pathname === "/eligibility" ? "active" : ""}`}>
                {t("nav.eligibility", "Eligibility")}
              </Link>
              <Link href="/recommendations" className={`nav-link ${pathname === "/recommendations" ? "active" : ""}`}>
                {t("nav.recommendations", "For You")}
              </Link>
              <Link href="/chatbot" className={`nav-link ${pathname === "/chatbot" ? "active" : ""}`}>
                {t("nav.aiChat", "AI Chat")}
              </Link>
              <Link href="/notifications" className={`nav-link ${pathname === "/notifications" ? "active" : ""}`} style={{ position: "relative" }}>
                🔔
                {unread > 0 && (
                  <span
                    style={{
                      position: "absolute",
                      top: "-4px",
                      right: "-8px",
                      minWidth: "18px",
                      height: "18px",
                      background: "var(--error)",
                      borderRadius: "9999px",
                      fontSize: "0.6875rem",
                      color: "white",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      fontWeight: 700,
                      padding: "0 4px",
                    }}
                  >
                    {unread > 99 ? "99+" : unread}
                  </span>
                )}
              </Link>
              <Link href="/profile" className={`nav-link ${pathname === "/profile" ? "active" : ""}`}>
                {t("nav.profile", "Profile")}
              </Link>
            </>
          ) : null}

          {/* Language Selector Dropdown */}
          <div style={{ position: "relative" }}>
            <button
              onClick={() => setLangMenuOpen(!langMenuOpen)}
              className="btn btn-ghost btn-sm"
              style={{
                display: "flex",
                alignItems: "center",
                gap: "0.35rem",
                padding: "0.4rem 0.75rem",
                borderRadius: "var(--radius-sm)",
                border: "1px solid var(--border)",
                background: "var(--bg-card)",
                cursor: "pointer",
                fontWeight: 600,
                fontSize: "0.875rem",
              }}
              title="Switch Language"
            >
              <span>{supportedLanguages.find((l) => l.code === language)?.flag || "🌐"}</span>
              <span>{supportedLanguages.find((l) => l.code === language)?.nativeName || "Language"}</span>
              <span style={{ fontSize: "0.65rem" }}>▼</span>
            </button>

            {langMenuOpen && (
              <div
                style={{
                  position: "absolute",
                  right: 0,
                  top: "115%",
                  background: "var(--bg-card)",
                  border: "1px solid var(--border)",
                  borderRadius: "var(--radius)",
                  boxShadow: "var(--shadow-lg)",
                  minWidth: "150px",
                  zIndex: 1000,
                  overflow: "hidden",
                }}
              >
                {supportedLanguages.map((opt) => (
                  <button
                    key={opt.code}
                    onClick={() => {
                      setLanguage(opt.code as SupportedLanguage);
                      setLangMenuOpen(false);
                    }}
                    style={{
                      width: "100%",
                      padding: "0.65rem 1rem",
                      textAlign: "left",
                      background: language === opt.code ? "var(--primary-50, rgba(27, 85, 155, 0.1))" : "transparent",
                      color: language === opt.code ? "var(--primary)" : "var(--text)",
                      border: "none",
                      borderBottom: "1px solid var(--border)",
                      display: "flex",
                      alignItems: "center",
                      gap: "0.5rem",
                      cursor: "pointer",
                      fontSize: "0.875rem",
                      fontWeight: language === opt.code ? 700 : 500,
                    }}
                  >
                    <span>{opt.flag}</span>
                    <span>{opt.nativeName}</span>
                    {language === opt.code && <span style={{ marginLeft: "auto" }}>✓</span>}
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Theme Toggle */}
          <button
            onClick={toggleDarkMode}
            className="btn btn-ghost btn-sm"
            style={{ fontSize: "1.1rem", padding: "0.4rem" }}
            title={darkMode ? t("nav.lightMode", "Light Mode") : t("nav.darkMode", "Dark Mode")}
          >
            {darkMode ? "☀️" : "🌙"}
          </button>

          {/* Auth Action */}
          {isLoggedIn ? (
            <button onClick={handleLogout} className="btn btn-ghost btn-sm" style={{ color: "var(--error)" }}>
              {t("nav.logout", "Log Out")}
            </button>
          ) : (
            <div style={{ display: "flex", gap: "0.5rem" }}>
              <Link href="/auth/login" className="btn btn-ghost btn-sm">
                {t("nav.login", "Login")}
              </Link>
              <Link href="/auth/signup" className="btn btn-primary btn-sm">
                {t("nav.signup", "Sign Up")}
              </Link>
            </div>
          )}
        </div>
      </div>
    </nav>
  );
}
