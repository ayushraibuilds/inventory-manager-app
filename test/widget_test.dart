import 'package:flutter_test/flutter_test.dart';
import 'package:ondc_seller_app/main.dart';

void main() {
  testWidgets('renders seller shell with pulse dashboard', (
    WidgetTester tester,
  ) async {
    await tester.pumpWidget(
      SellerApp(
        dashboardLoader: () async => {
          'todays_orders': 12,
          'pending_fulfillment': 4,
          'low_stock_alerts': 2,
        },
      ),
    );
    await tester.pumpAndSettle();

    expect(find.text('Seller Pulse'), findsOneWidget);
    expect(find.text('Scanner'), findsOneWidget);
    expect(find.text('AI Center'), findsOneWidget);
  });
}
