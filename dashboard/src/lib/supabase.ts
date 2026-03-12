import { createClient, SupabaseClient } from "@supabase/supabase-js";

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || "";
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || "";

// Lazy-initialize to avoid crashing during Vercel's build-time static generation
// where env vars may not be injected yet.
let _client: SupabaseClient | null = null;

export const supabase: SupabaseClient = new Proxy({} as SupabaseClient, {
    get(_target, prop) {
        if (!_client) {
            if (!supabaseUrl) {
                // During build-time SSR, return a no-op to prevent crashes
                return () => ({ data: null, error: { message: "Supabase not configured" } });
            }
            _client = createClient(supabaseUrl, supabaseAnonKey);
        }
        return (_client as any)[prop];
    },
});
