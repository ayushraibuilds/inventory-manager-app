import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:supabase_flutter/supabase_flutter.dart';

import 'config/app_config.dart';
import 'screens/activity_screen.dart';
import 'screens/ai_chat_screen.dart';
import 'screens/dashboard_screen.dart';
import 'screens/products_screen.dart';
import 'screens/scanner_screen.dart';
import 'screens/sign_in_screen.dart';
import 'services/session_service.dart';

const Color _primaryBlue = Color(0xFF2563EB);
const Color _slateBackground = Color(0xFF0F172A);
const Color _slateSurface = Color(0xFF162033);

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();

  if (AppConfig.hasSupabaseConfig) {
    await Supabase.initialize(
      url: AppConfig.supabaseUrl,
      anonKey: AppConfig.supabaseAnonKey,
    );
  }

  await SessionService().restoreSession();
  runApp(const SellerApp());
}

class SellerApp extends StatelessWidget {
  const SellerApp({super.key, this.dashboardLoader});

  final DashboardLoader? dashboardLoader;

  @override
  Widget build(BuildContext context) {
    const colorScheme = ColorScheme.dark(
      primary: _primaryBlue,
      secondary: Color(0xFF38BDF8),
      surface: _slateSurface,
      onPrimary: Colors.white,
      onSecondary: Colors.white,
      onSurface: Colors.white,
      outline: Color(0xFF334155),
    );

    final baseTheme = ThemeData(
      useMaterial3: true,
      brightness: Brightness.dark,
      colorScheme: colorScheme,
      scaffoldBackgroundColor: _slateBackground,
      canvasColor: _slateSurface,
      snackBarTheme: SnackBarThemeData(
        behavior: SnackBarBehavior.floating,
        backgroundColor: const Color(0xFF1E293B),
        contentTextStyle: const TextStyle(color: Colors.white),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(18)),
      ),
      appBarTheme: const AppBarTheme(
        backgroundColor: Colors.transparent,
        elevation: 0,
        surfaceTintColor: Colors.transparent,
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: const Color(0xFF111827),
        hintStyle: const TextStyle(color: Color(0xFF64748B)),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(18),
          borderSide: BorderSide.none,
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(18),
          borderSide: BorderSide.none,
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(18),
          borderSide: const BorderSide(color: _primaryBlue, width: 1.2),
        ),
      ),
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: _primaryBlue,
          foregroundColor: Colors.white,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(18),
          ),
          padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
        ),
      ),
      textTheme: ThemeData.dark().textTheme.apply(
        bodyColor: Colors.white,
        displayColor: Colors.white,
      ),
    );

    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: 'ONDC Super Seller',
      theme: baseTheme,
      home: AnimatedBuilder(
        animation: SessionService(),
        builder: (context, _) {
          switch (SessionService().status) {
            case SessionStatus.loading:
              return const _BootScreen();
            case SessionStatus.unauthenticated:
              return const SignInScreen();
            case SessionStatus.authenticated:
              return MainWrapper(dashboardLoader: dashboardLoader);
          }
        },
      ),
      builder: kDebugMode
          ? (context, child) {
              return Banner(
                message:
                    AppConfig.apiBaseUrl.contains('your-production-url.com')
                    ? 'Configure API'
                    : 'API Ready',
                location: BannerLocation.topEnd,
                color: AppConfig.apiBaseUrl.contains('your-production-url.com')
                    ? const Color(0xFFF97316)
                    : const Color(0xFF16A34A),
                child: child ?? const SizedBox.shrink(),
              );
            }
          : null,
    );
  }
}

class MainWrapper extends StatefulWidget {
  const MainWrapper({super.key, this.dashboardLoader});

  final DashboardLoader? dashboardLoader;

  @override
  State<MainWrapper> createState() => _MainWrapperState();
}

class _MainWrapperState extends State<MainWrapper> {
  int _currentIndex = 0;
  final Set<int> _visitedTabs = {0};

  late final List<WidgetBuilder> _screenBuilders = <WidgetBuilder>[
    (_) => DashboardScreen(loader: widget.dashboardLoader),
    (_) => const ProductsScreen(),
    (_) => const ScannerScreen(),
    (_) => const AiChatScreen(),
    (_) => const ActivityScreen(),
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Stack(
        children: [
          IndexedStack(
            index: _currentIndex,
            children: List.generate(_screenBuilders.length, (index) {
              if (!_visitedTabs.contains(index)) {
                return const SizedBox.shrink();
              }
              return _screenBuilders[index](context);
            }),
          ),
          Positioned(
            top: 18,
            right: 20,
            child: SafeArea(
              child: _SessionMenuButton(currentIndex: _currentIndex),
            ),
          ),
        ],
      ),
      bottomNavigationBar: DecoratedBox(
        decoration: const BoxDecoration(
          color: Color(0xFF111827),
          border: Border(top: BorderSide(color: Color(0xFF1E293B))),
        ),
        child: BottomNavigationBar(
          currentIndex: _currentIndex,
          onTap: (index) => setState(() {
            _currentIndex = index;
            _visitedTabs.add(index);
          }),
          backgroundColor: Colors.transparent,
          elevation: 0,
          selectedItemColor: _primaryBlue,
          unselectedItemColor: const Color(0xFF64748B),
          type: BottomNavigationBarType.fixed,
          items: const [
            BottomNavigationBarItem(
              icon: Icon(Icons.query_stats_rounded),
              label: 'Pulse',
            ),
            BottomNavigationBarItem(
              icon: Icon(Icons.inventory_2_rounded),
              label: 'Products',
            ),
            BottomNavigationBarItem(
              icon: Icon(Icons.qr_code_scanner_rounded),
              label: 'Scanner',
            ),
            BottomNavigationBarItem(
              icon: Icon(Icons.auto_awesome_rounded),
              label: 'AI Chat',
            ),
            BottomNavigationBarItem(
              icon: Icon(Icons.history_rounded),
              label: 'Activity',
            ),
          ],
        ),
      ),
    );
  }
}

class _BootScreen extends StatelessWidget {
  const _BootScreen();

  @override
  Widget build(BuildContext context) {
    return const Scaffold(
      body: Center(child: CircularProgressIndicator(color: Color(0xFF2563EB))),
    );
  }
}

class _SessionMenuButton extends StatelessWidget {
  const _SessionMenuButton({required this.currentIndex});

  final int currentIndex;

  @override
  Widget build(BuildContext context) {
    final sessionService = SessionService();
    return Material(
      color: const Color(0xCC111827),
      borderRadius: BorderRadius.circular(18),
      child: PopupMenuButton<String>(
        tooltip: 'Session',
        color: const Color(0xFF111827),
        onSelected: (value) async {
          if (value == 'sign_out') {
            await sessionService.signOut();
          }
        },
        itemBuilder: (context) {
          return [
            PopupMenuItem<String>(
              enabled: false,
              value: 'mode',
              child: Text(
                sessionService.authMode == SessionAuthMode.jwt
                    ? 'JWT session'
                    : sessionService.authMode == SessionAuthMode.supabase
                        ? 'Supabase session'
                        : 'API key session',
              ),
            ),
            if ((sessionService.sellerId ?? '').isNotEmpty)
              PopupMenuItem<String>(
                enabled: false,
                value: 'seller',
                child: Text('Seller: ${sessionService.sellerId}'),
              ),
            const PopupMenuDivider(),
            const PopupMenuItem<String>(
              value: 'sign_out',
              child: Text('Sign out'),
            ),
          ];
        },
        child: Container(
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(18),
            border: Border.all(color: const Color(0xFF1E293B)),
          ),
          child: Icon(
            currentIndex == 2
                ? Icons.more_horiz_rounded
                : Icons.account_circle_outlined,
            color: Colors.white,
          ),
        ),
      ),
    );
  }
}
