import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'core/theme/app_theme.dart';
import 'core/localization/app_localizations.dart';
import 'features/auth/providers.dart';
import 'features/onboarding/presentation/onboarding_flow.dart';
import 'features/notifications/providers.dart';
import 'features/shell/presentation/app_shell.dart';

final appNavigatorKey = GlobalKey<NavigatorState>();

class SwipeWearApp extends ConsumerWidget {
  const SwipeWearApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final locale = ref.watch(localeControllerProvider).locale;
    return MaterialApp(
      title: 'SwipeWear',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.light,
      locale: locale,
      supportedLocales: const [Locale('fr'), Locale('en')],
      localizationsDelegates: GlobalMaterialLocalizations.delegates,
      navigatorKey: appNavigatorKey,
      home: const AppGate(),
    );
  }
}

class AppGate extends ConsumerWidget {
  const AppGate({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l = AppLocalizations.of(context);
    ref.listen(sessionProvider, (_, next) {
      next.whenData(
        (session) => ref
            .read(pushNotificationServiceProvider)
            .initialize(session, navigatorKey: appNavigatorKey),
      );
    });
    final session = ref.watch(sessionProvider);
    return session.when(
      loading: () => _LoadingScreen(label: l.t('Préparation de ton espace…')),
      error:
          (_, __) =>
              _ErrorScreen(onRetry: () => ref.invalidate(sessionProvider)),
      data: (value) {
        Future<void>.microtask(
          () => ref
              .read(pushNotificationServiceProvider)
              .initialize(value, navigatorKey: appNavigatorKey),
        );
        final onboarding = ref.watch(onboardingCompleteProvider);
        return onboarding.when(
          loading:
              () =>
                  _LoadingScreen(label: l.t('Chargement de tes préférences…')),
          error: (_, __) => const OnboardingFlow(),
          data:
              (complete) =>
                  complete ? const AppShell() : const OnboardingFlow(),
        );
      },
    );
  }
}

class _LoadingScreen extends StatelessWidget {
  const _LoadingScreen({required this.label});

  final String label;

  @override
  Widget build(BuildContext context) => Scaffold(
    body: Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          const CircularProgressIndicator(color: AppColors.accent),
          const SizedBox(height: 16),
          Text(label),
        ],
      ),
    ),
  );
}

class _ErrorScreen extends StatelessWidget {
  const _ErrorScreen({required this.onRetry});

  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) => Scaffold(
    body: Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.cloud_off_outlined, size: 48),
            const SizedBox(height: 16),
            Text(
              AppLocalizations.of(context).t('Connexion impossible'),
              style: const TextStyle(fontSize: 20, fontWeight: FontWeight.w800),
            ),
            const SizedBox(height: 8),
            Text(
              AppLocalizations.of(
                context,
              ).t('Vérifie le serveur puis réessaie.'),
            ),
            const SizedBox(height: 20),
            FilledButton(
              onPressed: onRetry,
              child: Text(AppLocalizations.of(context).t('Réessayer')),
            ),
          ],
        ),
      ),
    ),
  );
}
