"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import api from "@/lib/api";
import { useLanguage } from "@/context/LanguageContext";

export default function SignupPage() {
  const router = useRouter();
  const { t } = useLanguage();
  const [formData, setFormData] = useState({
    full_name: "",
    email: "",
    password: "",
    confirmPassword: "",
  });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    if (formData.password !== formData.confirmPassword) {
      setError(t("auth.passwordMismatch", "Passwords do not match"));
      return;
    }

    if (formData.password.length < 8) {
      setError(t("auth.passwordMinLength", "Password must be at least 8 characters"));
      return;
    }

    setLoading(true);
    try {
      const data = (await api.signup({
        full_name: formData.full_name,
        email: formData.email,
        password: formData.password,
      })) as { access_token: string; refresh_token: string; user: Record<string, unknown> };

      api.setTokens(data.access_token, data.refresh_token);
      localStorage.setItem("user", JSON.stringify(data.user));
      router.push("/profile");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : t("auth.signupFailed", "Signup failed"));
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
              {t("auth.createAccount", "Create Account")}
            </h2>
          </Link>
          <p style={{ color: "var(--text-muted)", fontSize: "0.9375rem" }}>
            {t("auth.signupSubtitle", "Join 1000s of citizens discovering government schemes")}
          </p>
        </div>

        {error && (
          <div
            style={{
              padding: "0.75rem 1rem",
              background: "#fef2f2",
              color: "#dc2626",
              borderRadius: "var(--radius-sm)",
              marginBottom: "1.5rem",
              fontSize: "0.875rem",
              border: "1px solid #fecaca",
            }}
          >
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div style={{ marginBottom: "1.25rem" }}>
            <label className="label" htmlFor="full_name">
              {t("profile.fullName", "Full Name")}
            </label>
            <input
              id="full_name"
              name="full_name"
              type="text"
              className="input"
              placeholder="Your full name"
              value={formData.full_name}
              onChange={handleChange}
              required
            />
          </div>

          <div style={{ marginBottom: "1.25rem" }}>
            <label className="label" htmlFor="email">
              {t("auth.email", "Email Address")}
            </label>
            <input
              id="email"
              name="email"
              type="email"
              className="input"
              placeholder="you@example.com"
              value={formData.email}
              onChange={handleChange}
              required
            />
          </div>

          <div style={{ marginBottom: "1.25rem" }}>
            <label className="label" htmlFor="password">
              {t("auth.password", "Password")}
            </label>
            <input
              id="password"
              name="password"
              type="password"
              className="input"
              placeholder="Min 8 characters, uppercase, number, special"
              value={formData.password}
              onChange={handleChange}
              required
              minLength={8}
            />
          </div>

          <div style={{ marginBottom: "1.5rem" }}>
            <label className="label" htmlFor="confirmPassword">
              {t("auth.confirmPassword", "Confirm Password")}
            </label>
            <input
              id="confirmPassword"
              name="confirmPassword"
              type="password"
              className="input"
              placeholder="Re-enter password"
              value={formData.confirmPassword}
              onChange={handleChange}
              required
            />
          </div>

          <button
            type="submit"
            className="btn btn-primary btn-lg"
            disabled={loading}
            style={{ width: "100%", marginBottom: "1.5rem" }}
          >
            {loading ? t("common.loading", "Creating account...") : t("auth.createAccountBtn", "Create Account")}
          </button>
        </form>

        <div style={{ textAlign: "center" }}>
          <p style={{ color: "var(--text-muted)", fontSize: "0.9375rem" }}>
            {t("auth.alreadyHaveAccount", "Already have an account?")}{" "}
            <Link
              href="/auth/login"
              style={{ color: "var(--primary-light)", fontWeight: 600, textDecoration: "none" }}
            >
              {t("auth.signInLink", "Sign in")}
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
