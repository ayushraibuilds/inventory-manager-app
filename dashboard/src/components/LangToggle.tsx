"use client";

import { useState, useEffect } from "react";
import { Languages } from "lucide-react";
import { Lang, getStoredLang, setStoredLang } from "@/lib/i18n";

export default function LangToggle({ onChange }: { onChange?: (lang: Lang) => void }) {
    const [lang, setLang] = useState<Lang>("en");

    useEffect(() => {
        setLang(getStoredLang());
    }, []);

    const toggle = () => {
        const next: Lang = lang === "en" ? "hi" : "en";
        setLang(next);
        setStoredLang(next);
        onChange?.(next);
    };

    return (
        <button
            onClick={toggle}
            className="flex items-center gap-1.5 h-9 px-3 rounded-full bg-[var(--card-bg)] border border-[var(--border)] hover:bg-[var(--card-hover)] transition-all active:scale-90"
            title={lang === "en" ? "Switch to Hindi" : "Switch to English"}
        >
            <Languages className="w-4 h-4 text-[var(--text-muted)]" />
            <span className="text-xs font-bold text-[var(--text-primary)]">{lang === "en" ? "EN" : "हि"}</span>
        </button>
    );
}
