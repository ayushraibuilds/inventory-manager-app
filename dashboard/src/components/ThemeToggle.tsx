"use client";

import { useEffect, useState } from "react";
import { Sun, Moon } from "lucide-react";

export default function ThemeToggle() {
    const [theme, setTheme] = useState<"dark" | "light">("dark");

    useEffect(() => {
        const saved = localStorage.getItem("ondc-theme") as "dark" | "light" | null;
        if (saved) {
            setTheme(saved);
            document.documentElement.setAttribute("data-theme", saved);
        }
    }, []);

    const toggle = () => {
        const next = theme === "dark" ? "light" : "dark";
        setTheme(next);
        localStorage.setItem("ondc-theme", next);
        document.documentElement.setAttribute("data-theme", next);
    };

    return (
        <button
            onClick={toggle}
            className="flex items-center justify-center w-9 h-9 rounded-full bg-[var(--card-bg)] border border-[var(--border)] hover:bg-[var(--card-hover)] transition-all active:scale-90"
            title={`Switch to ${theme === "dark" ? "light" : "dark"} mode`}
        >
            {theme === "dark" ? (
                <Sun className="w-4 h-4 text-yellow-400" />
            ) : (
                <Moon className="w-4 h-4 text-blue-400" />
            )}
        </button>
    );
}
