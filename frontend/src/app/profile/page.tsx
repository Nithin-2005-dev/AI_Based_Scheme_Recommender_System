"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import api from "@/lib/api";

const STATES = [
  "Andhra Pradesh","Arunachal Pradesh","Assam","Bihar","Chhattisgarh","Goa","Gujarat",
  "Haryana","Himachal Pradesh","Jharkhand","Karnataka","Kerala","Madhya Pradesh",
  "Maharashtra","Manipur","Meghalaya","Mizoram","Nagaland","Odisha","Punjab",
  "Rajasthan","Sikkim","Tamil Nadu","Telangana","Tripura","Uttar Pradesh",
  "Uttarakhand","West Bengal","Delhi","Puducherry","Chandigarh","Jammu and Kashmir","Ladakh",
];

export default function ProfilePage() {
  const router = useRouter();
  const [profile, setProfile] = useState<Record<string, unknown>>({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState("");

  useEffect(() => {
    const token = localStorage.getItem("access_token");
    if (!token) { router.push("/auth/login"); return; }
    loadProfile();
  }, [router]);

  const loadProfile = async () => {
    try {
      const data = await api.getProfile() as Record<string, unknown>;
      setProfile(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (field: string, value: unknown) => {
    setProfile({ ...profile, [field]: value });
  };

  const handleSave = async () => {
    setSaving(true);
    setMessage("");
    try {
      const updateData = { ...profile };
      delete updateData.id;
      delete updateData.email;
      delete updateData.role;
      delete updateData.has_aadhaar;
      delete updateData.has_pan;
      delete updateData.profile_completed;
      delete updateData.profile_completion_percentage;
      delete updateData.is_email_verified;
      delete updateData.created_at;
      delete updateData.notification_preferences;
      delete updateData.preferred_languages;

      const updated = await api.updateProfile(updateData) as Record<string, unknown>;
      setProfile(updated);
      setMessage("Profile saved successfully! ✅");
      setTimeout(() => setMessage(""), 3000);
    } catch (err) {
      setMessage("Failed to save profile");
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div style={{ minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center" }}>
        <p>Loading profile...</p>
      </div>
    );
  }

  const completion = (profile.profile_completion_percentage as number) || 0;

  return (
    <div>
      <nav className="nav">
        <div className="nav-inner">
          <Link href="/" className="nav-logo"><span style={{ fontSize: "1.5rem" }}>🏛️</span><span>GovScheme AI</span></Link>
          <div className="nav-links">
            <Link href="/dashboard" className="nav-link">Dashboard</Link>
            <Link href="/schemes" className="nav-link">Schemes</Link>
            <Link href="/eligibility" className="nav-link">Eligibility</Link>
            <Link href="/chatbot" className="nav-link">AI Chat</Link>
            <Link href="/notifications" className="nav-link" style={{ position: "relative" }}>🔔</Link>
            <Link href="/profile" className="nav-link active">Profile</Link>
          </div>
        </div>
      </nav>

      <div className="container page" style={{ maxWidth: "900px" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "2rem" }}>
          <div>
            <h1>👤 Your Profile</h1>
            <p style={{ color: "var(--text-secondary)" }}>Complete your profile for better scheme recommendations</p>
          </div>
          <button onClick={handleSave} className="btn btn-primary" disabled={saving}>
            {saving ? "Saving..." : "💾 Save Profile"}
          </button>
        </div>

        {message && (
          <div className="card" style={{
            marginBottom: "1.5rem", padding: "0.75rem 1rem",
            background: message.includes("✅") ? "#ecfdf5" : "#fef2f2",
            color: message.includes("✅") ? "var(--success)" : "var(--error)",
            border: `1px solid ${message.includes("✅") ? "#a7f3d0" : "#fecaca"}`,
          }}>
            {message}
          </div>
        )}

        {/* Profile Completion */}
        <div className="card" style={{ marginBottom: "2rem" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.75rem" }}>
            <h4>Profile Completion</h4>
            <span style={{ fontWeight: 700, color: completion >= 70 ? "var(--success)" : "var(--warning)" }}>
              {completion}%
            </span>
          </div>
          <div className="progress-bar">
            <div className={`progress-bar-fill ${completion >= 70 ? "eligible" : "partial"}`}
              style={{ width: `${completion}%` }} />
          </div>
        </div>

        {/* Personal Information */}
        <div className="card" style={{ marginBottom: "1.5rem" }}>
          <h3 style={{ marginBottom: "1.25rem", display: "flex", alignItems: "center", gap: "0.5rem" }}>👤 Personal Information</h3>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem" }}>
            <div>
              <label className="label">Full Name</label>
              <input className="input" value={(profile.full_name as string) || ""} onChange={(e) => handleChange("full_name", e.target.value)} />
            </div>
            <div>
              <label className="label">Email (read-only)</label>
              <input className="input" value={(profile.email as string) || ""} disabled />
            </div>
            <div>
              <label className="label">Age</label>
              <input className="input" type="number" value={(profile.age as number) || ""} onChange={(e) => handleChange("age", parseInt(e.target.value) || null)} />
            </div>
            <div>
              <label className="label">Gender</label>
              <select className="select" value={(profile.gender as string) || ""} onChange={(e) => handleChange("gender", e.target.value)}>
                <option value="">Select</option>
                <option value="male">Male</option>
                <option value="female">Female</option>
                <option value="other">Other</option>
                <option value="prefer_not_to_say">Prefer not to say</option>
              </select>
            </div>
            <div>
              <label className="label">Mobile Number</label>
              <input className="input" value={(profile.mobile_number as string) || ""} onChange={(e) => handleChange("mobile_number", e.target.value)} placeholder="+91..." />
            </div>
            <div>
              <label className="label">Religion</label>
              <input className="input" value={(profile.religion as string) || ""} onChange={(e) => handleChange("religion", e.target.value)} placeholder="e.g., Hindu, Muslim, Christian" />
            </div>
          </div>
        </div>

        {/* Employment & Income */}
        <div className="card" style={{ marginBottom: "1.5rem" }}>
          <h3 style={{ marginBottom: "1.25rem" }}>💼 Employment & Income</h3>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem" }}>
            <div>
              <label className="label">Occupation</label>
              <input className="input" value={(profile.occupation as string) || ""} onChange={(e) => handleChange("occupation", e.target.value)} placeholder="e.g., Farmer, Teacher, Student" />
            </div>
            <div>
              <label className="label">Employment Status</label>
              <select className="select" value={(profile.employment_status as string) || ""} onChange={(e) => handleChange("employment_status", e.target.value)}>
                <option value="">Select</option>
                <option value="employed">Employed</option>
                <option value="unemployed">Unemployed</option>
                <option value="self_employed">Self Employed</option>
                <option value="retired">Retired</option>
                <option value="student">Student</option>
                <option value="homemaker">Homemaker</option>
              </select>
            </div>
            <div>
              <label className="label">Monthly Income (₹)</label>
              <input className="input" type="number" value={(profile.income as number) || ""} onChange={(e) => handleChange("income", parseFloat(e.target.value) || null)} />
            </div>
            <div>
              <label className="label">Annual Family Income (₹)</label>
              <input className="input" type="number" value={(profile.annual_family_income as number) || ""} onChange={(e) => handleChange("annual_family_income", parseFloat(e.target.value) || null)} />
            </div>
          </div>
        </div>

        {/* Education */}
        <div className="card" style={{ marginBottom: "1.5rem" }}>
          <h3 style={{ marginBottom: "1.25rem" }}>🎓 Education & Category</h3>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem" }}>
            <div>
              <label className="label">Education Level</label>
              <select className="select" value={(profile.education as string) || ""} onChange={(e) => handleChange("education", e.target.value)}>
                <option value="">Select</option>
                <option value="Below 10th">Below 10th</option>
                <option value="10th">10th</option>
                <option value="12th">12th</option>
                <option value="Graduate">Graduate</option>
                <option value="Post-Graduate">Post-Graduate</option>
                <option value="PhD">PhD</option>
                <option value="Diploma">Diploma</option>
                <option value="ITI">ITI</option>
              </select>
            </div>
            <div>
              <label className="label">Social Category</label>
              <select className="select" value={(profile.category as string) || ""} onChange={(e) => handleChange("category", e.target.value)}>
                <option value="">Select</option>
                <option value="General">General</option>
                <option value="OBC">OBC</option>
                <option value="SC">SC</option>
                <option value="ST">ST</option>
                <option value="EWS">EWS</option>
              </select>
            </div>
            <div>
              <label className="label">Caste</label>
              <input className="input" value={(profile.caste as string) || ""} onChange={(e) => handleChange("caste", e.target.value)} />
            </div>
            <div style={{ display: "flex", alignItems: "center", gap: "0.75rem", paddingTop: "1.5rem" }}>
              <label className="toggle">
                <input type="checkbox" checked={!!profile.minority_status} onChange={(e) => handleChange("minority_status", e.target.checked)} />
                <span className="toggle-slider" />
              </label>
              <span style={{ fontSize: "0.875rem" }}>Minority Status</span>
            </div>
          </div>
        </div>

        {/* Location */}
        <div className="card" style={{ marginBottom: "1.5rem" }}>
          <h3 style={{ marginBottom: "1.25rem" }}>📍 Location</h3>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem" }}>
            <div>
              <label className="label">State</label>
              <select className="select" value={(profile.state as string) || ""} onChange={(e) => handleChange("state", e.target.value)}>
                <option value="">Select State</option>
                {STATES.map((s) => <option key={s} value={s}>{s}</option>)}
              </select>
            </div>
            <div>
              <label className="label">District</label>
              <input className="input" value={(profile.district as string) || ""} onChange={(e) => handleChange("district", e.target.value)} />
            </div>
            <div>
              <label className="label">Pincode</label>
              <input className="input" value={(profile.pincode as string) || ""} onChange={(e) => handleChange("pincode", e.target.value)} maxLength={6} />
            </div>
          </div>
        </div>

        {/* Special Status */}
        <div className="card" style={{ marginBottom: "1.5rem" }}>
          <h3 style={{ marginBottom: "1.25rem" }}>⭐ Special Status</h3>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: "1rem" }}>
            {[
              { field: "is_farmer", label: "🌾 Farmer" },
              { field: "is_student", label: "🎓 Student" },
              { field: "is_disabled", label: "♿ Person with Disability" },
              { field: "is_widow", label: "👩 Widow" },
              { field: "is_senior_citizen", label: "👴 Senior Citizen (60+)" },
              { field: "is_pregnant_woman", label: "🤰 Pregnant Woman" },
              { field: "is_business_owner", label: "💼 Business Owner" },
            ].map(({ field, label }) => (
              <div key={field} style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
                <label className="toggle">
                  <input type="checkbox" checked={!!profile[field]} onChange={(e) => handleChange(field, e.target.checked)} />
                  <span className="toggle-slider" />
                </label>
                <span style={{ fontSize: "0.875rem" }}>{label}</span>
              </div>
            ))}
          </div>

          {!!profile.is_disabled && (
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem", marginTop: "1rem" }}>
              <div>
                <label className="label">Disability Type</label>
                <input className="input" value={(profile.disability_type as string) || ""} onChange={(e) => handleChange("disability_type", e.target.value)} />
              </div>
            </div>
          )}

          <div style={{ marginTop: "1rem" }}>
            <label className="label">Land Ownership</label>
            <select className="select" style={{ maxWidth: "300px" }} value={(profile.land_ownership as string) || ""} onChange={(e) => handleChange("land_ownership", e.target.value)}>
              <option value="">Select</option>
              <option value="No Land">No Land</option>
              <option value="< 2 Acres">Less than 2 Acres</option>
              <option value="2-5 Acres">2-5 Acres</option>
              <option value="> 5 Acres">More than 5 Acres</option>
            </select>
          </div>
        </div>

        {/* Save Button */}
        <div style={{ display: "flex", justifyContent: "flex-end", gap: "1rem", marginTop: "1rem" }}>
          <Link href="/dashboard" className="btn btn-outline">Cancel</Link>
          <button onClick={handleSave} className="btn btn-primary btn-lg" disabled={saving}>
            {saving ? "Saving..." : "💾 Save Profile"}
          </button>
        </div>
      </div>
    </div>
  );
}
