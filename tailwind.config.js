/** @type {import('tailwindcss').Config} */
export default {
  darkMode: ["class"],
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: {
          DEFAULT: "#116149",
          foreground: "#FFFFFF",
        },
        secondary: {
          DEFAULT: "#F7F6F0",
          foreground: "#1E2923",
        },
        accent: {
          DEFAULT: "#E69A2D",
          foreground: "#FFFFFF",
        },
        destructive: {
          DEFAULT: "#C93B32",
          foreground: "#FFFFFF",
        },
        muted: {
          DEFAULT: "#EDEBE2",
          foreground: "#5A655F",
        },
        card: {
          DEFAULT: "#FFFFFF",
          foreground: "#17211C",
        },
      },
      borderRadius: {
        lg: "0.75rem",
        md: "0.5rem",
        sm: "0.375rem",
      },
      boxShadow: {
        subtle: "0 1px 3px 0 rgba(17, 97, 73, 0.06), 0 1px 2px -1px rgba(17, 97, 73, 0.04)",
      },
    },
  },
  plugins: [],
};
