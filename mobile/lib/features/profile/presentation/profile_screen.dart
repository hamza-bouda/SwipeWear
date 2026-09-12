import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/theme/app_theme.dart';
import '../../../core/localization/app_localizations.dart';
import '../../auth/presentation/login_screen.dart';
import '../../auth/providers.dart';
import '../../billing/presentation/paywall_screen.dart';
import '../../billing/providers.dart';
import '../../onboarding/data/style_archetypes.dart';
import 'algorithm_screen.dart';
import '../providers.dart';
import '../providers_extra.dart';

class ProfileScreen extends ConsumerWidget {
  const ProfileScreen({super.key});

  Future<void> _editSizes(BuildContext context, WidgetRef ref) async {
    final l = AppLocalizations.of(context);
    final profile = ref.read(profileProvider).valueOrNull;
    if (profile == null) return;
    final selected = {...profile.sizes};
    final options = {...availableSizes}.toList();
    final result = await showModalBottomSheet<List<String>>(
      context: context,
      showDragHandle: true,
      builder:
          (context) => StatefulBuilder(
            builder:
                (context, setModalState) => Padding(
                  padding: const EdgeInsets.fromLTRB(24, 4, 24, 28),
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        l.t('Tes tailles'),
                        style: Theme.of(context).textTheme.headlineSmall
                            ?.copyWith(fontWeight: FontWeight.w900),
                      ),
                      const SizedBox(height: 12),
                      Wrap(
                        spacing: 8,
                        runSpacing: 8,
                        children:
                            options
                                .map(
                                  (size) => ChoiceChip(
                                    label: Text(size),
                                    selected: selected.contains(size),
                                    onSelected:
                                        (_) => setModalState(() {
                                          if (!selected.add(size)) {
                                            selected.remove(size);
                                          }
                                        }),
                                  ),
                                )
                                .toList(),
                      ),
                      const SizedBox(height: 20),
                      FilledButton(
                        onPressed:
                            () => Navigator.pop(context, selected.toList()),
                        child: Text(l.t('Enregistrer')),
                      ),
                    ],
                  ),
                ),
          ),
    );
    if (result == null || !context.mounted) return;
    final session = await ref.read(sessionProvider.future);
    await ref.read(profileRepositoryProvider).patch(session, sizes: result);
    ref.invalidate(profileProvider);
  }

  Future<void> _editBudget(BuildContext context, WidgetRef ref) async {
    final l = AppLocalizations.of(context);
    final profile = ref.read(profileProvider).valueOrNull;
    if (profile == null) return;
    var budget = profile.maxPrice ?? 120;
    final result = await showModalBottomSheet<double>(
      context: context,
      showDragHandle: true,
      builder:
          (context) => StatefulBuilder(
            builder:
                (context, setModalState) => Padding(
                  padding: const EdgeInsets.fromLTRB(24, 4, 24, 28),
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        l.t('Budget maximum'),
                        style: Theme.of(context).textTheme.headlineSmall
                            ?.copyWith(fontWeight: FontWeight.w900),
                      ),
                      const SizedBox(height: 8),
                      Text(
                        budget >= 250 ? l.t('Sans limite') : l.price(budget),
                        style: const TextStyle(
                          fontSize: 24,
                          fontWeight: FontWeight.w900,
                          color: AppColors.textPrimary,
                        ),
                      ),
                      Slider(
                        value: budget,
                        min: 20,
                        max: 250,
                        divisions: 23,
                        onChanged:
                            (value) => setModalState(() => budget = value),
                      ),
                      FilledButton(
                        onPressed: () => Navigator.pop(context, budget),
                        child: Text(l.t('Enregistrer')),
                      ),
                    ],
                  ),
                ),
          ),
    );
    if (result == null || !context.mounted) return;
    final session = await ref.read(sessionProvider.future);
    await ref
        .read(profileRepositoryProvider)
        .patch(
          session,
          maxPrice: result >= 250 ? null : result,
          clearMaxPrice: result >= 250,
        );
    ref.invalidate(profileProvider);
  }

  Future<void> _setNotificationPreference(
    BuildContext context,
    WidgetRef ref,
    String value,
  ) async {
    final session = await ref.read(sessionProvider.future);
    await ref
        .read(notificationRepositoryProvider)
        .setPreference(session, value);
    ref.invalidate(notificationPreferenceProvider);
    if (context.mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            AppLocalizations.of(
              context,
            ).t('Préférence de notification enregistrée.'),
          ),
        ),
      );
    }
  }

  Future<void> _deleteAccount(BuildContext context, WidgetRef ref) async {
    final l = AppLocalizations.of(context);
    final confirmed = await showDialog<bool>(
      context: context,
      builder:
          (context) => AlertDialog(
            title: Text(l.t('Supprimer le compte ?')),
            content: Text(
              l.t(
                'Ton compte, ton profil et tes événements seront supprimés définitivement.',
              ),
            ),
            actions: [
              TextButton(
                onPressed: () => Navigator.pop(context, false),
                child: Text(l.t('Annuler')),
              ),
              FilledButton(
                onPressed: () => Navigator.pop(context, true),
                child: Text(l.t('Supprimer')),
              ),
            ],
          ),
    );
    if (confirmed != true || !context.mounted) return;
    final session = await ref.read(sessionProvider.future);
    try {
      await ref.read(authRepositoryProvider).deleteAccount(session);
      // AuthRepository.clear also removes all account-scoped offline data.
      ref.invalidate(sessionProvider);
      ref.invalidate(onboardingCompleteProvider);
    } catch (_) {
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(l.t('Suppression impossible pour le moment.')),
          ),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l = AppLocalizations.of(context);
    final profile = ref.watch(profileProvider);
    final billing = ref.watch(billingProvider);
    final session = ref.watch(sessionProvider).valueOrNull;
    final notification = ref.watch(notificationPreferenceProvider);
    return Scaffold(
      backgroundColor: Colors.transparent,
      body: SafeArea(
        child: profile.when(
          loading:
              () => const Center(
                child: CircularProgressIndicator(color: AppColors.accent),
              ),
          error:
              (_, __) => Center(
                child: TextButton(
                  onPressed: () => ref.invalidate(profileProvider),
                  child: Text(l.t('Charger mon profil')),
                ),
              ),
          data:
              (value) => RefreshIndicator(
                onRefresh: () async {
                  ref.invalidate(profileProvider);
                  await ref.read(profileProvider.future);
                },
                child: ListView(
                  padding: const EdgeInsets.fromLTRB(24, 20, 24, 120),
                  children: [
                    Text(
                      l.t('Mon espace'),
                      style: Theme.of(context).textTheme.headlineMedium
                          ?.copyWith(fontWeight: FontWeight.w900),
                    ),
                    const SizedBox(height: 6),
                    Text(
                      session?.email ?? l.t('Session anonyme'),
                      style: const TextStyle(color: AppColors.textSecondary),
                    ),
                    const SizedBox(height: 18),
                    Row(
                      children: [
                        Container(
                          width: 58,
                          height: 58,
                          decoration: BoxDecoration(
                            color: AppColors.accent,
                            borderRadius: BorderRadius.circular(20),
                          ),
                          child: const Icon(Icons.person, size: 30),
                        ),
                        const SizedBox(width: 14),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                session?.email?.split('@').first ??
                                    l.t('Chineuse SwipeWear'),
                                style: const TextStyle(
                                  fontWeight: FontWeight.w900,
                                  fontSize: 17,
                                ),
                              ),
                              const SizedBox(height: 3),
                              Text(
                                l.t(
                                  'Toujours à la recherche de belles pièces.',
                                ),
                                style: const TextStyle(
                                  color: AppColors.textSecondary,
                                  fontSize: 12,
                                ),
                              ),
                            ],
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 16),
                    Container(
                      padding: const EdgeInsets.symmetric(vertical: 14),
                      decoration: BoxDecoration(
                        color: Colors.white,
                        borderRadius: BorderRadius.circular(18),
                        border: Border.all(color: AppColors.border),
                      ),
                      child: Row(
                        mainAxisAlignment: MainAxisAlignment.spaceAround,
                        children: [
                          _ProfileStat(
                            value.eventCount.toString(),
                            l.t('swipes'),
                          ),
                          _ProfileStat(
                            value.likedBrands.length.toString(),
                            l.t('marques aimées'),
                          ),
                          _ProfileStat(
                            value.sizes.length.toString(),
                            l.t('tailles'),
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(height: 22),
                    billing.when(
                      data:
                          (status) => _GoldCard(
                            active: status.isPremium,
                            onTap:
                                () => Navigator.push(
                                  context,
                                  MaterialPageRoute(
                                    builder:
                                        (_) => const PaywallScreen(
                                          trigger: 'profile',
                                        ),
                                  ),
                                ),
                          ),
                      loading: () => const LinearProgressIndicator(),
                      error:
                          (_, __) => _GoldCard(
                            active: false,
                            onTap:
                                () => Navigator.push(
                                  context,
                                  MaterialPageRoute(
                                    builder:
                                        (_) => const PaywallScreen(
                                          trigger: 'profile',
                                        ),
                                  ),
                                ),
                          ),
                    ),
                    const SizedBox(height: 24),
                    Text(
                      l.t('TON ALGORITHME'),
                      style: const TextStyle(
                        color: AppColors.textSecondary,
                        fontWeight: FontWeight.w900,
                        fontSize: 11,
                        letterSpacing: 1,
                      ),
                    ),
                    const SizedBox(height: 10),
                    _ActionTile(
                      icon: Icons.auto_awesome,
                      title: l.t('Voir mon algorithme'),
                      subtitle: l.t('Préférences apprises, choix et verrous'),
                      onTap:
                          () => Navigator.push(
                            context,
                            MaterialPageRoute(
                              builder: (_) => const AlgorithmScreen(),
                            ),
                          ),
                    ),
                    _SettingTile(
                      icon: Icons.wc_outlined,
                      title: l.t('Je cherche des pièces'),
                      value: l.gender(value.gender),
                      onTap: () => _chooseGender(context, ref, value.gender),
                    ),
                    _SettingTile(
                      icon: Icons.straighten_outlined,
                      title: l.t('Mes tailles'),
                      value:
                          value.sizes.isEmpty
                              ? l.t('À renseigner')
                              : value.sizes.join(' · '),
                      onTap: () => _editSizes(context, ref),
                    ),
                    _SettingTile(
                      icon: Icons.euro_outlined,
                      title: l.t('Budget maximum'),
                      value: l.maxPrice(value.maxPrice),
                      onTap: () => _editBudget(context, ref),
                    ),
                    _SettingTile(
                      icon: Icons.language,
                      title: l.t('Langue'),
                      value: l.isEnglish ? l.t('Anglais') : l.t('Français'),
                      onTap: () => _chooseLanguage(context, ref),
                    ),
                    if (value.lockedAttributes.isNotEmpty)
                      Padding(
                        padding: const EdgeInsets.only(top: 8),
                        child: Wrap(
                          spacing: 8,
                          runSpacing: 8,
                          children:
                              value.lockedAttributes
                                  .where((item) => item.value.isNotEmpty)
                                  .map(
                                    (item) => Chip(
                                      avatar: Icon(
                                        item.locked
                                            ? Icons.lock_outline
                                            : Icons.auto_awesome,
                                        size: 14,
                                      ),
                                      label: Text(item.value),
                                    ),
                                  )
                                  .toList(),
                        ),
                      ),
                    const SizedBox(height: 24),
                    Text(
                      l.t('NOTIFICATIONS'),
                      style: const TextStyle(
                        color: AppColors.textSecondary,
                        fontWeight: FontWeight.w900,
                        fontSize: 11,
                        letterSpacing: 1,
                      ),
                    ),
                    const SizedBox(height: 10),
                    Card(
                      child: Padding(
                        padding: const EdgeInsets.fromLTRB(14, 6, 14, 6),
                        child: notification.when(
                          data:
                              (pref) => DropdownButtonFormField<String>(
                                value: pref,
                                decoration: InputDecoration(
                                  labelText: l.t('Fréquence des alertes'),
                                  border: InputBorder.none,
                                ),
                                items: [
                                  DropdownMenuItem(
                                    value: 'instant',
                                    child: Text(l.t('Instantanée · Gold')),
                                  ),
                                  DropdownMenuItem(
                                    value: 'daily_digest',
                                    child: Text(l.t('Résumé quotidien')),
                                  ),
                                  DropdownMenuItem(
                                    value: 'disabled',
                                    child: Text(l.t('Désactivées')),
                                  ),
                                ],
                                onChanged: (value) {
                                  if (value != null) {
                                    _setNotificationPreference(
                                      context,
                                      ref,
                                      value,
                                    );
                                  }
                                },
                              ),
                          loading:
                              () => const Padding(
                                padding: EdgeInsets.all(12),
                                child: LinearProgressIndicator(),
                              ),
                          error:
                              (_, __) => Text(l.t('Préférences indisponibles')),
                        ),
                      ),
                    ),
                    const SizedBox(height: 24),
                    Text(
                      l.t('COMPTE'),
                      style: const TextStyle(
                        color: AppColors.textSecondary,
                        fontWeight: FontWeight.w900,
                        fontSize: 11,
                        letterSpacing: 1,
                      ),
                    ),
                    const SizedBox(height: 10),
                    if (session?.isAuthenticated != true)
                      _ActionTile(
                        icon: Icons.login,
                        title: l.t('Créer un compte ou se connecter'),
                        onTap:
                            () => Navigator.push(
                              context,
                              MaterialPageRoute(
                                builder: (_) => const LoginScreen(),
                              ),
                            ),
                      ),
                    _ActionTile(
                      icon: Icons.restart_alt,
                      title: l.t('Recalibrer mon style'),
                      onTap: () async {
                        await ref.read(sessionStoreProvider).clearOnboarding();
                        ref.invalidate(onboardingCompleteProvider);
                      },
                    ),
                    _ActionTile(
                      icon: Icons.delete_outline,
                      title: l.t('Supprimer mon compte'),
                      danger: true,
                      onTap: () => _deleteAccount(context, ref),
                    ),
                    const SizedBox(height: 12),
                    Center(
                      child: Text(
                        l.t('SwipeWear · L’IA qui chine pour toi 24 h/24'),
                        style: const TextStyle(
                          color: AppColors.textSecondary,
                          fontSize: 11,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
        ),
      ),
    );
  }

  Future<void> _chooseGender(
    BuildContext context,
    WidgetRef ref,
    String? current,
  ) async {
    final l = AppLocalizations.of(context);
    final value = await showModalBottomSheet<String>(
      context: context,
      showDragHandle: true,
      builder:
          (context) => Column(
            mainAxisSize: MainAxisSize.min,
            children:
                ['women', 'men', 'unisex']
                    .map(
                      (value) => ListTile(
                        title: Text(l.gender(value)),
                        trailing:
                            current == value
                                ? const Icon(
                                  Icons.check,
                                  color: AppColors.success,
                                )
                                : null,
                        onTap: () => Navigator.pop(context, value),
                      ),
                    )
                    .toList(),
          ),
    );
    if (value == null || !context.mounted) return;
    final session = await ref.read(sessionProvider.future);
    await ref.read(profileRepositoryProvider).patch(session, gender: value);
    ref.invalidate(profileProvider);
  }

  Future<void> _chooseLanguage(BuildContext context, WidgetRef ref) async {
    final l = AppLocalizations.of(context);
    final selected = await showModalBottomSheet<String>(
      context: context,
      showDragHandle: true,
      builder:
          (context) => Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Padding(
                padding: const EdgeInsets.fromLTRB(24, 4, 24, 12),
                child: Align(
                  alignment: Alignment.centerLeft,
                  child: Text(
                    l.t('Choisir la langue'),
                    style: Theme.of(context).textTheme.titleLarge?.copyWith(
                      fontWeight: FontWeight.w900,
                    ),
                  ),
                ),
              ),
              ListTile(
                title: Text(l.t('Français')),
                trailing:
                    !l.isEnglish
                        ? const Icon(Icons.check, color: AppColors.success)
                        : null,
                onTap: () => Navigator.pop(context, 'fr'),
              ),
              ListTile(
                title: Text(l.t('Anglais')),
                trailing:
                    l.isEnglish
                        ? const Icon(Icons.check, color: AppColors.success)
                        : null,
                onTap: () => Navigator.pop(context, 'en'),
              ),
              const SizedBox(height: 18),
            ],
          ),
    );
    if (selected == null || !context.mounted) return;
    await ref.read(localeControllerProvider).setLocale(selected);
    if (context.mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(AppLocalizations.of(context).t('Langue mise à jour.')),
        ),
      );
    }
  }
}

class _GoldCard extends StatelessWidget {
  const _GoldCard({required this.active, required this.onTap});
  final bool active;
  final VoidCallback onTap;
  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(22),
      child: Ink(
        decoration: BoxDecoration(
          gradient: AppGradients.gold,
          borderRadius: BorderRadius.circular(22),
        ),
        padding: const EdgeInsets.all(18),
        child: Row(
          children: [
            const Icon(
              Icons.workspace_premium_rounded,
              color: AppColors.textPrimary,
              size: 28,
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    active ? l.t('SwipeWear Gold actif') : l.t('Passe en Gold'),
                    style: const TextStyle(
                      color: AppColors.textPrimary,
                      fontWeight: FontWeight.w900,
                      fontSize: 17,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    active
                        ? l.t('Tes alertes sont prioritaires.')
                        : l.t('Alertes illimitées et instantanées.'),
                    style: const TextStyle(
                      color: AppColors.textPrimary,
                      fontSize: 12,
                    ),
                  ),
                ],
              ),
            ),
            const Icon(Icons.chevron_right, color: AppColors.textPrimary),
          ],
        ),
      ),
    );
  }
}

class _ProfileStat extends StatelessWidget {
  const _ProfileStat(this.value, this.label);

  final String value;
  final String label;

  @override
  Widget build(BuildContext context) => Column(
    children: [
      Text(
        value,
        style: const TextStyle(fontWeight: FontWeight.w900, fontSize: 18),
      ),
      const SizedBox(height: 2),
      Text(
        label,
        style: const TextStyle(color: AppColors.textSecondary, fontSize: 10),
      ),
    ],
  );
}

class _SettingTile extends StatelessWidget {
  const _SettingTile({
    required this.icon,
    required this.title,
    required this.value,
    required this.onTap,
  });
  final IconData icon;
  final String title;
  final String value;
  final VoidCallback onTap;
  @override
  Widget build(BuildContext context) => Card(
    margin: const EdgeInsets.only(bottom: 8),
    child: ListTile(
      leading: Icon(icon),
      title: Text(title, style: const TextStyle(fontWeight: FontWeight.w700)),
      subtitle: Text(value),
      trailing: const Icon(Icons.chevron_right),
      onTap: onTap,
    ),
  );
}

class _ActionTile extends StatelessWidget {
  const _ActionTile({
    required this.icon,
    required this.title,
    required this.onTap,
    this.subtitle,
    this.danger = false,
  });
  final IconData icon;
  final String title;
  final String? subtitle;
  final VoidCallback onTap;
  final bool danger;
  @override
  Widget build(BuildContext context) => ListTile(
    contentPadding: EdgeInsets.zero,
    leading: Icon(
      icon,
      color: danger ? AppColors.error : AppColors.textPrimary,
    ),
    title: Text(
      title,
      style: TextStyle(
        color: danger ? AppColors.error : AppColors.textPrimary,
        fontWeight: FontWeight.w700,
      ),
    ),
    subtitle: subtitle == null ? null : Text(subtitle!),
    onTap: onTap,
  );
}
