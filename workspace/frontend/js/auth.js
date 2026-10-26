// ===============================
// AI-Empowered_Mental_Health_Awareness_Website_with_AI_Chatbot Authentication & Requests
// ===============================

const API_URL = "http://127.0.0.1:8000"; // backend URL
window.API_URL = API_URL; // make it global

window.MindAuth = {
  // Save login info
  setUser(user) {
    localStorage.setItem("user", JSON.stringify(user));
    localStorage.setItem("userLoggedIn", "true");
  },

  // Get current user
  getUser() {
    const user = localStorage.getItem("user");
    return user ? JSON.parse(user) : null;
  },

  // Check if user is logged in
  isLoggedIn() {
    return localStorage.getItem("userLoggedIn") === "true" && this.getUser();
  },

  // Logout
  clearUser() {
    localStorage.removeItem("user");
    localStorage.removeItem("userLoggedIn");
    window.location.href = "login.html";
  },

  // Backend call for login
  async loginRequest(email, password) {
    try {
      const res = await fetch(`${API_URL}/login`, {
        method: "POST",
        headers: {"Content-Type":"application/x-www-form-urlencoded"},
        body: new URLSearchParams({
          email: email,
          password: password
        })
      });

      const data = await res.json();
      if (res.ok) {
        this.setUser({ email, token: data.token });
      } else {
        // Handle different error response formats
        if (data && data.detail) {
          msg.textContent = data.detail;
        } else if (data && typeof data === 'object') {
          msg.textContent = "Invalid email or password";
        } else if (typeof data === 'string') {
          msg.textContent = data;
        } else {
          msg.textContent = "Login failed. Please check your credentials.";
        }
      }
      return { ok: res.ok, data };
    } catch (err) {
      console.error("Login error:", err);
      return { ok: false, data: { detail: "Server error" } };
    }
  },

  // Backend call for signup
  async signupRequest(email, password) {
    try {
      const res = await fetch(`${API_URL}/register`, {
        method: "POST",
        headers: {"Content-Type":"application/x-www-form-urlencoded"},
        body: new URLSearchParams({
          email: email,
          password: password
        })
      });

      const data = await res.json();
      if (res.ok) {
        this.setUser({ email, token: data.token });
      } else {
        // Handle different error response formats
        if (data && data.detail) {
          msg.textContent = data.detail;
        } else if (data && typeof data === 'object') {
          msg.textContent = "Registration failed. Please try again.";
        } else if (typeof data === 'string') {
          msg.textContent = data;
        } else {
          msg.textContent = "Registration failed. Please check your information.";
        }
      }
      return { ok: res.ok, data };
    } catch (err) {
      console.error("Signup error:", err);
      return { ok: false, data: { detail: "Server error" } };
    }
  },

  // Submit feedback
  async submitFeedback(name, country, message, rating) {
    const user = this.getUser();
    if (!user) return { ok: false, data: { detail: "Please login first" } };

    try {
      const formData = new FormData();
      formData.append("name", name);
      formData.append("country", country);
      formData.append("message", message);
      formData.append("rating", rating);

      const res = await fetch(`${API_URL}/feedback`, {
        method: "POST",
        headers: { "token": user.token },
        body: formData,
      });
      const data = await res.json();
      return { ok: res.ok, data };
    } catch (err) {
      console.error("Feedback error:", err);
      return { ok: false, data: { detail: "Server error" } };
    }
  },

  // Get feedbacks
  async getFeedbacks() {
    const user = this.getUser();
    if (!user) return [];

    try {
      const res = await fetch(`${API_URL}/feedback`, {
        headers: { "token": user.token },
      });
      const data = await res.json();
      return data;
    } catch (err) {
      console.error("Get feedback error:", err);
      return [];
    }
  },

  // Submit stress detection
  async submitStress(userInput) {
    const user = this.getUser();
    if (!user) return { ok: false, data: { detail: "Please login first" } };

    try {
      const res = await fetch(`${API_URL}/stress`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "token": user.token,
        },
        body: JSON.stringify(userInput),
      });
      const data = await res.json();
      return { ok: res.ok, data };
    } catch (err) {
      console.error("Stress detection error:", err);
      return { ok: false, data: { detail: "Server error" } };
    }
  },

  // Get stress history
  async getStressHistory(email) {
    const user = this.getUser();
    if (!user) return [];

    try {
      const res = await fetch(`${API_URL}/stress/history?user=${email}`, {
        headers: { "token": user.token },
      });
      const data = await res.json();
      return data;
    } catch (err) {
      console.error("Get stress history error:", err);
      return [];
    }
  },

  // ===============================
  // Mood tracker (AI module)
  // ===============================

  // Submit a journal entry - runs the emotion classifier and logs it
  async submitMoodEntry(text) {
    const user = this.getUser();
    if (!user) return { ok: false, data: { detail: "Please login first" } };

    try {
      const res = await fetch(`${API_URL}/api/mood/entry`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user: user.email, text }),
      });
      const data = await res.json();
      return { ok: res.ok, data };
    } catch (err) {
      console.error("Mood entry error:", err);
      return { ok: false, data: { detail: "Server error" } };
    }
  },

  // Get the user's full mood history (for the trend chart + entries list)
  async getMoodHistory() {
    const user = this.getUser();
    if (!user) return [];

    try {
      const res = await fetch(`${API_URL}/api/mood/history?user=${encodeURIComponent(user.email)}`);
      const data = await res.json();
      return Array.isArray(data) ? data : [];
    } catch (err) {
      console.error("Get mood history error:", err);
      return [];
    }
  },

  // Get a forecast of where the user's mood is trending (needs 7+ entries)
  async getMoodForecast() {
    const user = this.getUser();
    if (!user) return { error: "Please login first" };

    try {
      const res = await fetch(`${API_URL}/api/mood/forecast?user=${encodeURIComponent(user.email)}`);
      return await res.json();
    } catch (err) {
      console.error("Get mood forecast error:", err);
      return { error: "Server error" };
    }
  },

  // ===============================
  // Chatbot (AI module)
  // ===============================

  async sendChatMessage(message) {
    const user = this.getUser();
    if (!user) return { ok: false, data: { detail: "Please login first" } };

    try {
      const res = await fetch(`${API_URL}/api/chatbot/message`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user: user.email, message }),
      });
      const data = await res.json();
      return { ok: res.ok, data };
    } catch (err) {
      console.error("Chatbot error:", err);
      return { ok: false, data: { detail: "Server error" } };
    }
  },

  async resetChatSession() {
    const user = this.getUser();
    if (!user) return;
    try {
      await fetch(`${API_URL}/api/chatbot/reset`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user: user.email }),
      });
    } catch (err) {
      console.error("Chat reset error:", err);
    }
  },

  // ===============================
  // Recommendations (AI module)
  // ===============================

  async getRecommendations() {
    const user = this.getUser();
    if (!user) return { error: "Please login first" };

    try {
      const res = await fetch(`${API_URL}/api/recommendations?user=${encodeURIComponent(user.email)}`);
      return await res.json();
    } catch (err) {
      console.error("Get recommendations error:", err);
      return { error: "Server error" };
    }
  },

  async submitResourceFeedback(resourceId, rating) {
    const user = this.getUser();
    if (!user) return { ok: false, data: { detail: "Please login first" } };

    try {
      const res = await fetch(`${API_URL}/api/recommendations/feedback`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user: user.email, resource_id: resourceId, rating }),
      });
      const data = await res.json();
      return { ok: res.ok, data };
    } catch (err) {
      console.error("Resource feedback error:", err);
      return { ok: false, data: { detail: "Server error" } };
    }
  },

  // ===============================
  // Self-assessment quiz (AI module)
  // ===============================

  async getQuiz(quizId) {
    try {
      const res = await fetch(`${API_URL}/api/quiz/${quizId}`);
      return await res.json();
    } catch (err) {
      console.error("Get quiz error:", err);
      return { error: "Server error" };
    }
  },

  async submitQuiz(quizId, selectedOptionIds) {
    const user = this.getUser();
    if (!user) return { ok: false, data: { detail: "Please login first" } };

    try {
      const res = await fetch(`${API_URL}/api/quiz/submit`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user: user.email,
          quiz_id: quizId,
          selected_option_ids: selectedOptionIds,
        }),
      });
      const data = await res.json();
      return { ok: res.ok, data };
    } catch (err) {
      console.error("Quiz submit error:", err);
      return { ok: false, data: { detail: "Server error" } };
    }
  },
};

// ===============================
// Restrict Navbar Links if not logged in
// ===============================
document.addEventListener("DOMContentLoaded", () => {
  const user = window.MindAuth.getUser();
  const protectedLinks = document.querySelectorAll("a[href$='.html']");

  protectedLinks.forEach((link) => {
    link.addEventListener("click", (e) => {
      if (!window.MindAuth.getUser()) {
        e.preventDefault();
        alert("Please login first to access this section.");
        window.location.href = "login.html";
      }
    });
  });
});
