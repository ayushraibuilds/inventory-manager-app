import 'dart:ui';
import 'package:flutter/material.dart';

import '../models/dashboard_stats.dart';
import '../services/api_service.dart';
import '../widgets/premium_shimmer.dart';

typedef DashboardLoader = Future<Map<String, dynamic>> Function();

class DashboardScreen extends StatefulWidget {
  const DashboardScreen({super.key, this.loader});

  final DashboardLoader? loader;

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  late Future<DashboardStats> _statsFuture;

  @override
  void initState() {
    super.initState();
    _statsFuture = _loadStats();
  }

  Future<DashboardStats> _loadStats() async {
    final payload =
        await (widget.loader?.call() ?? ApiService().getDashboardStats());
    return DashboardStats.fromApi(payload);
  }

  Future<void> _refresh() async {
    setState(() {
      _statsFuture = _loadStats();
    });
    await _statsFuture;
  }

  @override
  Widget build(BuildContext context) {
    return FutureBuilder<DashboardStats>(
      future: _statsFuture,
      builder: (context, snapshot) {
        Widget content;

        if (snapshot.connectionState == ConnectionState.waiting) {
          content = const _DashboardLoading();
        } else if (snapshot.hasError) {
          content = _DashboardError(
            message: _buildErrorMessage(snapshot.error),
            onRetry: _refresh,
          );
        } else {
          content = _DashboardBody(stats: snapshot.data!);
        }

        return RefreshIndicator(
          color: const Color(0xFF2563EB),
          onRefresh: _refresh,
          child: ListView(
            physics: const AlwaysScrollableScrollPhysics(),
            padding: const EdgeInsets.fromLTRB(20, 20, 20, 32),
            children: [content],
          ),
        );
      },
    );
  }

  String _buildErrorMessage(Object? error) {
    if (error is FormatException) {
      return 'Dashboard data is incomplete. Check your API connection.';
    }
    return '$error';
  }
}

class _DashboardBody extends StatelessWidget {
  const _DashboardBody({required this.stats});

  final DashboardStats stats;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Container(
          padding: const EdgeInsets.all(24),
          decoration: BoxDecoration(
            gradient: const LinearGradient(
              colors: [Color(0xFF2563EB), Color(0xFF0EA5E9)],
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
            ),
            borderRadius: BorderRadius.circular(28),
            boxShadow: const [
              BoxShadow(
                color: Color(0x332563EB),
                blurRadius: 30,
                offset: Offset(0, 18),
              ),
            ],
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: const [
              Text(
                'Seller Pulse',
                style: TextStyle(
                  color: Colors.white70,
                  fontSize: 14,
                  fontWeight: FontWeight.w600,
                ),
              ),
              SizedBox(height: 12),
              Text(
                'Your inventory at a glance.',
                style: TextStyle(
                  color: Colors.white,
                  fontSize: 28,
                  fontWeight: FontWeight.w800,
                  height: 1.1,
                ),
              ),
              SizedBox(height: 12),
              Text(
                'Track catalog size, total value, and stock risk from one screen.',
                style: TextStyle(
                  color: Colors.white70,
                  fontSize: 15,
                  height: 1.4,
                ),
              ),
            ],
          ),
        ),
        const SizedBox(height: 24),
        const Text(
          'Overview',
          style: TextStyle(fontSize: 18, fontWeight: FontWeight.w700),
        ),
        const SizedBox(height: 16),
        _MetricCard(
          title: 'Total Products',
          value: stats.todaysOrders,
          icon: Icons.inventory_2_outlined,
          accent: const Color(0xFF38BDF8),
          subtitle: 'Total items in your catalog right now.',
        ),
        const SizedBox(height: 14),
        _MetricCard(
          title: 'Catalog Value',
          value: stats.pendingFulfillment,
          icon: Icons.currency_rupee_rounded,
          accent: const Color(0xFF22C55E),
          subtitle: 'Total value of inventory at selling prices.',
          prefix: '₹',
        ),
        const SizedBox(height: 14),
        _MetricCard(
          title: 'Low Stock Alerts',
          value: stats.lowStockAlerts,
          icon: Icons.warning_amber_rounded,
          accent: const Color(0xFFF97316),
          subtitle: 'Products with 5 or fewer units remaining.',
        ),
      ],
    );
  }
}

class _MetricCard extends StatelessWidget {
  const _MetricCard({
    required this.title,
    required this.value,
    required this.icon,
    required this.accent,
    required this.subtitle,
    this.prefix = '',
  });

  final String title;
  final int value;
  final IconData icon;
  final Color accent;
  final String subtitle;
  final String prefix;

  @override
  Widget build(BuildContext context) {
    return Hero(
      tag: 'metric_${title.replaceAll(' ', '_')}',
      child: Material(
        color: Colors.transparent,
        child: ClipRRect(
          borderRadius: BorderRadius.circular(24),
          child: BackdropFilter(
            filter: ImageFilter.blur(sigmaX: 16, sigmaY: 16),
            child: Container(
              padding: const EdgeInsets.all(20),
              decoration: BoxDecoration(
                color: const Color(0xFF111827).withAlpha(140),
                borderRadius: BorderRadius.circular(24),
                border: Border.all(color: Colors.white.withAlpha(20), width: 1.5),
              ),
              child: Row(
                children: [
                  Container(
                    width: 56,
                    height: 56,
                    decoration: BoxDecoration(
                      color: accent.withAlpha(38),
                      borderRadius: BorderRadius.circular(18),
                      border: Border.all(color: accent.withAlpha(100), width: 1.0),
                    ),
                    child: Icon(icon, color: accent),
                  ),
                  const SizedBox(width: 16),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          title,
                          style: const TextStyle(
                            color: Colors.white,
                            fontSize: 16,
                            fontWeight: FontWeight.w700,
                          ),
                        ),
                        const SizedBox(height: 6),
                        Text(
                          subtitle,
                          style: const TextStyle(
                            color: Color(0xFF94A3B8),
                            fontSize: 13,
                            height: 1.35,
                          ),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(width: 12),
                  Text(
                    '$prefix$value',
                    style: const TextStyle(
                      color: Colors.white,
                      fontSize: 28,
                      fontWeight: FontWeight.w800,
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}

class _DashboardLoading extends StatelessWidget {
  const _DashboardLoading();

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: const [
        _PlaceholderBlock(height: 180),
        SizedBox(height: 24),
        _PlaceholderBlock(height: 106),
        SizedBox(height: 14),
        _PlaceholderBlock(height: 106),
        SizedBox(height: 14),
        _PlaceholderBlock(height: 106),
      ],
    );
  }
}

class _PlaceholderBlock extends StatelessWidget {
  const _PlaceholderBlock({required this.height});

  final double height;

  @override
  Widget build(BuildContext context) {
    return PremiumShimmer(
      height: height,
      borderRadius: BorderRadius.circular(24),
    );
  }
}

class _DashboardError extends StatelessWidget {
  const _DashboardError({required this.message, required this.onRetry});

  final String message;
  final Future<void> Function() onRetry;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(
        color: const Color(0xFF111827),
        borderRadius: BorderRadius.circular(24),
        border: Border.all(color: const Color(0xFF7F1D1D)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'Dashboard unavailable',
            style: TextStyle(
              color: Colors.white,
              fontSize: 20,
              fontWeight: FontWeight.w700,
            ),
          ),
          const SizedBox(height: 10),
          Text(
            message,
            style: const TextStyle(color: Color(0xFFCBD5E1), height: 1.4),
          ),
          const SizedBox(height: 18),
          ElevatedButton(onPressed: onRetry, child: const Text('Retry')),
        ],
      ),
    );
  }
}
