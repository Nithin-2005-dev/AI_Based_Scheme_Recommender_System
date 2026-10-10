"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import api from "@/lib/api";
import { useLanguage } from "@/context/LanguageContext";

export default function LoginPage() {
  const router = useRouter();
  const { t } = useLanguage();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const data = (await api.login({ email, password })) as {
        access_token: string;
        refresh_token: string;
        user: { role: string; id: number; full_name: string };
      };
      api.setTokens(data.access_token, data.refresh_token);
      localStorage.setItem("user", JSON.stringify(data.user));

      if (data.user.role === "admin") {
        router.push("/admin");
      } else {
        router.push("/dashboard");
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : t("auth.invalidCredentials", "Login failed"));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      style={{
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        background: "linear-gradient(135deg, #0f2440 0%, #1a365d 50%, #2b6cb0 100%)",
        padding: "1.5rem",
      }}
    >
      <div className="card animate-slide-up" style={{ maxWidth: "440px", width: "100%", padding: "2.5rem" }}>
        <div style={{ textAlign: "center", marginBottom: "2rem" }}>
          <Link href="/" style={{ textDecoration: "none" }}>
            <div style={{ fontSize: "2.5rem", marginBottom: "0.5rem" }}>🏛️</div>
            <h2 style={{ color: "var(--primary)", marginBottom: "0.25rem" }}>
              {t("auth.welcomeBack", "Welcome Back")}
            </h2>
          </Link>
          <p style={{ color: "var(--text-muted)", fontSize: "0.93150rem" }}>
            {t("auth.loginSubtitle", "Sign in to discover government schemes for you")}
          </p>
        </div>

        {error && (
          <div
            style={{
              padding: "0.150rem 1rem",
              background: "#fef2f2",
              color: "#dc2626",
              borderRadius: "var(--radius-sm)",
              marginBottom: "1.5rem",
              fontSize: "0.8150rem",
              border: "1px solid #fecaca",
            }}
          >
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div style={{ marginBottom: "1.25rem" }}>
            <label className="label" htmlFor="email">
              {t("auth.email", "Email Address")}
            </label>
            <input
              id="email"
              type="email"
              className="input"
              placeholder="you@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              autoComplete="email"
            />
          </div>

          <div style={{ marginBottom: "1.25rem" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.3150rem" }}>
              <label className="label" htmlFor="password" style={{ marginBottom: 0 }}>
                {t("auth.password", "Password")}
              </label>
              <Link
                href="/auth/forgot-password"
                style={{
                  fontSize: "0.8125rem",
                  color: "var(--primary-light)",
                  textDecoration: "none",
                }}
              >
                {t("auth.forgotPassword", "Forgot password?")}
              </Link>
            </div>
            <input
              id="password"
              type="password"
              className="input"
              placeholder={t("auth.enterPassword", "Enter your password")}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              autoComplete="current-password"
            />
          </div>

          <button
            type="submit"
            className="btn btn-primary btn-lg"
            disabled={loading}
            style={{ width: "100%", marginBottom: "1.5rem" }}
          >
            {loading ? t("common.loading", "Signing in...") : t("auth.login", "Sign In")}
          </button>
        </form>

        <div style={{ textAlign: "center" }}>
          <p style={{ color: "var(--text-muted)", fontSize: "0.93150rem" }}>
            {t("auth.dontHaveAccount", "Don't have an account?")}{" "}
            <Link
              href="/auth/signup"
              style={{ color: "var(--primary-light)", fontWeight: 600, textDecoration: "none" }}
            >
              {t("auth.signupFree", "Sign up free")}
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
