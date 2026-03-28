import 'package:flutter/foundation.dart';
import 'package:supabase_flutter/supabase_flutter.dart';

import '../config/app_config.dart';

enum SessionStatus { loading, authenticated, unauthenticated }

class SessionService extends ChangeNotifier {
  SessionService._internal();

  static final SessionService _instance = SessionService._internal();

  factory SessionService() => _instance;

  SessionStatus _status = SessionStatus.loading;
  String? _sellerId;

  SessionStatus get status => _status;
  String? get sellerId => _sellerId;
  bool get isAuthenticated => _status == SessionStatus.authenticated;

  /// Returns a valid access token for API calls from Supabase.
  Future<String?> getAccessToken() async {
    if (!AppConfig.hasSupabaseConfig) return null;
    return Supabase.instance.client.auth.currentSession?.accessToken;
  }

  Future<void> restoreSession() async {
    _status = SessionStatus.loading;
    notifyListeners();

    if (AppConfig.hasSupabaseConfig) {
      try {
        final session = Supabase.instance.client.auth.currentSession;
        if (session != null) {
          _sellerId = session.user.id;
          _status = SessionStatus.authenticated;
          notifyListeners();
          return;
        }
      } catch (_) {
        // Session expired or Supabase failed
      }
    }

    _status = SessionStatus.unauthenticated;
    notifyListeners();
  }

  /// Sign in with Supabase email/password.
  Future<void> signInWithEmail({
    required String email,
    required String password,
  }) async {
    if (!AppConfig.hasSupabaseConfig) {
      throw Exception('Supabase is not configured. Add SUPABASE_URL and SUPABASE_ANON_KEY via --dart-define.');
    }

    final response = await Supabase.instance.client.auth.signInWithPassword(
      email: email,
      password: password,
    );

    if (response.session == null) {
      throw Exception('Sign-in failed. Check your email and password.');
    }

    _sellerId = response.user?.id;
    _status = SessionStatus.authenticated;
    notifyListeners();
  }

  /// Sign up with Supabase email/password.
  Future<void> signUpWithEmail({
    required String email,
    required String password,
  }) async {
    if (!AppConfig.hasSupabaseConfig) {
      throw Exception('Supabase is not configured.');
    }

    final response = await Supabase.instance.client.auth.signUp(
      email: email,
      password: password,
    );

    if (response.session != null) {
      _sellerId = response.user?.id;
      _status = SessionStatus.authenticated;
      notifyListeners();
    } else {
      throw Exception('Account created. Please check your email to confirm, then sign in.');
    }
  }

  Future<void> signOut() async {
    if (AppConfig.hasSupabaseConfig) {
      try {
        await Supabase.instance.client.auth.signOut();
      } catch (_) {
        // Ignore Supabase sign-out errors
      }
    }

    _sellerId = null;
    _status = SessionStatus.unauthenticated;
    notifyListeners();
  }
}
