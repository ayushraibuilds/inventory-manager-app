import 'package:flutter_test/flutter_test.dart';
import 'package:ondc_seller_app/services/api_service.dart';

void main() {
  group('ApiService Tests', () {
    late ApiService apiService;

    setUp(() {
      apiService = ApiService();
    });

    test('ApiService generates correct base URL', () {
      expect(ApiService.baseUrl, equals('https://api.ondcsuperseller.com/v1'));
    });
    
    // We would mock HTTP calls here using mockito for a full test suite
  });
}
