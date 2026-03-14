import 'package:flutter/material.dart';

import '../services/api_service.dart';

typedef DashboardLoader = Future<Map<String, dynamic>> Function();

class DashboardScreen extends StatefulWidget {
  const DashboardScreen({super.key, this.loader});

  final DashboardLoader? loader;

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  late Future<Map<String, dynamic>> _statsFuture;

  @override
  void initState() {
    super.initState();
    _statsFuture = _loadStats();
  }

  Future<Map<String, dynamic>> _loadStats() {
    return widget.loader?.call() ?? ApiService().getDashboardStats();
  }

  Future<void> _refresh() async {
    setState(() {
      _statsFuture = _loadStats();
    });

    await _statsFuture;
  }

  @override
  Widget build(BuildContext context) {
    return FutureBuilder<Map<String, dynamic>>(
      future: _statsFuture,
      builder: (context, snapshot) {
        Widget content;

        if (snapshot.connectionState == ConnectionState.waiting) {
          content = const _DashboardLoading();
        } else if (snapshot.hasError) {
          content = _DashboardError(
            message: '${snapshot.error}',
            onRetry: _refresh,
          );
        } else {
          final payload = _normalizePayload(snapshot.data ?? const {});
          content = _DashboardBody(payload: payload);
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

  Map<String, dynamic> _normalizePayload(Map<String, dynamic> source) {
    final nested = source['stats'];
    if (nested is Map) {
      return Map<String, dynamic>.from(nested);
    }

    return source;
  }
}

class _DashboardBody extends StatelessWidget {
  const _DashboardBody({required this.payload});

  final Map<String, dynamic> payload;

  @override
  Widget build(BuildContext context) {
    final ordersToday = _readInt(payload, [
      'todays_orders',
      'today_orders',
      'todayOrders',
      'orders_today',
    ]);
    final pendingFulfillment = _readInt(payload, [
      'pending_fulfillment',
      'pending_orders',
      'pendingFulfillment',
      'pendingOrders',
    ]);
    final lowStockAlerts = _readInt(payload, [
      'low_stock_alerts',
      'low_stock',
      'lowStockAlerts',
      'lowStock',
    ]);

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
                'Your ONDC floor is live and synced.',
                style: TextStyle(
                  color: Colors.white,
                  fontSize: 28,
                  fontWeight: FontWeight.w800,
                  height: 1.1,
                ),
              ),
              SizedBox(height: 12),
              Text(
                'Track orders, fulfillment pressure, and stock risk from one command surface.',
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
          'Today',
          style: TextStyle(fontSize: 18, fontWeight: FontWeight.w700),
        ),
        const SizedBox(height: 16),
        _MetricCard(
          title: "Today's Orders",
          value: ordersToday,
          icon: Icons.shopping_bag_outlined,
          accent: const Color(0xFF38BDF8),
          subtitle: 'Orders created across your live catalog today.',
        ),
        const SizedBox(height: 14),
        _MetricCard(
          title: 'Pending Fulfillment',
          value: pendingFulfillment,
          icon: Icons.local_shipping_outlined,
          accent: const Color(0xFF22C55E),
          subtitle: 'Orders still waiting to be packed or dispatched.',
        ),
        const SizedBox(height: 14),
        _MetricCard(
          title: 'Low Stock Alerts',
          value: lowStockAlerts,
          icon: Icons.warning_amber_rounded,
          accent: const Color(0xFFF97316),
          subtitle: 'SKUs close to sellout and needing replenishment.',
        ),
      ],
    );
  }

  int _readInt(Map<String, dynamic> data, List<String> keys) {
    for (final key in keys) {
      final value = data[key];
      if (value is int) {
        return value;
      }
      if (value is num) {
        return value.toInt();
      }
      if (value is String) {
        return int.tryParse(value) ?? 0;
      }
    }

    return 0;
  }
}

class _MetricCard extends StatelessWidget {
  const _MetricCard({
    required this.title,
    required this.value,
    required this.icon,
    required this.accent,
    required this.subtitle,
  });

  final String title;
  final int value;
  final IconData icon;
  final Color accent;
  final String subtitle;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: const Color(0xFF111827),
        borderRadius: BorderRadius.circular(24),
        border: Border.all(color: const Color(0xFF1E293B)),
      ),
      child: Row(
        children: [
          Container(
            width: 56,
            height: 56,
            decoration: BoxDecoration(
              color: accent.withAlpha(38),
              borderRadius: BorderRadius.circular(18),
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
            '$value',
            style: const TextStyle(
              color: Colors.white,
              fontSize: 30,
              fontWeight: FontWeight.w800,
            ),
          ),
        ],
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
    return Container(
      height: height,
      decoration: BoxDecoration(
        color: const Color(0xFF111827),
        borderRadius: BorderRadius.circular(24),
      ),
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
