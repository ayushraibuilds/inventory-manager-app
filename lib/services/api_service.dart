import 'dart:convert';
import 'package:http/http.dart' as http;
// import 'package:shared_preferences/shared_preferences.dart';

class ApiService {
  static const String baseUrl = 'https://api.ondcsuperseller.com/v1';

  Future<String?> _getToken() async {
    // Scaffold token retrieval
    return "MOCK_TOKEN";
  }

  Future<Map<String, String>> _getHeaders() async {
    final token = await _getToken();
    return {
      'Content-Type': 'application/json',
      if (token != null) 'Authorization': 'Bearer $token',
    };
  }

  Future<dynamic> getOrders() async {
    // Handle offline mode and real backend endpoints
    final headers = await _getHeaders();
    final response = await http.get(Uri.parse('$baseUrl/orders'), headers: headers);
    
    if (response.statusCode == 200) {
      return json.decode(response.body);
    } else {
      throw Exception('Failed to load orders: ${response.statusCode}');
    }
  }

  // Real API methods
}
