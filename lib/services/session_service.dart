import 'package:flutter/foundation.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:supabase_flutter/supabase_flutter.dart';

import '../config/app_config.dart';

enum SessionStatus { loading, authenticated, unauthenticated }

enum SessionAuthMode { supabase, jwt, apiKey, unknown }

class SessionService extends ChangeNotifier {
  SessionService._internal();

  static const String _tokenStorageKey = 'seller_jwt';
  static const String _apiKeyStorageKey = 'seller_api_key';
  static const String _sellerIdStorageKey = 'seller_id';
  static const List<String> _legacyTokenKeys = [
    'seller_jwt',
    'jwt',
    'jwt_token',
    'access_token',
    'token',
  ];

  static final SessionService _instance = SessionService._internal();
  static const FlutterSecureStorage _secureStorage = FlutterSecureStorage();

  factory SessionService() => _instance;

  SessionStatus _status = SessionStatus.loading;
  SessionAuthMode _authMode = SessionAuthMode.unknown;
  String? _sellerId;

  SessionStatus get status => _status;
  SessionAuthMode get authMode => _authMode;
  String? get sellerId => _sellerId;
  bool get isAuthenticated => _status == SessionStatus.authenticated;

  /// Returns a valid access token for API calls.
  /// Prefers Supabase session, falls back to stored JWT/API key.
  Future<String?> getAccessToken() async {
    if (_authMode == SessionAuthMode.supabase && AppConfig.hasSupabaseConfig) {
      final session = Supabase.instance.client.auth.currentSession;
      if (session != null) {
        return session.accessToken;
      }
    }
    return readToken();
  }

  Future<void> restoreSession() async {
    _status = SessionStatus.loading;
    notifyListeners();

    // Check Supabase session first
    if (AppConfig.hasSupabaseConfig) {
      try {
        final session = Supabase.instance.client.auth.currentSession;
        if (session != null) {
          _authMode = SessionAuthMode.supabase;
          _sellerId = session.user.id;
          _status = SessionStatus.authenticated;
          notifyListeners();
          return;
        }
      } catch (_) {
        // Supabase not initialized or session expired, fall through
      }
    }

    // Fall back to stored credentials
    final token = await readToken();
    final apiKey = await readApiKey();
    _sellerId = await readSellerId();

    if ((token != null && token.isNotEmpty) ||
        (apiKey != null && apiKey.isNotEmpty)) {
      _authMode = token != null && token.isNotEmpty
          ? SessionAuthMode.jwt
          : SessionAuthMode.apiKey;
      _status = SessionStatus.authenticated;
    } else {
      _authMode = SessionAuthMode.unknown;
      _status = SessionStatus.unauthenticated;
    }

    notifyListeners();
  }

  Future<String?> readToken() async {
    final secureToken = await _secureStorage.read(key: _tokenStorageKey);
    if (secureToken != null && secureToken.trim().isNotEmpty) {
      return secureToken.trim();
    }

    final preferences = await SharedPreferences.getInstance();
    for (final key in _legacyTokenKeys) {
      final legacyToken = preferences.getString(key);
      if (legacyToken == null || legacyToken.trim().isEmpty) {
        continue;
      }

      final token = legacyToken.trim();
      await saveToken(token);

      for (final legacyKey in _legacyTokenKeys) {
        await preferences.remove(legacyKey);
      }

      return token;
    }

    return null;
  }

  Future<String?> readApiKey() async {
    final apiKey = await _secureStorage.read(key: _apiKeyStorageKey);
    if (apiKey == null || apiKey.trim().isEmpty) {
      return null;
    }
    return apiKey.trim();
  }

  Future<String?> readSellerId() async {
    final sellerId = await _secureStorage.read(key: _sellerIdStorageKey);
    if (sellerId == null || sellerId.trim().isEmpty) {
      return null;
    }
    return sellerId.trim();
  }

  Future<void> saveToken(String token) async {
    await _secureStorage.write(key: _tokenStorageKey, value: token.trim());
  }

  Future<void> saveApiKey(String apiKey) async {
    await _secureStorage.write(key: _apiKeyStorageKey, value: apiKey.trim());
  }

  Future<void> saveSellerId(String? sellerId) async {
    final normalized = sellerId?.trim() ?? '';
    if (normalized.isEmpty) {
      await _secureStorage.delete(key: _sellerIdStorageKey);
      _sellerId = null;
    } else {
      await _secureStorage.write(key: _sellerIdStorageKey, value: normalized);
      _sellerId = normalized;
    }
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

    _authMode = SessionAuthMode.supabase;
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
      _authMode = SessionAuthMode.supabase;
      _sellerId = response.user?.id;
      _status = SessionStatus.authenticated;
      notifyListeners();
    } else {
      throw Exception('Account created. Please check your email to confirm, then sign in.');
    }
  }

  Future<void> signInWithJwt({required String token, String? sellerId}) async {
    await saveToken(token);
    await _secureStorage.delete(key: _apiKeyStorageKey);
    await saveSellerId(sellerId);
    _authMode = SessionAuthMode.jwt;
    _status = SessionStatus.authenticated;
    notifyListeners();
  }

  Future<void> signInWithApiKey({
    required String apiKey,
    String? sellerId,
  }) async {
    await saveApiKey(apiKey);
    await _secureStorage.delete(key: _tokenStorageKey);
    await saveSellerId(sellerId);
    _authMode = SessionAuthMode.apiKey;
    _status = SessionStatus.authenticated;
    notifyListeners();
  }

  Future<void> signOut() async {
    // Sign out from Supabase if active
    if (_authMode == SessionAuthMode.supabase && AppConfig.hasSupabaseConfig) {
      try {
        await Supabase.instance.client.auth.signOut();
      } catch (_) {
        // Ignore Supabase sign-out errors
      }
    }

    await _secureStorage.delete(key: _tokenStorageKey);
    await _secureStorage.delete(key: _apiKeyStorageKey);
    await _secureStorage.delete(key: _sellerIdStorageKey);

    final preferences = await SharedPreferences.getInstance();
    for (final key in _legacyTokenKeys) {
      await preferences.remove(key);
    }

    _sellerId = null;
    _authMode = SessionAuthMode.unknown;
    _status = SessionStatus.unauthenticated;
    notifyListeners();
  }
}
