import 'package:dio/dio.dart';

import '../config/app_config.dart';
import 'session_service.dart';

class ApiService {
  ApiService._internal() {
    _dio = Dio(
      BaseOptions(
        baseUrl: AppConfig.apiBaseUrl,
        connectTimeout: const Duration(seconds: 20),
        receiveTimeout: const Duration(seconds: 20),
        sendTimeout: const Duration(seconds: 20),
        contentType: Headers.jsonContentType,
        responseType: ResponseType.json,
      ),
    );

    _dio.interceptors.add(
      InterceptorsWrapper(
        onRequest: (options, handler) async {
          // Prefer Supabase access token, fall back to stored JWT/API key
          final accessToken = await SessionService().getAccessToken();
          final apiKey = await SessionService().readApiKey();

          if (accessToken != null && accessToken.isNotEmpty) {
            options.headers['Authorization'] = 'Bearer $accessToken';
          } else if (apiKey != null && apiKey.isNotEmpty) {
            options.headers['X-API-Key'] = apiKey;
          }

          final sellerId = SessionService().sellerId;
          if (sellerId != null && sellerId.isNotEmpty) {
            options.queryParameters['seller_id'] = sellerId;
          }

          handler.next(options);
        },
        onError: (error, handler) async {
          if (error.response?.statusCode == 401) {
            await SessionService().signOut();
          }
          handler.next(error);
        },
      ),
    );
  }

  static final ApiService _instance = ApiService._internal();
  factory ApiService() => _instance;
  late final Dio _dio;

  // ──────────────────────────────────────────────
  // Catalog
  // ──────────────────────────────────────────────

  /// Fetch products from GET /api/catalog
  Future<List<Map<String, dynamic>>> getCatalog({String? search}) async {
    final queryParams = <String, dynamic>{
      'limit': 200,
      'offset': 0,
    };
    if (search != null && search.isNotEmpty) {
      queryParams['search'] = search;
    }

    final response = await _send(
      () => _dio.get('api/catalog', queryParameters: queryParams),
    );

    final data = _extractMap(response);
    final items = data['items'];
    if (items is List) {
      return items
          .whereType<Map>()
          .map((e) => Map<String, dynamic>.from(e))
          .toList(growable: false);
    }
    return [];
  }

  /// Add a product via POST /api/catalog/item
  Future<void> addProduct({
    required String name,
    required double price,
    required int quantity,
    String? category,
  }) async {
    await _send(
      () => _dio.post('api/catalog/item', data: {
        'name': name,
        'selling_price': price,
        'quantity': quantity,
        if (category != null && category.isNotEmpty) 'category': category,
      }),
    );
  }

  /// Update a product via PUT /api/catalog/item/{id}
  Future<void> updateProduct(String itemId, Map<String, dynamic> updates) async {
    await _send(
      () => _dio.put('api/catalog/item/$itemId', data: updates),
    );
  }

  /// Update inventory quantity by barcode — uses the catalog item update
  Future<void> updateInventory(String barcode, int quantity) async {
    // Search for the product by barcode, then update its quantity
    final products = await getCatalog(search: barcode);
    if (products.isEmpty) {
      // If not found, create a new product with the barcode as the name
      await addProduct(name: barcode, price: 0, quantity: quantity);
      return;
    }
    final product = products.first;
    final itemId = product['id']?.toString() ?? '';
    if (itemId.isEmpty) {
      throw const ApiException('Product found but has no ID.');
    }
    final currentQty = (product['quantity'] as num?)?.toInt() ?? 0;
    await updateProduct(itemId, {'quantity': currentQty + quantity});
  }

  /// Delete a product via DELETE /api/catalog/item/{id}
  Future<void> deleteProduct(String itemId) async {
    await _send(
      () => _dio.delete('api/catalog/item/$itemId'),
    );
  }

  /// Fetch recent activity from GET /api/activity
  Future<List<Map<String, dynamic>>> getActivity() async {
    final response = await _send(
      () => _dio.get('api/activity'),
    );

    final data = _extractMap(response);
    final activities = data['activities'] ?? data['items'] ?? data['events'];
    if (activities is List) {
      return activities
          .whereType<Map>()
          .map((e) => Map<String, dynamic>.from(e))
          .toList(growable: false);
    }
    return [];
  }

  // ──────────────────────────────────────────────
  // Dashboard stats (computed from catalog)
  // ──────────────────────────────────────────────

  /// Get dashboard stats from catalog data
  Future<Map<String, dynamic>> getDashboardStats() async {
    final products = await getCatalog();

    int totalProducts = products.length;
    double totalValue = 0;
    int lowStock = 0;

    for (final p in products) {
      final price = (p['selling_price'] ?? p['price'] ?? 0) as num;
      final qty = (p['quantity'] ?? 0) as num;
      totalValue += price.toDouble() * qty.toDouble();
      if (qty <= 5) lowStock++;
    }

    return {
      'stats': {
        'todays_orders': totalProducts,
        'pending_fulfillment': totalValue.round(),
        'low_stock_alerts': lowStock,
      },
    };
  }

  // ──────────────────────────────────────────────
  // AI Chat
  // ──────────────────────────────────────────────

  Future<String> sendAiCommand(String message) async {
    final payload = await _send(
      () => _dio.post('api/agent/chat', data: {'message': message}),
    );

    if (payload is String && payload.trim().isNotEmpty) {
      return payload;
    }

    final data = _extractMap(payload);
    for (final key in ['response', 'reply', 'message', 'content']) {
      final value = data[key];
      if (value is String && value.trim().isNotEmpty) {
        return value;
      }
    }

    throw const ApiException('AI response payload did not contain a message.');
  }

  // ──────────────────────────────────────────────
  // Session verification
  // ──────────────────────────────────────────────

  Future<List<String>> verifySession({String? jwt, String? apiKey}) async {
    final response = await _send(
      () => _dio.get(
        'api/sellers',
        options: Options(
          headers: _authHeaders(jwt: jwt, apiKey: apiKey),
        ),
      ),
    );
    final payload = _extractMap(response);
    final sellers = payload['sellers'];
    if (sellers is List) {
      return sellers
          .whereType<String>()
          .map((seller) => seller.trim())
          .where((seller) => seller.isNotEmpty)
          .toList(growable: false);
    }
    throw const ApiException(
      'Session verification response did not contain sellers.',
    );
  }

  // ──────────────────────────────────────────────
  // Helpers
  // ──────────────────────────────────────────────

  Future<dynamic> _send(Future<Response<dynamic>> Function() request) async {
    try {
      final response = await request();
      return response.data;
    } on DioException catch (error) {
      if (error.response?.statusCode == 401) {
        throw const UnauthorizedException();
      }
      throw ApiException(_buildErrorMessage(error));
    }
  }

  Map<String, dynamic> _extractMap(dynamic payload) {
    if (payload is Map<String, dynamic>) return payload;
    if (payload is Map) return Map<String, dynamic>.from(payload);
    throw const ApiException('Unexpected API response format.');
  }

  String _buildErrorMessage(DioException error) {
    final data = error.response?.data;
    if (data is Map) {
      final map = Map<String, dynamic>.from(data);
      for (final key in ['detail', 'message', 'error']) {
        final value = map[key];
        if (value is String && value.trim().isNotEmpty) return value;
      }
    }
    return error.message ?? 'Unexpected network error.';
  }

  Map<String, dynamic> _authHeaders({String? jwt, String? apiKey}) {
    if (jwt != null && jwt.trim().isNotEmpty) {
      return {'Authorization': 'Bearer ${jwt.trim()}'};
    }
    if (apiKey != null && apiKey.trim().isNotEmpty) {
      return {'X-API-Key': apiKey.trim()};
    }
    return const {};
  }
}

class ApiException implements Exception {
  const ApiException(this.message);
  final String message;
  @override
  String toString() => message;
}

class UnauthorizedException extends ApiException {
  const UnauthorizedException()
    : super('Your session expired. Please sign in again.');
}
