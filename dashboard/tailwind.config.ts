import type { Config } from "tailwindcss";

const config: Config = {
    content: [
        "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
        "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
        "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
    ],
    theme: {
        extend: {
            colors: {
                background: "#0d1117",
                foreground: "#c9d1d9",
                primary: "#58a6ff",
                accent: "#f78166",
                surface: "rgba(22, 27, 34, 0.7)",
                border: "rgba(48, 54, 61, 0.5)",
                glassbg: "rgba(255, 255, 255, 0.03)",
                glassborder: "rgba(255, 255, 255, 0.08)",
                success: "#3fb950"
            },
            fontFamily: {
                sans: ['Inter', 'system-ui', 'sans-serif'],
            }
        },
    },
    plugins: [],
};
export default config;
