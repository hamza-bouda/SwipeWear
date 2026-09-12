import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/analytics/providers.dart';
import '../../../core/localization/app_localizations.dart';
import '../../../core/widgets/offline_banner.dart';
import '../../../core/network/api_client.dart';
import '../../../core/theme/app_theme.dart';
import '../../auth/providers.dart';
import '../../billing/presentation/paywall_screen.dart';
import '../../billing/providers.dart';
import '../../profile/providers.dart';
import '../../onboarding/data/style_archetypes.dart';
import '../../shared/widgets/product_tile.dart';
import '../data/alerts_repository.dart';
import '../providers.dart';

class AlertsScreen extends ConsumerStatefulWidget {
  const AlertsScreen({super.key});

  @override
  ConsumerState<AlertsScreen> createState() => _AlertsScreenState();
}

class _AlertsScreenState extends ConsumerState<AlertsScreen> {
  String _filter = 'Actives';

  Future<void> _showCreate(BuildContext context, WidgetRef ref) async {
    final l = AppLocalizations.of(context);
    final existing = ref.read(alertsProvider).valueOrNull;
    final premium = ref.read(billingProvider).valueOrNull?.isPremium == true;
    if (existing != null &&
        existing.activeCount >= existing.freeLimit &&
        !premium) {
      await Navigator.push(
        context,
        MaterialPageRoute(
          builder: (_) => const PaywallScreen(trigger: 'alert_limit'),
        ),
      );
      return;
    }
    final snapshot = ref.read(profileProvider).valueOrNull;
    final result = await _showAlertEditor(
      context,
      initialSizes: snapshot?.sizes ?? const [],
    );
    if (result == null || result.label.isEmpty || !context.mounted) return;
    try {
      final session = await ref.read(sessionProvider.future);
      await ref
          .read(alertsRepositoryProvider)
          .create(
            session,
            label: result.label,
            type: 'style',
            maxPrice: result.budget,
            sizes: result.sizes,
            minCondition: result.minCondition,
          );
      unawaited(
        ref
            .read(analyticsServiceProvider)
            .track(session, 'alert_created', properties: {'type': 'style'}),
      );
      ref.invalidate(alertsProvider);
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(l.t('Alerte créée. On chine pour toi.'))),
        );
      }
    } on ApiException catch (error) {
      if (context.mounted) {
        if (error.statusCode == 403) {
          await Navigator.push(
            context,
            MaterialPageRoute(
              builder: (_) => const PaywallScreen(trigger: 'alert_limit'),
            ),
          );
        } else {
          ScaffoldMessenger.of(
            context,
          ).showSnackBar(SnackBar(content: Text(error.message)));
        }
      }
    }
  }

  Future<void> _showEdit(
    BuildContext context,
    WidgetRef ref,
    AlertItem alert,
  ) async {
    final l = AppLocalizations.of(context);
    final result = await _showAlertEditor(
      context,
      existing: alert,
      initialSizes: alert.sizes,
    );
    if (result == null || !context.mounted) return;
    try {
      final session = await ref.read(sessionProvider.future);
      await ref
          .read(alertsRepositoryProvider)
          .updateConstraints(
            session,
            alert,
            maxPrice: result.budget,
            sizes: result.sizes,
            minCondition: result.minCondition,
          );
      unawaited(
        ref
            .read(analyticsServiceProvider)
            .track(session, 'alert_updated', properties: {'type': alert.type}),
      );
      ref.invalidate(alertsProvider);
      if (context.mounted) {
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(SnackBar(content: Text(l.t('Alerte mise à jour.'))));
      }
    } on ApiException catch (error) {
      if (context.mounted) {
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(SnackBar(content: Text(error.message)));
      }
    }
  }

  Future<_AlertDraft?> _showAlertEditor(
    BuildContext context, {
    AlertItem? existing,
    required List<String> initialSizes,
  }) async {
    final l = AppLocalizations.of(context);
    final labelController = TextEditingController(text: existing?.label);
    final budgetController = TextEditingController(
      text: existing?.maxPrice?.toStringAsFixed(0) ?? '',
    );
    final selectedSizes = {...initialSizes};
    var minCondition = existing?.minCondition ?? 'Toutes';
    String? editorError;
    final result = await showModalBottomSheet<_AlertDraft>(
      context: context,
      isScrollControlled: true,
      showDragHandle: true,
      builder:
          (context) => Padding(
            padding: EdgeInsets.fromLTRB(
              24,
              8,
              24,
              MediaQuery.viewInsetsOf(context).bottom + 24,
            ),
            child: StatefulBuilder(
              builder:
                  (context, setModalState) => SingleChildScrollView(
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          existing == null
                              ? l.t('Nouvelle alerte')
                              : l.t('Modifier ton alerte'),
                          style: Theme.of(context).textTheme.headlineSmall
                              ?.copyWith(fontWeight: FontWeight.w900),
                        ),
                        const SizedBox(height: 6),
                        Text(
                          existing == null
                              ? l.t(
                                'Décris la pièce que tu veux chasser et affine les critères.',
                              )
                              : l.t('Ajuste les critères de ta chasse.'),
                        ),
                        const SizedBox(height: 20),
                        if (existing == null) ...[
                          TextField(
                            controller: labelController,
                            autofocus: true,
                            decoration: InputDecoration(
                              labelText: l.t('Recherche'),
                              hintText: l.t('Ex. veste en cuir vintage'),
                            ),
                          ),
                          const SizedBox(height: 16),
                        ] else ...[
                          InputDecorator(
                            decoration: InputDecoration(
                              labelText: l.t('Recherche'),
                            ),
                            child: Text(
                              existing.label,
                              style: const TextStyle(
                                fontWeight: FontWeight.w700,
                              ),
                            ),
                          ),
                          const SizedBox(height: 16),
                        ],
                        Text(
                          l.t('Tailles recherchées'),
                          style: const TextStyle(fontWeight: FontWeight.w800),
                        ),
                        const SizedBox(height: 8),
                        Wrap(
                          spacing: 7,
                          runSpacing: 7,
                          children:
                              _alertSizes
                                  .map(
                                    (size) => ChoiceChip(
                                      label: Text(size),
                                      selected: selectedSizes.contains(size),
                                      onSelected:
                                          (_) => setModalState(() {
                                            if (!selectedSizes.add(size)) {
                                              selectedSizes.remove(size);
                                            }
                                          }),
                                    ),
                                  )
                                  .toList(),
                        ),
                        const SizedBox(height: 14),
                        TextField(
                          controller: budgetController,
                          keyboardType: const TextInputType.numberWithOptions(
                            decimal: true,
                          ),
                          decoration: InputDecoration(
                            labelText: l.t('Budget maximum (optionnel)'),
                            suffixText: '€',
                          ),
                        ),
                        const SizedBox(height: 14),
                        DropdownButtonFormField<String>(
                          value: minCondition,
                          decoration: InputDecoration(
                            labelText: l.t('État minimum'),
                          ),
                          items:
                              _conditionOptions
                                  .map(
                                    (item) => DropdownMenuItem(
                                      value: item.value,
                                      child: Text(l.t(item.label)),
                                    ),
                                  )
                                  .toList(),
                          onChanged: (value) {
                            if (value != null) {
                              setModalState(() => minCondition = value);
                            }
                          },
                        ),
                        const SizedBox(height: 20),
                        if (editorError != null)
                          Padding(
                            padding: const EdgeInsets.only(bottom: 8),
                            child: Text(
                              editorError!,
                              style: const TextStyle(
                                color: AppColors.error,
                                fontSize: 12,
                              ),
                            ),
                          ),
                        FilledButton(
                          onPressed: () {
                            final label =
                                existing?.label ?? labelController.text.trim();
                            final rawBudget = budgetController.text.trim();
                            final budget =
                                rawBudget.isEmpty
                                    ? null
                                    : double.tryParse(
                                      rawBudget.replaceAll(',', '.'),
                                    );
                            if (label.isEmpty) {
                              setModalState(
                                () =>
                                    editorError = l.t(
                                      'Décris la pièce que tu recherches.',
                                    ),
                              );
                              return;
                            }
                            if (rawBudget.isNotEmpty &&
                                (budget == null || budget <= 0)) {
                              setModalState(
                                () =>
                                    editorError = l.t(
                                      'Indique un budget valide.',
                                    ),
                              );
                              return;
                            }
                            Navigator.pop(
                              context,
                              _AlertDraft(
                                label,
                                budget,
                                selectedSizes.toList(),
                                minCondition == 'Toutes' ? null : minCondition,
                              ),
                            );
                          },
                          child: Text(
                            existing == null
                                ? l.t('Créer mon alerte')
                                : l.t('Enregistrer les critères'),
                          ),
                        ),
                        const SizedBox(height: 6),
                        Text(
                          l.t(
                            'Les sources légales disponibles sont surveillées automatiquement.',
                          ),
                          style: const TextStyle(
                            color: AppColors.textSecondary,
                            fontSize: 12,
                          ),
                        ),
                      ],
                    ),
                  ),
            ),
          ),
    );
    // The modal route may still be reversing when its Future completes. Keep
    // the controllers alive through that animation to avoid stale TextFields.
    await Future<void>.delayed(const Duration(milliseconds: 500));
    labelController.dispose();
    budgetController.dispose();
    return result;
  }

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    final ref = this.ref;
    final alerts = ref.watch(alertsProvider);
    return Scaffold(
      backgroundColor: Colors.transparent,
      body: SafeArea(
        child: alerts.when(
          loading:
              () => const Center(
                child: CircularProgressIndicator(color: AppColors.accent),
              ),
          error:
              (error, _) => Center(
                child: Padding(
                  padding: const EdgeInsets.all(24),
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      const Icon(Icons.notifications_off_outlined, size: 48),
                      const SizedBox(height: 12),
                      Text(
                        l.t('Alertes indisponibles'),
                        style: const TextStyle(
                          fontWeight: FontWeight.w900,
                          fontSize: 19,
                        ),
                      ),
                      Text(
                        error.toString(),
                        textAlign: TextAlign.center,
                        style: const TextStyle(color: AppColors.textSecondary),
                      ),
                      TextButton(
                        onPressed: () => ref.invalidate(alertsProvider),
                        child: Text(l.t('Réessayer')),
                      ),
                    ],
                  ),
                ),
              ),
          data: (snapshot) {
            final visibleAlerts =
                snapshot.alerts
                    .where(
                      (alert) => switch (_filter) {
                        'Actives' => alert.active,
                        'En pause' => !alert.active,
                        _ => true,
                      },
                    )
                    .toList();
            final premium =
                ref.read(billingProvider).valueOrNull?.isPremium == true;
            final limitReached =
                snapshot.activeCount >= snapshot.freeLimit && !premium;
            return RefreshIndicator(
              onRefresh: () async {
                ref.invalidate(alertsProvider);
                await ref.read(alertsProvider.future);
              },
              child: CustomScrollView(
                slivers: [
                  if (snapshot.isOffline)
                    const SliverToBoxAdapter(child: OfflineBanner()),
                  SliverToBoxAdapter(
                    child: SectionHeader(
                      eyebrow: l.t('Chasse personnalisée'),
                      title: l.t('Mes alertes'),
                    ),
                  ),
                  SliverToBoxAdapter(
                    child: SizedBox(
                      height: 46,
                      child: ListView.separated(
                        padding: const EdgeInsets.symmetric(horizontal: 24),
                        scrollDirection: Axis.horizontal,
                        itemCount: _filters.length,
                        separatorBuilder: (_, __) => const SizedBox(width: 8),
                        itemBuilder: (_, index) {
                          final filter = _filters[index];
                          final count =
                              filter == 'Actives'
                                  ? snapshot.activeCount
                                  : filter == 'En pause'
                                  ? snapshot.alerts
                                      .where((alert) => !alert.active)
                                      .length
                                  : snapshot.alerts.length;
                          return ChoiceChip(
                            label: Text('${l.t(filter)} ($count)'),
                            selected: _filter == filter,
                            onSelected: (_) => setState(() => _filter = filter),
                          );
                        },
                      ),
                    ),
                  ),
                  if (snapshot.missedDeals > 0)
                    SliverToBoxAdapter(
                      child: Padding(
                        padding: const EdgeInsets.fromLTRB(24, 8, 24, 16),
                        child: Container(
                          padding: const EdgeInsets.all(16),
                          decoration: BoxDecoration(
                            color: AppColors.accentLight,
                            borderRadius: BorderRadius.circular(18),
                          ),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Row(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  const Icon(
                                    Icons.bolt,
                                    color: AppColors.textPrimary,
                                  ),
                                  const SizedBox(width: 10),
                                  Expanded(
                                    child: Text(
                                      l.isEnglish
                                          ? '${snapshot.missedDeals} missed find(s). Gold alerts you instantly instead of the free 30-minute delay.'
                                          : '${snapshot.missedDeals} pépite(s) ratée(s). Gold te prévient instantanément, au lieu du délai gratuit de 30 minutes.',
                                      style: const TextStyle(
                                        fontWeight: FontWeight.w700,
                                        height: 1.35,
                                      ),
                                    ),
                                  ),
                                ],
                              ),
                              const SizedBox(height: 6),
                              TextButton(
                                onPressed:
                                    () => Navigator.push(
                                      context,
                                      MaterialPageRoute(
                                        builder:
                                            (_) => const PaywallScreen(
                                              trigger: 'missed_deal',
                                            ),
                                      ),
                                    ),
                                child: Text(l.t('Découvrir Gold')),
                              ),
                            ],
                          ),
                        ),
                      ),
                    ),
                  ...(visibleAlerts.isEmpty
                      ? [
                        const SliverFillRemaining(
                          hasScrollBody: false,
                          child: _NoAlerts(),
                        ),
                      ]
                      : [
                        SliverPadding(
                          padding: const EdgeInsets.fromLTRB(20, 8, 20, 0),
                          sliver: SliverList(
                            delegate: SliverChildBuilderDelegate((
                              context,
                              index,
                            ) {
                              final alert = visibleAlerts[index];
                              return _AlertCard(
                                alert: alert,
                                onEdit: () => _showEdit(context, ref, alert),
                                onToggle: (value) async {
                                  final session = await ref.read(
                                    sessionProvider.future,
                                  );
                                  await ref
                                      .read(alertsRepositoryProvider)
                                      .setStatus(session, alert, value);
                                  ref.invalidate(alertsProvider);
                                },
                                onDelete: () async {
                                  final session = await ref.read(
                                    sessionProvider.future,
                                  );
                                  await ref
                                      .read(alertsRepositoryProvider)
                                      .remove(session, alert);
                                  unawaited(
                                    ref
                                        .read(analyticsServiceProvider)
                                        .track(
                                          session,
                                          'alert_deleted',
                                          properties: {'type': alert.type},
                                        ),
                                  );
                                  ref.invalidate(alertsProvider);
                                },
                              );
                            }, childCount: visibleAlerts.length),
                          ),
                        ),
                      ]),
                  SliverToBoxAdapter(
                    child: Padding(
                      padding: const EdgeInsets.fromLTRB(24, 16, 24, 120),
                      child: Column(
                        children: [
                          OutlinedButton.icon(
                            onPressed: () => _showCreate(context, ref),
                            icon: Icon(
                              limitReached
                                  ? Icons.workspace_premium_outlined
                                  : Icons.add,
                            ),
                            label: Text(
                              limitReached
                                  ? l.t('Passer en Gold pour continuer')
                                  : l.t('Nouvelle alerte'),
                            ),
                          ),
                          const SizedBox(height: 14),
                          Text(
                            l.t(
                              'Les alertes actives surveillent les nouvelles pièces correspondant à tes tailles et ton budget.',
                            ),
                            textAlign: TextAlign.center,
                            style: const TextStyle(
                              color: AppColors.textSecondary,
                              fontSize: 12,
                              height: 1.35,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                ],
              ),
            );
          },
        ),
      ),
    );
  }
}

const _filters = ['Actives', 'En pause', 'Toutes'];

class _AlertDraft {
  const _AlertDraft(this.label, this.budget, this.sizes, this.minCondition);
  final String label;
  final double? budget;
  final List<String> sizes;
  final String? minCondition;
}

class _ConditionOption {
  const _ConditionOption(this.value, this.label);
  final String value;
  final String label;
}

const _alertSizes = [...availableSizes];
const _conditionOptions = [
  _ConditionOption('Toutes', 'Tous les états'),
  _ConditionOption('like_new', 'Très bon état minimum'),
  _ConditionOption('good', 'Bon état minimum'),
  _ConditionOption('fair', 'État correct minimum'),
  _ConditionOption('new', 'Neuf uniquement'),
];

class _AlertCard extends StatelessWidget {
  const _AlertCard({
    required this.alert,
    required this.onEdit,
    required this.onToggle,
    required this.onDelete,
  });
  final AlertItem alert;
  final VoidCallback onEdit;
  final ValueChanged<bool> onToggle;
  final VoidCallback onDelete;

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    final priceLabel =
        alert.maxPrice == null
            ? l.t('Sans budget max')
            : 'Max ${l.price(alert.maxPrice!)}';
    final sizesLabel =
        alert.sizes.isEmpty ? l.t('Toutes tailles') : alert.sizes.join(', ');
    final conditionLabel =
        alert.minCondition == null
            ? ''
            : ' · ${l.t(_conditionLabel(alert.minCondition!))}';
    return Card(
      margin: const EdgeInsets.only(bottom: 10),
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Row(
          children: [
            Container(
              width: 42,
              height: 42,
              decoration: BoxDecoration(
                color: alert.active ? AppColors.accentLight : AppColors.surface,
                borderRadius: BorderRadius.circular(14),
              ),
              child: Icon(
                alert.active
                    ? Icons.notifications_active
                    : Icons.notifications_none,
                color:
                    alert.active
                        ? AppColors.textPrimary
                        : AppColors.textSecondary,
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    alert.label,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: const TextStyle(fontWeight: FontWeight.w800),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    '$priceLabel · $sizesLabel$conditionLabel',
                    style: const TextStyle(
                      color: AppColors.textSecondary,
                      fontSize: 12,
                    ),
                  ),
                ],
              ),
            ),
            IconButton(
              onPressed: onEdit,
              icon: const Icon(Icons.tune_rounded),
              tooltip: l.t('Modifier'),
            ),
            Switch(value: alert.active, onChanged: onToggle),
            IconButton(
              onPressed: onDelete,
              icon: const Icon(Icons.delete_outline),
              tooltip: l.t('Supprimer'),
            ),
          ],
        ),
      ),
    );
  }
}

String _conditionLabel(String value) => switch (value) {
  'new' => 'Neuf uniquement',
  'like_new' => 'Très bon état +',
  'good' => 'Bon état +',
  'fair' => 'État correct +',
  _ => value,
};

class _NoAlerts extends StatelessWidget {
  const _NoAlerts();
  @override
  Widget build(BuildContext context) => Center(
    child: Padding(
      padding: const EdgeInsets.all(28),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          const Icon(
            Icons.notifications_none,
            size: 52,
            color: AppColors.textSecondary,
          ),
          const SizedBox(height: 14),
          Text(
            AppLocalizations.of(context).t('Aucune alerte active'),
            style: Theme.of(
              context,
            ).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w900),
          ),
          const SizedBox(height: 8),
          Text(
            AppLocalizations.of(context).t(
              'Crée une alerte pour que SwipeWear chine même quand tu n’es pas dans l’app.',
            ),
            textAlign: TextAlign.center,
            style: const TextStyle(color: AppColors.textSecondary, height: 1.4),
          ),
        ],
      ),
    ),
  );
}
