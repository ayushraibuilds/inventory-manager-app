class DashboardStats {
  const DashboardStats({
    required this.todaysOrders,
    required this.pendingFulfillment,
    required this.lowStockAlerts,
  });

  final int todaysOrders;
  final int pendingFulfillment;
  final int lowStockAlerts;

  factory DashboardStats.fromApi(Map<String, dynamic> payload) {
    final source = payload['stats'];
    final data = source is Map
        ? Map<String, dynamic>.from(source)
        : Map<String, dynamic>.from(payload);

    return DashboardStats(
      todaysOrders: _readRequiredInt(data, [
        'todays_orders',
        'today_orders',
        'todayOrders',
        'orders_today',
      ]),
      pendingFulfillment: _readRequiredInt(data, [
        'pending_fulfillment',
        'pending_orders',
        'pendingFulfillment',
        'pendingOrders',
      ]),
      lowStockAlerts: _readRequiredInt(data, [
        'low_stock_alerts',
        'low_stock',
        'lowStockAlerts',
        'lowStock',
      ]),
    );
  }

  static int _readRequiredInt(Map<String, dynamic> data, List<String> keys) {
    for (final key in keys) {
      final value = data[key];
      if (value is int) {
        return value;
      }
      if (value is num) {
        return value.toInt();
      }
      if (value is String) {
        final parsed = int.tryParse(value.trim());
        if (parsed != null) {
          return parsed;
        }
      }
    }

    throw const FormatException(
      'Dashboard payload is missing one or more required metrics.',
    );
  }
}
