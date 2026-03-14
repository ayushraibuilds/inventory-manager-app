import 'package:dio/dio.dart';
import 'package:shared_preferences/shared_preferences.dart';

class ApiService {
  ApiService._internal() {
    _dio = Dio(
      BaseOptions(
        baseUrl: _baseUrl,
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
          final preferences = await SharedPreferences.getInstance();
          final token = _readStoredToken(preferences);

          if (token != null && token.isNotEmpty) {
            options.headers['Authorization'] = 'Bearer $token';
          }

          handler.next(options);
        },
      ),
    );
  }

  static const String _baseUrl = 'https://your-production-url.com/api/v1/';
  static const List<String> _candidateTokenKeys = [
    'jwt',
    'jwt_token',
    'access_token',
    'token',
  ];

  static final ApiService _instance = ApiService._internal();

  factory ApiService() => _instance;

  late final Dio _dio;

  Future<Map<String, dynamic>> getDashboardStats() async {
    try {
      final response = await _dio.get('stats');
      return _extractMap(response.data);
    } on DioException catch (error) {
      throw Exception(_buildErrorMessage(error));
    }
  }

  Future<void> updateInventory(String barcode, int quantity) async {
    try {
      await _dio.post(
        'inventory',
        data: {'barcode': barcode, 'quantity': quantity},
      );
    } on DioException catch (error) {
      throw Exception(_buildErrorMessage(error));
    }
  }

  Future<String> sendAiCommand(String message) async {
    try {
      final response = await _dio.post(
        'agent/chat',
        data: {'message': message},
      );

      final payload = response.data;
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

      throw Exception('AI response payload did not contain a message.');
    } on DioException catch (error) {
      throw Exception(_buildErrorMessage(error));
    }
  }

  String? _readStoredToken(SharedPreferences preferences) {
    for (final key in _candidateTokenKeys) {
      final token = preferences.getString(key);
      if (token != null && token.trim().isNotEmpty) {
        return token.trim();
      }
    }

    return null;
  }

  Map<String, dynamic> _extractMap(dynamic payload) {
    if (payload is Map<String, dynamic>) {
      return payload;
    }

    if (payload is Map) {
      return Map<String, dynamic>.from(payload);
    }

    throw Exception('Unexpected API response format.');
  }

  String _buildErrorMessage(DioException error) {
    final data = error.response?.data;
    if (data is Map) {
      final map = Map<String, dynamic>.from(data);
      for (final key in ['detail', 'message', 'error']) {
        final value = map[key];
        if (value is String && value.trim().isNotEmpty) {
          return value;
        }
      }
    }

    return error.message ?? 'Unexpected network error.';
  }
}
