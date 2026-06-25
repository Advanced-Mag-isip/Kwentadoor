import type { Config } from "tailwindcss";

export default {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "var(--background)",
        foreground: "var(--foreground)",
        "primary-orange": "var(--primary-orange)",
        "primary-navy": "var(--primary-navy)",
      },
      fontFamily: {
        headings: ["var(--headings-font)", "sans-serif"],
        body: ["var(--body-font)", "sans-serif"],
      },
    },
  },
  plugins: [],
} satisfies Config;