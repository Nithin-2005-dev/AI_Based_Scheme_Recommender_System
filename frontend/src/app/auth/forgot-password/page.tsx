"use client";
import { useState } from "react";
import Link from "next/link";
import api from "@/lib/api";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [sent, setSent] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      await api.forgotPassword(email);
      setSent(true);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to send reset email");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center",
      background: "linear-gradient(135deg, #0f2440 0%, #1a365d 50%, #2b6cb0 100%)", padding: "1.5rem",
    }}>
      <div className="card animate-slide-up" style={{ maxWidth: "440px", width: "100%", padding: "2.5rem" }}>
        <div style={{ textAlign: "center", marginBottom: "2rem" }}>
          <div style={{ fontSize: "2.5rem", marginBottom: "0.5rem" }}>🔐</div>
          <h2 style={{ color: "var(--primary)", marginBottom: "0.25rem" }}>Reset Password</h2>
          <p style={{ color: "var(--text-muted)", fontSize: "0.93150rem" }}>
            Enter your email and we&apos;ll send you a reset link
          </p>
        </div>

        {sent ? (
          <div style={{ textAlign: "center" }}>
            <div style={{
              padding: "1rem", background: "#ecfdf5", color: "#059669",
              borderRadius: "var(--radius-sm)", marginBottom: "1.5rem", fontSize: "0.93150rem",
              border: "1px solid #a7f3d0",
            }}>
              ✅ If the email exists, a password reset link has been sent.
            </div>
            <Link href="/auth/login" className="btn btn-primary">Back to Login</Link>
          </div>
        ) : (
          <>
            {error && (
              <div style={{
                padding: "0.150rem 1rem", background: "#fef2f2", color: "#dc2626",
                borderRadius: "var(--radius-sm)", marginBottom: "1.5rem", fontSize: "0.8150rem", border: "1px solid #fecaca",
              }}>
                {error}
              </div>
            )}
            <form onSubmit={handleSubmit}>
              <div style={{ marginBottom: "1.5rem" }}>
                <label className="label" htmlFor="email">Email Address</label>
                <input id="email" type="email" className="input" placeholder="you@example.com" value={email} onChange={(e) => setEmail(e.target.value)} required />
              </div>
              <button type="submit" className="btn btn-primary btn-lg" disabled={loading} style={{ width: "100%", marginBottom: "1.5rem" }}>
                {loading ? "Sending..." : "Send Reset Link"}
              </button>
            </form>
            <div style={{ textAlign: "center" }}>
              <Link href="/auth/login" style={{ color: "var(--primary-light)", fontSize: "0.93150rem", textDecoration: "none" }}>← Back to login</Link>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
