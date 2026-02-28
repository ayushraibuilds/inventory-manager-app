"use client";

import React, { createContext, useContext, useState, useEffect } from "react";
import { useRouter, usePathname } from "next/navigation";

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
        // On mount, check if user is logged in
        const storedToken = localStorage.getItem("token");
        const storedSellerId = localStorage.getItem("seller_id");

        if (storedToken && storedSellerId) {
            setToken(storedToken);
            setSellerId(storedSellerId);
        }

        setIsLoading(false);
    }, []);

    useEffect(() => {
        if (isLoading) return;

        // Protect routes
        const publicPaths = ["/", "/login", "/signup"];
        if (!token && !publicPaths.includes(pathname)) {
            router.push("/login");
        } else if (token && (pathname === "/login" || pathname === "/signup")) {
            router.push("/dashboard");
        }
    }, [token, pathname, isLoading, router]);

    const login = (newToken: string, newSellerId: string) => {
        localStorage.setItem("token", newToken);
        localStorage.setItem("seller_id", newSellerId);
        setToken(newToken);
        setSellerId(newSellerId);
        router.push("/dashboard");
    };

    const logout = () => {
        localStorage.removeItem("token");
        localStorage.removeItem("seller_id");
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
