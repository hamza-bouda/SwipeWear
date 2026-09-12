import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/theme/app_theme.dart';
import '../../../core/localization/app_localizations.dart';
import '../../auth/providers.dart';
import '../data/profile.dart';
import '../providers.dart';
import '../providers_extra.dart';

class AlgorithmScreen extends ConsumerWidget {
  const AlgorithmScreen({super.key});

  Future<void> _add(BuildContext context, WidgetRef ref) async {
    final draft = await _showPreferenceEditor(context);
    if (draft == null || !context.mounted) return;
    try {
      final session = await ref.read(sessionProvider.future);
      await ref
          .read(profileRepositoryProvider)
          .addPreference(session, draft.attribute, draft.value);
      ref.invalidate(algorithmPreferencesProvider);
    } catch (_) {
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(
              AppLocalizations.of(
                context,
              ).t('Impossible d’ajouter cette préférence.'),
            ),
          ),
        );
      }
    }
  }

  Future<void> _remove(
    BuildContext context,
    WidgetRef ref,
    PreferenceItem item,
  ) async {
    try {
      final session = await ref.read(sessionProvider.future);
      await ref
          .read(profileRepositoryProvider)
          .removePreference(session, item.id);
      ref.invalidate(algorithmPreferencesProvider);
      ref.invalidate(profileProvider);
    } catch (_) {
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(
              AppLocalizations.of(
                context,
              ).t('Impossible de retirer cette préférence.'),
            ),
          ),
        );
      }
    }
  }

  Future<void> _toggleLock(
    BuildContext context,
    WidgetRef ref,
    PreferenceItem item,
  ) async {
    try {
      final session = await ref.read(sessionProvider.future);
      await ref
          .read(profileRepositoryProvider)
          .setPreferenceLocked(session, item.id, locked: !item.locked);
      ref.invalidate(algorithmPreferencesProvider);
      ref.invalidate(profileProvider);
    } catch (_) {
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(
              AppLocalizations.of(
                context,
              ).t('Impossible de modifier cette préférence.'),
            ),
          ),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l = AppLocalizations.of(context);
    final preferences = ref.watch(algorithmPreferencesProvider);
    return Scaffold(
      appBar: AppBar(
        title: Text(
          l.t('Mon algorithme'),
          style: const TextStyle(fontWeight: FontWeight.w900),
        ),
        actions: [
          IconButton(
            onPressed: () => _add(context, ref),
            icon: const Icon(Icons.add),
            tooltip: l.t('Ajouter une préférence'),
          ),
        ],
      ),
      body: preferences.when(
        loading:
            () => const Center(
              child: CircularProgressIndicator(color: AppColors.accent),
            ),
        error:
            (_, __) => Center(
              child: TextButton(
                onPressed: () => ref.invalidate(algorithmPreferencesProvider),
                child: Text(l.t('Charger mon algorithme')),
              ),
            ),
        data:
            (items) => RefreshIndicator(
              onRefresh: () async {
                ref.invalidate(algorithmPreferencesProvider);
                await ref.read(algorithmPreferencesProvider.future);
              },
              child: ListView(
                padding: const EdgeInsets.fromLTRB(24, 14, 24, 120),
                children: [
                  const _AlgorithmIntro(),
                  const SizedBox(height: 22),
                  if (items.isEmpty)
                    const _EmptyAlgorithm()
                  else ...[
                    for (final group in _groups)
                      _PreferenceGroup(
                        title: l.t(group.title),
                        items:
                            items.where((item) => group.matches(item)).toList(),
                        onRemove: (item) => _remove(context, ref, item),
                        onToggleLock: (item) => _toggleLock(context, ref, item),
                      ),
                  ],
                  const SizedBox(height: 18),
                  OutlinedButton.icon(
                    onPressed: () => _add(context, ref),
                    icon: const Icon(Icons.add),
                    label: Text(l.t('Ajouter une préférence')),
                  ),
                ],
              ),
            ),
      ),
    );
  }
}

class _AlgorithmIntro extends StatelessWidget {
  const _AlgorithmIntro();

  @override
  Widget build(BuildContext context) => Container(
    padding: const EdgeInsets.all(18),
    decoration: BoxDecoration(
      color: AppColors.textPrimary,
      borderRadius: BorderRadius.circular(22),
    ),
    child: Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Icon(Icons.auto_awesome, color: AppColors.accent, size: 26),
        SizedBox(width: 12),
        Expanded(
          child: Text(
            AppLocalizations.of(context).t(
              'Ton algorithme apprend avec tes swipes. Ajoute, retire ou verrouille une préférence pour garder le contrôle.',
            ),
            style: TextStyle(
              color: Colors.white,
              height: 1.4,
              fontWeight: FontWeight.w600,
            ),
          ),
        ),
      ],
    ),
  );
}

class _EmptyAlgorithm extends StatelessWidget {
  const _EmptyAlgorithm();

  @override
  Widget build(BuildContext context) => Padding(
    padding: EdgeInsets.symmetric(vertical: 34),
    child: Column(
      children: [
        Icon(
          Icons.auto_awesome_outlined,
          size: 48,
          color: AppColors.textSecondary,
        ),
        SizedBox(height: 12),
        Text(
          AppLocalizations.of(context).t('Ton algorithme se construit'),
          style: const TextStyle(fontWeight: FontWeight.w900, fontSize: 17),
        ),
        SizedBox(height: 7),
        Text(
          AppLocalizations.of(
            context,
          ).t('Commence à swiper ou ajoute une préférence manuellement.'),
          textAlign: TextAlign.center,
          style: const TextStyle(color: AppColors.textSecondary, height: 1.4),
        ),
      ],
    ),
  );
}

class _PreferenceGroupConfig {
  const _PreferenceGroupConfig(this.title, this.matches);

  final String title;
  final bool Function(PreferenceItem item) matches;
}

final _groups = [
  _PreferenceGroupConfig(
    'Préférences apprises',
    (item) => item.source == 'learned',
  ),
  _PreferenceGroupConfig('Mes choix', (item) => item.source != 'learned'),
];

class _PreferenceGroup extends StatelessWidget {
  const _PreferenceGroup({
    required this.title,
    required this.items,
    required this.onRemove,
    required this.onToggleLock,
  });

  final String title;
  final List<PreferenceItem> items;
  final ValueChanged<PreferenceItem> onRemove;
  final ValueChanged<PreferenceItem> onToggleLock;

  @override
  Widget build(BuildContext context) {
    if (items.isEmpty) return const SizedBox.shrink();
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Padding(
          padding: const EdgeInsets.only(bottom: 8),
          child: Text(
            title.toUpperCase(),
            style: const TextStyle(
              color: AppColors.textSecondary,
              fontSize: 11,
              fontWeight: FontWeight.w900,
              letterSpacing: 1,
            ),
          ),
        ),
        ...items.map(
          (item) => Card(
            margin: const EdgeInsets.only(bottom: 8),
            child: ListTile(
              leading: CircleAvatar(
                backgroundColor:
                    item.locked ? AppColors.accent : AppColors.accentLight,
                child: Icon(
                  _iconFor(item.attribute),
                  color: AppColors.textPrimary,
                ),
              ),
              title: Text(
                _labelFor(item, AppLocalizations.of(context)),
                style: const TextStyle(fontWeight: FontWeight.w800),
              ),
              subtitle: Text(
                item.locked
                    ? AppLocalizations.of(
                      context,
                    ).t('Verrouillée dans ton feed')
                    : _sourceLabel(item.source, AppLocalizations.of(context)),
              ),
              trailing: PopupMenuButton<String>(
                onSelected: (action) {
                  if (action == 'lock') onToggleLock(item);
                  if (action == 'remove') onRemove(item);
                },
                itemBuilder:
                    (_) => [
                      PopupMenuItem(
                        value: 'lock',
                        child: Text(
                          item.locked
                              ? AppLocalizations.of(context).t('Déverrouiller')
                              : AppLocalizations.of(context).t('Verrouiller'),
                        ),
                      ),
                      PopupMenuItem(
                        value: 'remove',
                        child: Text(AppLocalizations.of(context).t('Retirer')),
                      ),
                    ],
              ),
            ),
          ),
        ),
        const SizedBox(height: 14),
      ],
    );
  }
}

String _labelFor(PreferenceItem item, AppLocalizations l) {
  final prefix = switch (item.attribute) {
    'liked_brands' => l.t('Marque aimée'),
    'rejected_brands' => l.t('Marque à éviter'),
    'color' => l.t('Couleur'),
    'category' => l.t('Catégorie'),
    'style' => l.t('Style'),
    'sizes' => l.t('Taille'),
    'max_price_eur' => l.t('Budget max'),
    _ => item.attribute,
  };
  return '$prefix · ${item.value}';
}

String _sourceLabel(String source, AppLocalizations l) =>
    source == 'learned'
        ? l.t('Apprise avec tes swipes')
        : l.t('Ajoutée par toi');

IconData _iconFor(String attribute) => switch (attribute) {
  'liked_brands' || 'rejected_brands' => Icons.sell_outlined,
  'color' => Icons.palette_outlined,
  'category' => Icons.category_outlined,
  'style' => Icons.auto_awesome_outlined,
  'sizes' => Icons.straighten_outlined,
  _ => Icons.tune,
};

class _PreferenceDraft {
  const _PreferenceDraft(this.attribute, this.value);
  final String attribute;
  final String value;
}

Future<_PreferenceDraft?> _showPreferenceEditor(BuildContext context) async {
  final l = AppLocalizations.of(context);
  final valueController = TextEditingController();
  var attribute = 'style';
  final result = await showModalBottomSheet<_PreferenceDraft>(
    context: context,
    isScrollControlled: true,
    showDragHandle: true,
    builder:
        (context) => StatefulBuilder(
          builder:
              (context, setModalState) => Padding(
                padding: EdgeInsets.fromLTRB(
                  24,
                  6,
                  24,
                  MediaQuery.viewInsetsOf(context).bottom + 24,
                ),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      l.t('Ajouter une préférence'),
                      style: Theme.of(context).textTheme.headlineSmall
                          ?.copyWith(fontWeight: FontWeight.w900),
                    ),
                    const SizedBox(height: 16),
                    DropdownButtonFormField<String>(
                      value: attribute,
                      decoration: InputDecoration(labelText: l.t('Type')),
                      items: [
                        DropdownMenuItem(
                          value: 'style',
                          child: Text(l.t('Style préféré')),
                        ),
                        DropdownMenuItem(
                          value: 'color',
                          child: Text(l.t('Couleur préférée')),
                        ),
                        DropdownMenuItem(
                          value: 'category',
                          child: Text(l.t('Catégorie préférée')),
                        ),
                        DropdownMenuItem(
                          value: 'liked_brands',
                          child: Text(l.t('Marque aimée')),
                        ),
                        DropdownMenuItem(
                          value: 'rejected_brands',
                          child: Text(l.t('Marque à éviter')),
                        ),
                      ],
                      onChanged: (next) {
                        if (next != null) setModalState(() => attribute = next);
                      },
                    ),
                    const SizedBox(height: 12),
                    TextField(
                      controller: valueController,
                      autofocus: true,
                      decoration: InputDecoration(
                        labelText: l.t('Valeur'),
                        hintText: l.t('Ex. vintage, noir, Levi’s…'),
                      ),
                    ),
                    const SizedBox(height: 18),
                    SizedBox(
                      width: double.infinity,
                      child: FilledButton(
                        onPressed: () {
                          final value = valueController.text.trim();
                          if (value.isEmpty) return;
                          Navigator.pop(
                            context,
                            _PreferenceDraft(attribute, value),
                          );
                        },
                        child: Text(l.t('Ajouter')),
                      ),
                    ),
                  ],
                ),
              ),
        ),
  );
  // `showModalBottomSheet` completes as soon as the pop starts, while the
  // reverse animation can still rebuild the TextField. Dispose afterwards so
  // the animation never reads a controller that is already disposed.
  await Future<void>.delayed(const Duration(milliseconds: 500));
  valueController.dispose();
  return result;
}
