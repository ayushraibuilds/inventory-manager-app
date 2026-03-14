import 'package:flutter/material.dart';

import '../config/app_config.dart';
import '../services/api_service.dart';
import '../services/session_service.dart';

class SignInScreen extends StatefulWidget {
  const SignInScreen({super.key});

  @override
  State<SignInScreen> createState() => _SignInScreenState();
}

enum _SignInMode { email, jwt, apiKey }

class _SignInScreenState extends State<SignInScreen> {
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();
  final _credentialController = TextEditingController();
  final _sellerIdController = TextEditingController();

  _SignInMode _mode = AppConfig.hasSupabaseConfig
      ? _SignInMode.email
      : _SignInMode.jwt;
  bool _isSubmitting = false;
  bool _isSignUp = false;
  String? _errorMessage;

  @override
  void dispose() {
    _emailController.dispose();
    _passwordController.dispose();
    _credentialController.dispose();
    _sellerIdController.dispose();
    super.dispose();
  }

  Future<void> _submitEmail() async {
    final email = _emailController.text.trim();
    final password = _passwordController.text.trim();

    if (email.isEmpty || password.isEmpty) {
      setState(() => _errorMessage = 'Email and password are required.');
      return;
    }

    if (password.length < 6) {
      setState(() => _errorMessage = 'Password must be at least 6 characters.');
      return;
    }

    setState(() {
      _isSubmitting = true;
      _errorMessage = null;
    });

    try {
      if (_isSignUp) {
        await SessionService().signUpWithEmail(email: email, password: password);
      } else {
        await SessionService().signInWithEmail(email: email, password: password);
      }
    } catch (error) {
      setState(() => _errorMessage = '$error');
    } finally {
      if (mounted) setState(() => _isSubmitting = false);
    }
  }

  Future<void> _submitLegacy() async {
    final credential = _credentialController.text.trim();
    final sellerId = _sellerIdController.text.trim();

    if (credential.isEmpty) {
      setState(() {
        _errorMessage = _mode == _SignInMode.jwt
            ? 'JWT is required.'
            : 'API key is required.';
      });
      return;
    }

    setState(() {
      _isSubmitting = true;
      _errorMessage = null;
    });

    try {
      final sellers = await ApiService().verifySession(
        jwt: _mode == _SignInMode.jwt ? credential : null,
        apiKey: _mode == _SignInMode.apiKey ? credential : null,
      );

      final resolvedSellerId = sellerId.isNotEmpty
          ? sellerId
          : sellers.length == 1
              ? sellers.first
              : null;

      if (_mode == _SignInMode.jwt) {
        await SessionService().signInWithJwt(
          token: credential,
          sellerId: resolvedSellerId,
        );
      } else {
        await SessionService().signInWithApiKey(
          apiKey: credential,
          sellerId: resolvedSellerId,
        );
      }
    } catch (error) {
      setState(() => _errorMessage = '$error');
    } finally {
      if (mounted) setState(() => _isSubmitting = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: DecoratedBox(
        decoration: const BoxDecoration(
          gradient: LinearGradient(
            colors: [Color(0xFF020617), Color(0xFF0F172A), Color(0xFF111827)],
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
          ),
        ),
        child: SafeArea(
          child: Center(
            child: SingleChildScrollView(
              padding: const EdgeInsets.all(24),
              child: ConstrainedBox(
                constraints: const BoxConstraints(maxWidth: 460),
                child: Container(
                  padding: const EdgeInsets.all(28),
                  decoration: BoxDecoration(
                    color: const Color(0xE6111827),
                    borderRadius: BorderRadius.circular(30),
                    border: Border.all(color: const Color(0xFF1E293B)),
                    boxShadow: const [
                      BoxShadow(
                        color: Color(0x332563EB),
                        blurRadius: 36,
                        offset: Offset(0, 20),
                      ),
                    ],
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Container(
                        width: 60,
                        height: 60,
                        decoration: BoxDecoration(
                          borderRadius: BorderRadius.circular(20),
                          gradient: const LinearGradient(
                            colors: [Color(0xFF2563EB), Color(0xFF38BDF8)],
                          ),
                        ),
                        child: const Icon(
                          Icons.storefront_rounded,
                          color: Colors.white,
                          size: 30,
                        ),
                      ),
                      const SizedBox(height: 24),
                      Text(
                        _isSignUp ? 'Create Account' : 'Seller Access',
                        style: const TextStyle(
                          color: Colors.white,
                          fontSize: 32,
                          fontWeight: FontWeight.w800,
                        ),
                      ),
                      const SizedBox(height: 12),
                      Text(
                        _mode == _SignInMode.email
                            ? _isSignUp
                                ? 'Create a seller account to manage your ONDC inventory.'
                                : 'Sign in with your email and password to access your dashboard.'
                            : 'Connect this device using a seller JWT or a server API key.',
                        style: const TextStyle(
                          color: Color(0xFFCBD5E1),
                          fontSize: 15,
                          height: 1.45,
                        ),
                      ),
                      const SizedBox(height: 24),

                      // Mode selector
                      if (AppConfig.hasSupabaseConfig)
                        Padding(
                          padding: const EdgeInsets.only(bottom: 20),
                          child: Row(
                            children: [
                              _ModeChip(
                                label: 'Email',
                                icon: Icons.email_outlined,
                                selected: _mode == _SignInMode.email,
                                onTap: () => setState(() {
                                  _mode = _SignInMode.email;
                                  _errorMessage = null;
                                }),
                              ),
                              const SizedBox(width: 8),
                              _ModeChip(
                                label: 'JWT',
                                icon: Icons.verified_user_outlined,
                                selected: _mode == _SignInMode.jwt,
                                onTap: () => setState(() {
                                  _mode = _SignInMode.jwt;
                                  _isSignUp = false;
                                  _errorMessage = null;
                                }),
                              ),
                              const SizedBox(width: 8),
                              _ModeChip(
                                label: 'API Key',
                                icon: Icons.vpn_key_outlined,
                                selected: _mode == _SignInMode.apiKey,
                                onTap: () => setState(() {
                                  _mode = _SignInMode.apiKey;
                                  _isSignUp = false;
                                  _errorMessage = null;
                                }),
                              ),
                            ],
                          ),
                        ),

                      // Email/password fields
                      if (_mode == _SignInMode.email) ...[
                        TextField(
                          controller: _emailController,
                          keyboardType: TextInputType.emailAddress,
                          textInputAction: TextInputAction.next,
                          decoration: const InputDecoration(
                            labelText: 'Email',
                            hintText: 'you@example.com',
                            prefixIcon: Icon(Icons.email_outlined, size: 20),
                          ),
                        ),
                        const SizedBox(height: 14),
                        TextField(
                          controller: _passwordController,
                          obscureText: true,
                          textInputAction: TextInputAction.done,
                          onSubmitted: (_) => _submitEmail(),
                          decoration: const InputDecoration(
                            labelText: 'Password',
                            hintText: '••••••••',
                            prefixIcon: Icon(Icons.lock_outlined, size: 20),
                          ),
                        ),
                      ],

                      // JWT/API Key fields
                      if (_mode == _SignInMode.jwt || _mode == _SignInMode.apiKey) ...[
                        TextField(
                          controller: _credentialController,
                          obscureText: _mode == _SignInMode.jwt,
                          maxLines: _mode == _SignInMode.jwt ? 3 : 1,
                          decoration: InputDecoration(
                            labelText: _mode == _SignInMode.jwt
                                ? 'Seller JWT'
                                : 'Server API Key',
                            hintText: _mode == _SignInMode.jwt
                                ? 'Paste the Supabase/ONDC seller token'
                                : 'Paste the backend API key',
                          ),
                        ),
                        const SizedBox(height: 14),
                        TextField(
                          controller: _sellerIdController,
                          decoration: const InputDecoration(
                            labelText: 'Seller ID',
                            hintText: 'Optional if backend returns a single seller',
                          ),
                        ),
                      ],

                      if (_errorMessage != null) ...[
                        const SizedBox(height: 16),
                        Container(
                          padding: const EdgeInsets.all(14),
                          decoration: BoxDecoration(
                            color: const Color(0xFF7F1D1D).withAlpha(60),
                            borderRadius: BorderRadius.circular(14),
                            border: Border.all(color: const Color(0xFF7F1D1D)),
                          ),
                          child: Row(
                            children: [
                              const Icon(Icons.error_outline,
                                  color: Color(0xFFFCA5A5), size: 18),
                              const SizedBox(width: 10),
                              Expanded(
                                child: Text(
                                  _errorMessage!,
                                  style: const TextStyle(
                                    color: Color(0xFFFCA5A5),
                                    fontWeight: FontWeight.w500,
                                    fontSize: 13,
                                    height: 1.4,
                                  ),
                                ),
                              ),
                            ],
                          ),
                        ),
                      ],
                      const SizedBox(height: 22),
                      SizedBox(
                        width: double.infinity,
                        child: ElevatedButton(
                          onPressed: _isSubmitting
                              ? null
                              : _mode == _SignInMode.email
                                  ? _submitEmail
                                  : _submitLegacy,
                          child: _isSubmitting
                              ? const SizedBox(
                                  width: 22,
                                  height: 22,
                                  child: CircularProgressIndicator(
                                    strokeWidth: 2.2,
                                    color: Colors.white,
                                  ),
                                )
                              : Text(
                                  _mode == _SignInMode.email
                                      ? (_isSignUp
                                          ? 'Create Account'
                                          : 'Sign In')
                                      : 'Verify and Continue',
                                ),
                        ),
                      ),
                      if (_mode == _SignInMode.email) ...[
                        const SizedBox(height: 14),
                        Center(
                          child: TextButton(
                            onPressed: () => setState(() {
                              _isSignUp = !_isSignUp;
                              _errorMessage = null;
                            }),
                            child: Text(
                              _isSignUp
                                  ? 'Already have an account? Sign in'
                                  : "Don't have an account? Sign up",
                              style: const TextStyle(
                                color: Color(0xFF60A5FA),
                                fontSize: 14,
                              ),
                            ),
                          ),
                        ),
                      ],
                    ],
                  ),
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}

class _ModeChip extends StatelessWidget {
  const _ModeChip({
    required this.label,
    required this.icon,
    required this.selected,
    required this.onTap,
  });

  final String label;
  final IconData icon;
  final bool selected;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return Expanded(
      child: Material(
        color: selected ? const Color(0xFF2563EB) : const Color(0xFF0F172A),
        borderRadius: BorderRadius.circular(14),
        child: InkWell(
          onTap: onTap,
          borderRadius: BorderRadius.circular(14),
          child: Container(
            padding: const EdgeInsets.symmetric(vertical: 12),
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(14),
              border: Border.all(
                color: selected
                    ? const Color(0xFF60A5FA)
                    : const Color(0xFF1E293B),
              ),
            ),
            child: Column(
              children: [
                Icon(icon, size: 18,
                    color: selected ? Colors.white : const Color(0xFF64748B)),
                const SizedBox(height: 4),
                Text(
                  label,
                  style: TextStyle(
                    fontSize: 12,
                    fontWeight: FontWeight.w600,
                    color: selected ? Colors.white : const Color(0xFF64748B),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
