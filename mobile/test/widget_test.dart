import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:swipewear/features/auth/data/session.dart';
import 'package:swipewear/features/auth/providers.dart';
import 'package:swipewear/features/feed/data/feed_repository.dart';
import 'package:swipewear/features/feed/data/product.dart';
import 'package:swipewear/features/feed/providers.dart';
import 'package:swipewear/features/shell/presentation/app_shell.dart';
import 'package:swipewear/app.dart';

void main() {
  test('product exposes listing age and size fallback', () {
    final product = Product.fromJson({
      'id': 'p1',
      'title': 'Veste',
      'brand': 'Carhartt',
      'price': 42,
      'condition': 'good',
      'category': 'jackets',
      'size_eu': 'M',
      'image_urls': ['https://example.com/image.jpg'],
      'source': 'ebay',
      'enriched_attrs': {
        'created_at':
            DateTime.now()
                .toUtc()
                .subtract(const Duration(hours: 3))
                .toIso8601String(),
      },
    });

    expect(product.size, 'M');
    expect(product.ageLabel, startsWith('Il y a 3 h'));
  });

  testWidgets('SwipeWear renders the mobile shell', (
    WidgetTester tester,
  ) async {
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          sessionProvider.overrideWith(
            (ref) async =>
                const Session(userId: 'test-user', accessToken: 'test-token'),
          ),
          onboardingCompleteProvider.overrideWith((ref) async => true),
          feedProvider.overrideWith(
            (ref) async => const FeedResponse(items: []),
          ),
        ],
        child: const MaterialApp(
          locale: Locale('fr'),
          supportedLocales: [Locale('fr'), Locale('en')],
          localizationsDelegates: GlobalMaterialLocalizations.delegates,
          home: AppShell(),
        ),
      ),
    );
    await tester.pump(const Duration(milliseconds: 100));

    expect(
      find.byWidgetPredicate(
        (widget) =>
            widget is RichText && widget.text.toPlainText() == 'SwipeWear',
      ),
      findsOneWidget,
    );
    expect(find.byKey(const ValueKey('feed-title')), findsOneWidget);
    expect(find.text('Dressing'), findsOneWidget);
  });

  testWidgets('new session opens the style calibration', (tester) async {
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          sessionProvider.overrideWith(
            (ref) async =>
                const Session(userId: 'test-user', accessToken: 'test-token'),
          ),
          onboardingCompleteProvider.overrideWith((ref) async => false),
        ],
        child: const MaterialApp(
          locale: Locale('fr'),
          supportedLocales: [Locale('fr'), Locale('en')],
          localizationsDelegates: GlobalMaterialLocalizations.delegates,
          home: AppGate(),
        ),
      ),
    );
    for (var index = 0; index < 5; index++) {
      await tester.pump(const Duration(milliseconds: 100));
    }

    expect(find.textContaining('Ton style.'), findsOneWidget);
    expect(find.text('Continuer'), findsOneWidget);
  });
}
