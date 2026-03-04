"use client";

import { useEffect, useState } from "react";
import { Sun, Moon, Monitor } from "lucide-react";

type ThemeMode = "dark" | "light" | "system";

export default function ThemeToggle() {
    const [mode, setMode] = useState<ThemeMode>("system");

    const applyTheme = (m: ThemeMode) => {
        let resolved: "dark" | "light";
        if (m === "system") {
            resolved = window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
        } else {
            resolved = m;
        }
        document.documentElement.setAttribute("data-theme", resolved);
    };

    useEffect(() => {
        const saved = localStorage.getItem("ondc-theme-mode") as ThemeMode | null;
        const initial = saved || "system";
        setMode(initial);
        applyTheme(initial);

        // Listen for system preference changes when in system mode
        const mq = window.matchMedia("(prefers-color-scheme: dark)");
        const handler = () => {
            if ((localStorage.getItem("ondc-theme-mode") || "system") === "system") {
                applyTheme("system");
            }
        };
        mq.addEventListener("change", handler);
        return () => mq.removeEventListener("change", handler);
    }, []);

    const cycle = () => {
        const order: ThemeMode[] = ["system", "dark", "light"];
        const next = order[(order.indexOf(mode) + 1) % order.length];
        setMode(next);
        localStorage.setItem("ondc-theme-mode", next);
        applyTheme(next);
    };

    const icon = () => {
        switch (mode) {
            case "dark": return <Moon className="w-4 h-4 text-blue-400" />;
            case "light": return <Sun className="w-4 h-4 text-yellow-400" />;
            case "system": return <Monitor className="w-4 h-4 text-[var(--text-muted)]" />;
        }
    };

    const label = () => {
        switch (mode) {
            case "dark": return "Dark";
            case "light": return "Light";
            case "system": return "Auto";
        }
    };

    return (
        <button
            onClick={cycle}
            className="flex items-center justify-center gap-1.5 h-9 px-3 rounded-full bg-[var(--card-bg)] border border-[var(--border)] hover:bg-[var(--card-hover)] transition-all active:scale-90"
            title={`Theme: ${label()} — click to cycle`}
        >
            {icon()}
            <span className="text-xs font-medium text-[var(--text-muted)] hidden sm:inline">{label()}</span>
        </button>
    );
}
