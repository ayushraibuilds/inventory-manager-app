import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;
import 'session_service.dart';

class ApiService {
  static const String baseUrl = 'https://api.ondcsuperseller.com/v1';

  Future<String?> _getToken() async {
    return SessionService().getAccessToken();
  }

  Future<Map<String, String>> _getHeaders() async {
    final token = await _getToken();
    return {
      'Content-Type': 'application/json',
      if (token != null) 'Authorization': 'Bearer $token',
    };
  }

  Future<dynamic> getOrders() async {
    try {
      final headers = await _getHeaders();
      final response = await http.get(Uri.parse('$baseUrl/orders'), headers: headers);
      
      if (response.statusCode == 200) {
        return json.decode(response.body);
      } else {
        throw Exception('Failed to load orders: \${response.statusCode}');
      }
    } on SocketException {
      throw Exception('Network error: Cannot load orders while offline.');
    }
  }

  Future<dynamic> getProducts() async {
    try {
      final headers = await _getHeaders();
      final response = await http.get(Uri.parse('$baseUrl/products'), headers: headers);
      
      if (response.statusCode == 200) {
        return json.decode(response.body);
      } else {
        throw Exception('Failed to load products: \${response.statusCode}');
      }
    } on SocketException {
      throw Exception('Network error: Cannot load products while offline.');
    }
  }

  Future<dynamic> addCatalogItem(Map<String, dynamic> item) async {
    try {
      final headers = await _getHeaders();
      final response = await http.post(
        Uri.parse('$baseUrl/products'), 
        headers: headers,
        body: json.encode(item)
      );
      
      if (response.statusCode == 201 || response.statusCode == 200) {
        return json.decode(response.body);
      } else {
        throw Exception('Failed to add product: ${response.statusCode}');
      }
    } on SocketException {
      throw Exception('Network error: Check your internet connection (Offline).');
    }
  }

  Future<String> sendAiCommand(String message) async {
    try {
      final headers = await _getHeaders();
      final response = await http.post(
        Uri.parse('$baseUrl/ai-command'),
        headers: headers,
        body: json.encode({'message': message}),
      );
      
      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        return data['response'] ?? 'Action completed successfully via backend agent.';
      } else {
        throw Exception('Failed to execute AI command: \${response.statusCode}');
      }
    } on SocketException {
      throw Exception('Network error: Action deferred, device offline.');
    }
  }

  Future<void> updateInventory(String barcode, int quantity) async {
    try {
      final headers = await _getHeaders();
      final response = await http.post(
        Uri.parse('$baseUrl/inventory/update'),
        headers: headers,
        body: json.encode({'barcode': barcode, 'quantity': quantity}),
      );
      
      if (response.statusCode != 200 && response.statusCode != 201) {
        throw Exception('Failed to update inventory: \${response.statusCode}');
      }
    } on SocketException {
      throw Exception('Network error: Unable to sync inventory changes online.');
    }
  }
}
