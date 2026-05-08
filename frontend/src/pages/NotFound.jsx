import React from "react";

export default function NotFound() {
  return (
    <div
      style={{
        minHeight: "100vh",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        gap: "12px",
        fontFamily: "Inter, sans-serif",
      }}
    >
      <h1 style={{ fontSize: "4rem", fontWeight: 800, color: "#3b82f6" }}>404</h1>
      <p style={{ color: "#94a3b8" }}>Page not found — C-IAW Agent</p>
      <a href="/" style={{ color: "#60a5fa", textDecoration: "none", fontSize: "0.875rem" }}>
        ← Back to Dashboard
      </a>
    </div>
  );
}
