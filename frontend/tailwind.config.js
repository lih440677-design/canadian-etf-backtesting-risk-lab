/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#18212f",
        graphite: "#4b5563",
        frost: "#f7f9fb",
        line: "#d8dee8",
        pine: "#0f766e",
        copper: "#b45309",
        wine: "#9f1239",
      },
      boxShadow: {
        panel: "0 16px 40px rgba(24, 33, 47, 0.08)",
      },
    },
  },
  plugins: [],
};

