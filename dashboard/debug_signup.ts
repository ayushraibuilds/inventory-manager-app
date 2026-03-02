import { createClient } from '@supabase/supabase-js';

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || '';
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || '';

const supabase = createClient(supabaseUrl, supabaseAnonKey);

async function testSignup() {
    console.log("Testing Supabase Signup...");
    const { data, error } = await supabase.auth.signUp({
        email: `test1234567@gmail.com`,
        password: "password1234",
    });

    if (error) {
        console.error("SUPABASE ERROR:", error.name, error.message, error.status);
    } else {
        console.log("SUPABASE SUCCESS:", data);
        if (data.session == null) {
            console.log("Email confirmation is required!");
        }
    }
}

testSignup();
