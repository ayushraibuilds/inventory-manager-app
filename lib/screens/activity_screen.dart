import 'package:flutter/material.dart';

import '../services/api_service.dart';

class ActivityScreen extends StatefulWidget {
  const ActivityScreen({super.key});

  @override
  State<ActivityScreen> createState() => _ActivityScreenState();
}

class _ActivityScreenState extends State<ActivityScreen> {
  late Future<List<Map<String, dynamic>>> _activityFuture;

  @override
  void initState() {
    super.initState();
    _activityFuture = ApiService().getActivity();
  }

  Future<void> _refresh() async {
    setState(() {
      _activityFuture = ApiService().getActivity();
    });
    await _activityFuture;
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Padding(
              padding: EdgeInsets.fromLTRB(20, 20, 20, 0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Activity',
                    style: TextStyle(
                      color: Colors.white,
                      fontSize: 28,
                      fontWeight: FontWeight.w800,
                    ),
                  ),
                  SizedBox(height: 8),
                  Text(
                    'Recent actions and changes across your catalog.',
                    style: TextStyle(
                      color: Color(0xFFCBD5E1),
                      fontSize: 15,
                      height: 1.4,
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 16),
            Expanded(
              child: FutureBuilder<List<Map<String, dynamic>>>(
                future: _activityFuture,
                builder: (context, snapshot) {
                  if (snapshot.connectionState == ConnectionState.waiting) {
                    return _buildLoading();
                  }
                  if (snapshot.hasError) {
                    return _buildError(snapshot.error);
                  }
                  final activities = snapshot.data ?? [];
                  if (activities.isEmpty) {
                    return _buildEmpty();
                  }
                  return RefreshIndicator(
                    color: const Color(0xFF2563EB),
                    onRefresh: _refresh,
                    child: ListView.separated(
                      padding: const EdgeInsets.fromLTRB(20, 0, 20, 32),
                      physics: const AlwaysScrollableScrollPhysics(),
                      itemCount: activities.length,
                      separatorBuilder: (_, index) => const SizedBox(height: 8),
                      itemBuilder: (context, index) {
                        return _ActivityCard(activity: activities[index]);
                      },
                    ),
                  );
                },
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildLoading() {
    return ListView(
      padding: const EdgeInsets.symmetric(horizontal: 20),
      children: List.generate(6, (_) => Padding(
        padding: const EdgeInsets.only(bottom: 8),
        child: Container(
          height: 72,
          decoration: BoxDecoration(
            color: const Color(0xFF111827),
            borderRadius: BorderRadius.circular(18),
          ),
        ),
      )),
    );
  }

  Widget _buildError(Object? error) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.error_outline, color: Color(0xFFF97316), size: 48),
            const SizedBox(height: 16),
            Text('$error',
              textAlign: TextAlign.center,
              style: const TextStyle(color: Color(0xFFCBD5E1), height: 1.4),
            ),
            const SizedBox(height: 18),
            ElevatedButton(onPressed: _refresh, child: const Text('Retry')),
          ],
        ),
      ),
    );
  }

  Widget _buildEmpty() {
    return const Center(
      child: Padding(
        padding: EdgeInsets.all(32),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.history, color: Color(0xFF64748B), size: 48),
            SizedBox(height: 20),
            Text('No recent activity',
              style: TextStyle(
                color: Colors.white, fontSize: 20, fontWeight: FontWeight.w700,
              ),
            ),
            SizedBox(height: 8),
            Text(
              'Actions like adding products, updating prices, or scanning barcodes will appear here.',
              textAlign: TextAlign.center,
              style: TextStyle(color: Color(0xFF94A3B8), height: 1.4),
            ),
          ],
        ),
      ),
    );
  }
}

class _ActivityCard extends StatelessWidget {
  const _ActivityCard({required this.activity});

  final Map<String, dynamic> activity;

  @override
  Widget build(BuildContext context) {
    final action = activity['action'] ?? activity['type'] ?? 'update';
    final description = activity['description'] ?? activity['message'] ?? '';
    final timestamp = activity['timestamp'] ?? activity['created_at'] ?? '';
    final productName = activity['product_name'] ??
        activity['item_name'] ??
        activity['name'] ??
        '';

    final _ActionStyle style = _actionStyle(action.toString().toLowerCase());

    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: const Color(0xFF111827),
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: const Color(0xFF1E293B)),
      ),
      child: Row(
        children: [
          Container(
            width: 42, height: 42,
            decoration: BoxDecoration(
              color: style.color.withAlpha(30),
              borderRadius: BorderRadius.circular(14),
            ),
            child: Icon(style.icon, color: style.color, size: 20),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                if (productName.isNotEmpty)
                  Text(productName,
                    style: const TextStyle(
                      color: Colors.white,
                      fontSize: 15,
                      fontWeight: FontWeight.w600,
                    ),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                if (description.isNotEmpty)
                  Text(description,
                    style: const TextStyle(
                      color: Color(0xFF94A3B8),
                      fontSize: 13,
                      height: 1.35,
                    ),
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                  ),
              ],
            ),
          ),
          if (timestamp.isNotEmpty)
            Padding(
              padding: const EdgeInsets.only(left: 8),
              child: Text(
                _formatTimestamp(timestamp),
                style: const TextStyle(
                  color: Color(0xFF64748B),
                  fontSize: 12,
                ),
              ),
            ),
        ],
      ),
    );
  }

  static String _formatTimestamp(String timestamp) {
    try {
      final dt = DateTime.parse(timestamp);
      final now = DateTime.now();
      final diff = now.difference(dt);
      if (diff.inMinutes < 1) return 'now';
      if (diff.inMinutes < 60) return '${diff.inMinutes}m';
      if (diff.inHours < 24) return '${diff.inHours}h';
      if (diff.inDays < 7) return '${diff.inDays}d';
      return '${dt.day}/${dt.month}';
    } catch (_) {
      return timestamp.length > 10 ? timestamp.substring(0, 10) : timestamp;
    }
  }

  static _ActionStyle _actionStyle(String action) {
    if (action.contains('add') || action.contains('create')) {
      return const _ActionStyle(Icons.add_circle_outline, Color(0xFF22C55E));
    }
    if (action.contains('delete') || action.contains('remove')) {
      return const _ActionStyle(Icons.remove_circle_outline, Color(0xFFEF4444));
    }
    if (action.contains('price') || action.contains('update')) {
      return const _ActionStyle(Icons.edit_outlined, Color(0xFF38BDF8));
    }
    if (action.contains('scan')) {
      return const _ActionStyle(Icons.qr_code_scanner, Color(0xFFA78BFA));
    }
    if (action.contains('import')) {
      return const _ActionStyle(Icons.upload_file_outlined, Color(0xFFF97316));
    }
    return const _ActionStyle(Icons.history, Color(0xFF94A3B8));
  }
}

class _ActionStyle {
  const _ActionStyle(this.icon, this.color);
  final IconData icon;
  final Color color;
}
