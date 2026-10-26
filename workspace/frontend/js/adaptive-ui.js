// ===============================
// AI-Empowered_Mental_Health_Awareness_Website_with_AI_Chatbot Adaptive UI
// Satisfies Objective 6: "an adaptive user interface that changes
// according to the user's mood."
//
// How it works: fetches the user's most recent logged emotion, then sets
// a small set of CSS custom properties on <body> (accent color + a warm/
// cool background tint). Any page that includes this script AND defines
// its colors using var(--adaptive-accent) / var(--adaptive-glow) instead
// of a hardcoded color will visually respond to the user's mood.
//
// Usage: include this script on any page AFTER auth.js, then call
//   window.AdaptiveUI.apply();
// on page load.
// ===============================

const MOOD_THEMES = {
  joy:      { accent: "#f59e0b", glow: "rgba(245, 158, 11, .25)", label: "feeling joyful" },
  love:     { accent: "#ec4899", glow: "rgba(236, 72, 153, .22)", label: "feeling love" },
  surprise: { accent: "#22d3ee", glow: "rgba(34, 211, 238, .22)", label: "feeling surprised" },
  sadness:  { accent: "#60a5fa", glow: "rgba(96, 165, 250, .18)", label: "feeling low" },
  fear:     { accent: "#a78bfa", glow: "rgba(167, 139, 250, .18)", label: "feeling anxious" },
  anger:    { accent: "#f87171", glow: "rgba(248, 113, 113, .2)",  label: "feeling frustrated" },
  default:  { accent: "#8b5cf6", glow: "rgba(139, 92, 246, .25)",  label: "" },
};

window.AdaptiveUI = {
  async apply() {
    if (!window.MindAuth || !window.MindAuth.isLoggedIn()) return;

    let latestEmotion = null;
    try {
      const history = await window.MindAuth.getMoodHistory();
      if (history.length > 0) {
        latestEmotion = history[history.length - 1].emotion;
      }
    } catch (err) {
      console.error("AdaptiveUI: could not fetch mood history", err);
      return;
    }

    const theme = MOOD_THEMES[latestEmotion] || MOOD_THEMES.default;
    document.documentElement.style.setProperty("--adaptive-accent", theme.accent);
    document.documentElement.style.setProperty("--adaptive-glow", theme.glow);

    // Optional: surface a small, non-intrusive banner if a spot for it
    // exists on the page (id="adaptiveBanner")
    const banner = document.getElementById("adaptiveBanner");
    if (banner && theme.label) {
      banner.textContent = `Your space is tuned to how you've been ${theme.label} lately.`;
      banner.style.display = "block";
    }
  },
};
