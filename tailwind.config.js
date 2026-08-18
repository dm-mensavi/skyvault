/** @type {import("tailwindcss").Config} */
module.exports = {
  darkMode: ["class", "[data-theme=\"dark\"]"],
  content: [
    "./templates/**/*.html",
    "./static/**/*.js",
    "./ai_features/**/*.py",
    "./vault/**/*.py"
  ],
  theme: {
    extend: {
      colors: {
        sky: {
          bg: {
            primary: "var(--bg-primary)",
            secondary: "var(--bg-secondary)",
            tertiary: "var(--bg-tertiary)",
          },
          sidebar: {
            bg: "var(--sidebar-bg)",
            hover: "var(--sidebar-hover)",
            active: "var(--sidebar-active)",
          },
          text: {
            primary: "var(--text-primary)",
            secondary: "var(--text-secondary)",
            muted: "var(--text-muted)",
          },
          accent: {
            DEFAULT: "var(--accent-color)",
            hover: "var(--accent-hover)",
            light: "var(--accent-light)",
          },
          danger: {
            DEFAULT: "var(--danger-color)",
            hover: "var(--danger-hover)",
          },
          card: {
            bg: "var(--card-bg)",
            border: "var(--card-border)",
          },
          modal: {
            bg: "var(--modal-bg)",
          }
        }
      },
      fontFamily: {
        sans: ["Outfit", "Poppins", "-apple-system", "BlinkMacSystemFont", "sans-serif"],
      }
    },
  },
  plugins: [
    require("@tailwindcss/forms")
  ],
}
