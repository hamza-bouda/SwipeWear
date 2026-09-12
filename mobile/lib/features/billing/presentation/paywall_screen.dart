import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/analytics/providers.dart';
import '../../../core/localization/app_localizations.dart';
import '../../../core/theme/app_theme.dart';
import '../../auth/providers.dart';
import '../data/revenuecat_service.dart';
import '../providers.dart';

class PaywallScreen extends ConsumerStatefulWidget {
  const PaywallScreen({super.key, this.trigger = 'profile'});

  final String trigger;

  @override
  ConsumerState<PaywallScreen> createState() => _PaywallScreenState();
}

class _PaywallScreenState extends ConsumerState<PaywallScreen> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) => _trackViewed());
  }

  Future<void> _trackViewed() async {
    try {
      final session = await ref.read(sessionProvider.future);
      await ref
          .read(analyticsServiceProvider)
          .track(
            session,
            'paywall_viewed',
            properties: {'trigger': widget.trigger},
          );
    } catch (_) {}
  }

  Future<void> _purchase(
    BuildContext context,
    WidgetRef ref, {
    bool annual = false,
  }) async {
    try {
      final session = await ref.read(sessionProvider.future);
      final result = await RevenueCatService.purchase(session, annual: annual);
      if (!context.mounted) return;
      if (result.active) {
        ref.invalidate(billingProvider);
        unawaited(
          ref
              .read(analyticsServiceProvider)
              .track(
                session,
                'subscribe',
                properties: {
                  'trigger': widget.trigger,
                  'plan': annual ? 'annual' : 'monthly',
                },
              ),
        );
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(
              AppLocalizations.of(context).t('Bienvenue dans SwipeWear Gold.'),
            ),
          ),
        );
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(
              result.message ?? AppLocalizations.of(context).t('Achat annulé.'),
            ),
          ),
        );
      }
    } catch (error) {
      if (context.mounted) {
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(SnackBar(content: Text('Achat impossible : $error')));
      }
    }
  }

  Future<void> _restore(BuildContext context, WidgetRef ref) async {
    try {
      final session = await ref.read(sessionProvider.future);
      final result = await RevenueCatService.restore(session);
      if (!context.mounted) return;
      ref.invalidate(billingProvider);
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            result.active
                ? 'Ton abonnement Gold est restauré.'
                : 'Aucun abonnement actif trouvé.',
          ),
        ),
      );
    } catch (error) {
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Restauration impossible : $error')),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    final status = ref.watch(billingProvider);
    return Scaffold(
      appBar: AppBar(
        title: Text(
          l.t('SwipeWear Gold'),
          style: const TextStyle(fontWeight: FontWeight.w900),
        ),
      ),
      body: ListView(
        padding: const EdgeInsets.fromLTRB(24, 12, 24, 32),
        children: [
          Container(
            padding: const EdgeInsets.all(22),
            decoration: BoxDecoration(
              color: AppColors.textPrimary,
              borderRadius: BorderRadius.circular(26),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  l.t('Chine avant tout le monde.'),
                  style: const TextStyle(
                    color: Colors.white,
                    fontWeight: FontWeight.w900,
                    fontSize: 26,
                    height: 1.05,
                  ),
                ),
                const SizedBox(height: 10),
                Text(
                  _triggerCopy(l, widget.trigger),
                  style: const TextStyle(color: Colors.white70, height: 1.4),
                ),
                const SizedBox(height: 20),
                const Text(
                  '4,99 € / mois',
                  style: TextStyle(
                    color: AppColors.accent,
                    fontWeight: FontWeight.w900,
                    fontSize: 24,
                  ),
                ),
                const Text(
                  'ou 39,99 € / an',
                  style: TextStyle(color: Colors.white70, fontSize: 12),
                ),
              ],
            ),
          ),
          const SizedBox(height: 24),
          _Benefit(
            icon: Icons.bolt,
            title: l.t('Alertes instantanées'),
            detail: l.t(
              'Sois averti dès qu’une pépite correspond à ton style.',
            ),
          ),
          _Benefit(
            icon: Icons.notifications_active_outlined,
            title: l.t('Alertes illimitées'),
            detail: l.t(
              'Chasse plusieurs styles, tailles et budgets en parallèle.',
            ),
          ),
          _Benefit(
            icon: Icons.local_fire_department_outlined,
            title: l.t('Drop sans friction'),
            detail: l.t(
              'Ne rate plus les pièces rares avant qu’elles ne partent.',
            ),
          ),
          const SizedBox(height: 22),
          status.when(
            loading:
                () => const Center(
                  child: CircularProgressIndicator(color: AppColors.accent),
                ),
            error:
                (_, __) =>
                    _Unavailable(onPurchase: () => _purchase(context, ref)),
            data:
                (value) =>
                    value.isPremium
                        ? const _ActiveGold()
                        : Column(
                          children: [
                            FilledButton(
                              onPressed: () => _purchase(context, ref),
                              child: Text(l.t('Essai 7 jours · 4,99 € / mois')),
                            ),
                            const SizedBox(height: 10),
                            OutlinedButton(
                              onPressed:
                                  () => _purchase(context, ref, annual: true),
                              child: Text(l.t('Essai 7 jours · 39,99 € / an')),
                            ),
                            const SizedBox(height: 10),
                            TextButton(
                              onPressed: () => _restore(context, ref),
                              child: Text(l.t('Restaurer mon abonnement')),
                            ),
                            const SizedBox(height: 4),
                            Text(
                              l.t(
                                'Abonnement sécurisé via l’App Store ou Google Play.',
                              ),
                              textAlign: TextAlign.center,
                              style: TextStyle(
                                fontSize: 11,
                                color: AppColors.textSecondary,
                              ),
                            ),
                          ],
                        ),
          ),
        ],
      ),
    );
  }

  String _triggerCopy(AppLocalizations l, String source) => switch (source) {
    'alert_limit' => l.t(
      'Tu as atteint la limite gratuite. Gold garde toutes tes chasses actives.',
    ),
    'drop_completed' => l.t(
      'Le Drop est épuisé. Gold ajoute la priorité et les alertes illimitées.',
    ),
    _ => l.t(
      'Les membres Gold reçoivent les trouvailles avant le délai gratuit de 30 minutes.',
    ),
  };
}

class _Benefit extends StatelessWidget {
  const _Benefit({
    required this.icon,
    required this.title,
    required this.detail,
  });
  final IconData icon;
  final String title;
  final String detail;
  @override
  Widget build(BuildContext context) => Padding(
    padding: const EdgeInsets.only(bottom: 16),
    child: Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Container(
          width: 42,
          height: 42,
          decoration: BoxDecoration(
            color: AppColors.accentLight,
            borderRadius: BorderRadius.circular(14),
          ),
          child: Icon(icon),
        ),
        const SizedBox(width: 12),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(title, style: const TextStyle(fontWeight: FontWeight.w900)),
              const SizedBox(height: 3),
              Text(
                detail,
                style: const TextStyle(
                  color: AppColors.textSecondary,
                  fontSize: 13,
                  height: 1.3,
                ),
              ),
            ],
          ),
        ),
      ],
    ),
  );
}

class _ActiveGold extends StatelessWidget {
  const _ActiveGold();
  @override
  Widget build(BuildContext context) => Container(
    padding: const EdgeInsets.all(16),
    decoration: BoxDecoration(
      color: AppColors.accentLight,
      borderRadius: BorderRadius.circular(18),
    ),
    child: Row(
      children: [
        const Icon(Icons.verified, color: AppColors.success),
        const SizedBox(width: 10),
        Expanded(
          child: Text(
            AppLocalizations.of(context).t('Ton abonnement Gold est actif.'),
            style: const TextStyle(fontWeight: FontWeight.w800),
          ),
        ),
      ],
    ),
  );
}

class _Unavailable extends StatelessWidget {
  const _Unavailable({required this.onPurchase});
  final VoidCallback onPurchase;
  @override
  Widget build(BuildContext context) => Column(
    children: [
      Text(
        AppLocalizations.of(
          context,
        ).t('Le statut Gold sera disponible dès que le serveur est connecté.'),
        textAlign: TextAlign.center,
        style: const TextStyle(color: AppColors.textSecondary),
      ),
      const SizedBox(height: 12),
      OutlinedButton(
        onPressed: onPurchase,
        child: Text(AppLocalizations.of(context).t('Réessayer')),
      ),
    ],
  );
}
