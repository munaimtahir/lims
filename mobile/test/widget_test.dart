import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:lims_mobile/presentation/screens/login/login_screen.dart';

void main() {
  testWidgets('Login form should show validation errors when empty', (WidgetTester tester) async {
    await tester.pumpWidget(
      const ProviderScope(
        child: MaterialApp(
          home: LoginScreen(),
        ),
      ),
    );

    // Find the login button
    final loginButton = find.byType(ElevatedButton);
    expect(loginButton, findsOneWidget);

    // Tap it without entering anything
    await tester.tap(loginButton);
    await tester.pump();

    // Should see "Required" error messages
    expect(find.text('Required'), findsNWidgets(2));
  });
}
