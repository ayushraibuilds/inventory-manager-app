"use client";

import React, { createContext, useContext, useState, useEffect } from "react";
import { useRouter, usePathname } from "next/navigation";
import { supabase } from "@/lib/supabase";

interface AuthContextType {
    token: string | null;
    sellerId: string | null;
    login: (token: string, sellerId: string) => void;
    logout: () => void;
    isAuthenticated: boolean;
    isLoading: boolean;
    getAuthHeaders: () => Record<string, string>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
    const [token, setToken] = useState<string | null>(null);
    const [sellerId, setSellerId] = useState<string | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const router = useRouter();
    const pathname = usePathname();

    useEffect(() => {
        const initSession = async () => {
            const { data: { session } } = await supabase.auth.getSession();
            if (session) {
                setToken(session.access_token);
                setSellerId(session.user.id);
            }
            setIsLoading(false);
        };
        initSession();

        const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
            if (session) {
                setToken(session.access_token);
                setSellerId(session.user.id);
            } else {
                setToken(null);
                setSellerId(null);
            }
        });

        return () => subscription.unsubscribe();
    }, []);

    useEffect(() => {
        if (isLoading) return;

        const publicPaths = ["/", "/login", "/signup", "/privacy", "/terms"];
        if (!token && !publicPaths.includes(pathname)) {
            router.push("/login");
        } else if (token && (pathname === "/login" || pathname === "/signup")) {
            router.push("/dashboard");
        }
    }, [token, pathname, isLoading, router]);

    const login = (newToken: string, newSellerId: string) => {
        setToken(newToken);
        setSellerId(newSellerId);
        router.push("/dashboard");
    };

    const logout = async () => {
        await supabase.auth.signOut();
        setToken(null);
        setSellerId(null);
        router.push("/");
    };

    const getAuthHeaders = (): Record<string, string> => {
        const headers: Record<string, string> = {};
        if (token) headers["Authorization"] = `Bearer ${token}`;
        return headers;
    };

    return (
        <AuthContext.Provider value={{ token, sellerId, login, logout, isAuthenticated: !!token, isLoading, getAuthHeaders }}>
            {children}
        </AuthContext.Provider>
    );
}

export function useAuth() {
    const context = useContext(AuthContext);
    if (context === undefined) {
        throw new Error("useAuth must be used within an AuthProvider");
    }
    return context;
}
