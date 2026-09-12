import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:image_picker/image_picker.dart';

import '../../../core/localization/app_localizations.dart';
import '../../../core/theme/app_theme.dart';
import '../../auth/providers.dart';
import '../data/style_archetypes.dart';
import '../providers.dart';

class OnboardingFlow extends ConsumerStatefulWidget {
  const OnboardingFlow({super.key});

  @override
  ConsumerState<OnboardingFlow> createState() => _OnboardingFlowState();
}

class _OnboardingFlowState extends ConsumerState<OnboardingFlow> {
  final _pageController = PageController();
  final _selectedStyles = <String>{};
  final _selectedSizes = <String>{};
  final _picker = ImagePicker();
  String _gender = 'unisex';
  double _budget = 120;
  List<String> _inspirationPaths = const [];
  int _page = 0;
  bool _saving = false;
  String? _error;

  Future<void> _next() async {
    if (_page == 0) {
      _advance();
      return;
    }
    if (_page == 1 && _selectedStyles.isEmpty && _inspirationPaths.isEmpty) {
      setState(
        () =>
            _error = AppLocalizations.of(
              context,
            ).t('Choisis au moins un univers ou ajoute une inspiration.'),
      );
      return;
    }
    if (_page < 2) {
      _advance();
      return;
    }
    await _finish();
  }

  void _advance() {
    setState(() => _error = null);
    _pageController.nextPage(
      duration: const Duration(milliseconds: 280),
      curve: Curves.easeOutCubic,
    );
    setState(() => _page++);
  }

  Future<void> _toggleStyle(String id) async {
    if (!_selectedStyles.contains(id) && _inspirationPaths.isNotEmpty) {
      final replace = await _confirmChoiceReplacement(
        title: AppLocalizations.of(context).t('Remplacer tes inspirations ?'),
        message: AppLocalizations.of(context).t(
          'Le parcours par styles remplacera les inspirations importées pour garder un profil clair.',
        ),
      );
      if (!replace || !mounted) return;
      setState(() => _inspirationPaths = const []);
    }
    setState(() {
      if (!_selectedStyles.add(id)) _selectedStyles.remove(id);
      _error = null;
    });
  }

  Future<void> _pickInspirations() async {
    final images = await _picker.pickMultiImage(imageQuality: 85, limit: 10);
    if (!mounted || images.isEmpty) return;
    if (_selectedStyles.isNotEmpty) {
      final replace = await _confirmChoiceReplacement(
        title: AppLocalizations.of(context).t('Remplacer tes styles ?'),
        message: AppLocalizations.of(context).t(
          'Le parcours par inspirations remplacera les styles sélectionnés pour laisser l’IA analyser tes images.',
        ),
      );
      if (!replace || !mounted) return;
    }
    setState(() {
      _selectedStyles.clear();
      _inspirationPaths = images.map((image) => image.path).toList();
      _error = null;
    });
  }

  Future<bool> _confirmChoiceReplacement({
    required String title,
    required String message,
  }) async {
    final result = await showDialog<bool>(
      context: context,
      builder:
          (context) => AlertDialog(
            title: Text(title),
            content: Text(message),
            actions: [
              TextButton(
                onPressed: () => Navigator.pop(context, false),
                child: Text(AppLocalizations.of(context).t('Annuler')),
              ),
              FilledButton(
                onPressed: () => Navigator.pop(context, true),
                child: Text(AppLocalizations.of(context).t('Continuer')),
              ),
            ],
          ),
    );
    return result ?? false;
  }

  Future<void> _finish() async {
    if (_selectedSizes.isEmpty) {
      setState(
        () =>
            _error = AppLocalizations.of(context).t(
              'Sélectionne au moins une taille pour recevoir des pièces pertinentes.',
            ),
      );
      return;
    }
    setState(() {
      _saving = true;
      _error = null;
    });
    try {
      final session = await ref.read(sessionProvider.future);
      final repository = ref.read(onboardingRepositoryProvider);
      await repository.submitStyles(
        session,
        styleIds: _selectedStyles.toList(),
        sizes: _selectedSizes.toList(),
        maxPrice: _budget >= 250 ? null : _budget,
        gender: _gender,
      );
      if (_inspirationPaths.isNotEmpty) {
        await repository.uploadInspirations(session, _inspirationPaths);
      }
      await ref.read(sessionStoreProvider).setOnboardingComplete(true);
      ref.invalidate(onboardingCompleteProvider);
    } catch (error) {
      if (!mounted) return;
      setState(() {
        _saving = false;
        _error = AppLocalizations.of(
          context,
        ).t('Impossible de sauvegarder tes préférences. Réessaie.');
      });
    }
  }

  Future<void> _skip() async {
    await ref.read(sessionStoreProvider).setOnboardingComplete(true);
    ref.invalidate(onboardingCompleteProvider);
  }

  @override
  void dispose() {
    _pageController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final l = AppLocalizations.of(context);
    return Scaffold(
      body: DecoratedBox(
        decoration: const BoxDecoration(gradient: AppGradients.background),
        child: SafeArea(
          child: Column(
            children: [
              Padding(
                padding: const EdgeInsets.fromLTRB(24, 20, 24, 12),
                child: Row(
                  children: [
                    if (_page > 0)
                      IconButton(
                        onPressed:
                            _saving
                                ? null
                                : () {
                                  _pageController.previousPage(
                                    duration: const Duration(milliseconds: 220),
                                    curve: Curves.easeOut,
                                  );
                                  setState(() => _page--);
                                },
                        icon: const Icon(Icons.arrow_back),
                      )
                    else
                      const SizedBox(width: 48),
                    Expanded(
                      child: LinearProgressIndicator(
                        value: (_page + 1) / 3,
                        minHeight: 6,
                        borderRadius: BorderRadius.circular(99),
                        color: AppColors.accent,
                        backgroundColor: AppColors.accentLight,
                      ),
                    ),
                    TextButton(
                      onPressed: _saving ? null : _skip,
                      child: Text(l.t('Passer')),
                    ),
                  ],
                ),
              ),
              Expanded(
                child: PageView(
                  controller: _pageController,
                  physics: const NeverScrollableScrollPhysics(),
                  children: [
                    _WelcomePage(
                      theme: theme,
                      gender: _gender,
                      onGenderChanged:
                          (value) => setState(() => _gender = value),
                    ),
                    _StylePage(
                      selected: _selectedStyles,
                      onToggle: (id) => _toggleStyle(id),
                      onPickInspirations: _pickInspirations,
                      inspirationCount: _inspirationPaths.length,
                    ),
                    _ConstraintsPage(
                      selectedSizes: _selectedSizes,
                      budget: _budget,
                      onToggleSize:
                          (size) => setState(() {
                            if (!_selectedSizes.add(size)) {
                              _selectedSizes.remove(size);
                            }
                            _error = null;
                          }),
                      onBudgetChanged:
                          (value) => setState(() => _budget = value),
                    ),
                  ],
                ),
              ),
              if (_error != null)
                Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 24),
                  child: Text(
                    _error!,
                    style: const TextStyle(color: AppColors.error),
                    textAlign: TextAlign.center,
                  ),
                ),
              Padding(
                padding: const EdgeInsets.fromLTRB(24, 12, 24, 24),
                child: FilledButton(
                  onPressed: _saving ? null : _next,
                  child:
                      _saving
                          ? const SizedBox(
                            width: 20,
                            height: 20,
                            child: CircularProgressIndicator(strokeWidth: 2),
                          )
                          : Text(
                            _page == 2
                                ? l.t('Découvrir mon feed')
                                : l.t('Continuer'),
                          ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _WelcomePage extends StatelessWidget {
  const _WelcomePage({
    required this.theme,
    required this.gender,
    required this.onGenderChanged,
  });

  final ThemeData theme;
  final String gender;
  final ValueChanged<String> onGenderChanged;

  @override
  Widget build(BuildContext context) => Padding(
    padding: const EdgeInsets.fromLTRB(24, 28, 24, 12),
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'SwipeWear',
              style: TextStyle(
                fontSize: 28,
                fontWeight: FontWeight.w900,
                letterSpacing: -1.4,
              ),
            ),
            Text(
              AppLocalizations.of(context).t('Ton style, à ta façon.'),
              style: const TextStyle(
                color: AppColors.textSecondary,
                fontSize: 11,
                fontWeight: FontWeight.w700,
              ),
            ),
          ],
        ),
        const Spacer(),
        Text(
          AppLocalizations.of(context).t('Ton style.\nTa prochaine pépite.'),
          style: theme.textTheme.displaySmall?.copyWith(
            fontWeight: FontWeight.w900,
            height: 1.05,
          ),
        ),
        const SizedBox(height: 16),
        Text(
          AppLocalizations.of(context).t(
            'SwipeWear apprend ce que tu aimes pour chiner plus vite, au meilleur prix.',
          ),
          style: theme.textTheme.bodyLarge?.copyWith(
            color: AppColors.textSecondary,
            height: 1.45,
          ),
        ),
        const SizedBox(height: 32),
        Text(
          AppLocalizations.of(context).t('Je cherche des pièces'),
          style: theme.textTheme.titleMedium?.copyWith(
            fontWeight: FontWeight.w800,
          ),
        ),
        const SizedBox(height: 12),
        Wrap(
          spacing: 10,
          runSpacing: 10,
          children: [
            _ChoiceChip(
              label: AppLocalizations.of(context).t('Femme'),
              selected: gender == 'women',
              onTap: () => onGenderChanged('women'),
            ),
            _ChoiceChip(
              label: AppLocalizations.of(context).t('Homme'),
              selected: gender == 'men',
              onTap: () => onGenderChanged('men'),
            ),
            _ChoiceChip(
              label: AppLocalizations.of(context).t('Tout me va'),
              selected: gender == 'unisex',
              onTap: () => onGenderChanged('unisex'),
            ),
          ],
        ),
        const Spacer(flex: 2),
      ],
    ),
  );
}

class _StylePage extends StatelessWidget {
  const _StylePage({
    required this.selected,
    required this.onToggle,
    required this.onPickInspirations,
    required this.inspirationCount,
  });

  final Set<String> selected;
  final Future<void> Function(String) onToggle;
  final Future<void> Function() onPickInspirations;
  final int inspirationCount;

  @override
  Widget build(BuildContext context) => Padding(
    padding: const EdgeInsets.fromLTRB(24, 16, 24, 0),
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          AppLocalizations.of(context).t('Quels styles te font vibrer ?'),
          style: Theme.of(
            context,
          ).textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.w900),
        ),
        const SizedBox(height: 6),
        Text(
          AppLocalizations.of(context).t(
            'Choisis les univers qui te ressemblent ou importe quelques inspirations. L’IA affinera ensuite tes recommandations.',
          ),
        ),
        const SizedBox(height: 18),
        Expanded(
          child: GridView.builder(
            itemCount: styleArchetypes.length,
            gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
              crossAxisCount: 2,
              crossAxisSpacing: 12,
              mainAxisSpacing: 12,
              childAspectRatio: .84,
            ),
            itemBuilder: (context, index) {
              final style = styleArchetypes[index];
              final isSelected = selected.contains(style.id);
              return InkWell(
                onTap: () => unawaited(onToggle(style.id)),
                borderRadius: BorderRadius.circular(20),
                child: Ink(
                  decoration: BoxDecoration(
                    borderRadius: BorderRadius.circular(20),
                    border: Border.all(
                      color: isSelected ? AppColors.accent : Colors.transparent,
                      width: 3,
                    ),
                    color: AppColors.surface,
                  ),
                  child: ClipRRect(
                    borderRadius: BorderRadius.circular(17),
                    child: Stack(
                      fit: StackFit.expand,
                      children: [
                        Image.network(
                          style.imageUrl,
                          fit: BoxFit.cover,
                          errorBuilder:
                              (_, __, ___) =>
                                  const ColoredBox(color: AppColors.surface),
                        ),
                        DecoratedBox(
                          decoration: BoxDecoration(
                            gradient: LinearGradient(
                              begin: Alignment.topCenter,
                              end: Alignment.bottomCenter,
                              colors: [
                                Colors.transparent,
                                Colors.black.withValues(alpha: .75),
                              ],
                            ),
                          ),
                        ),
                        Positioned(
                          left: 12,
                          right: 12,
                          bottom: 12,
                          child: Text(
                            style.label,
                            style: const TextStyle(
                              color: Colors.white,
                              fontWeight: FontWeight.w800,
                            ),
                          ),
                        ),
                        if (isSelected)
                          const Positioned(
                            top: 10,
                            right: 10,
                            child: CircleAvatar(
                              radius: 14,
                              backgroundColor: AppColors.accent,
                              child: Icon(
                                Icons.check,
                                size: 17,
                                color: AppColors.textPrimary,
                              ),
                            ),
                          ),
                      ],
                    ),
                  ),
                ),
              );
            },
          ),
        ),
        OutlinedButton.icon(
          onPressed: () => unawaited(onPickInspirations()),
          icon: const Icon(Icons.photo_library_outlined),
          label: Text(
            inspirationCount == 0
                ? AppLocalizations.of(context).t('Importer mes inspirations')
                : AppLocalizations.of(context).isEnglish
                ? '$inspirationCount inspiration(s) added'
                : '$inspirationCount inspiration(s) ajoutée(s)',
          ),
        ),
      ],
    ),
  );
}

class _ConstraintsPage extends StatelessWidget {
  const _ConstraintsPage({
    required this.selectedSizes,
    required this.budget,
    required this.onToggleSize,
    required this.onBudgetChanged,
  });

  final Set<String> selectedSizes;
  final double budget;
  final ValueChanged<String> onToggleSize;
  final ValueChanged<double> onBudgetChanged;

  @override
  Widget build(BuildContext context) => ListView(
    padding: const EdgeInsets.fromLTRB(24, 16, 24, 0),
    children: [
      Text(
        AppLocalizations.of(context).t('Les bons filtres, dès le départ'),
        style: Theme.of(
          context,
        ).textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.w900),
      ),
      const SizedBox(height: 6),
      Text(
        AppLocalizations.of(context).t(
          'Ta taille est un filtre dur : tu ne perdras pas de temps sur des pièces impossibles à porter.',
        ),
      ),
      const SizedBox(height: 26),
      Text(
        AppLocalizations.of(context).t('Tes tailles'),
        style: Theme.of(
          context,
        ).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w800),
      ),
      const SizedBox(height: 12),
      _SizeGroup(
        title: AppLocalizations.of(context).t('Hauts'),
        sizes: topSizes,
        selected: selectedSizes,
        onToggle: onToggleSize,
      ),
      const SizedBox(height: 18),
      _SizeGroup(
        title: AppLocalizations.of(context).t('Bas'),
        sizes: bottomSizes,
        selected: selectedSizes,
        onToggle: onToggleSize,
      ),
      const SizedBox(height: 18),
      _SizeGroup(
        title: AppLocalizations.of(context).t('Pointures'),
        sizes: shoeSizes,
        selected: selectedSizes,
        onToggle: onToggleSize,
      ),
      const SizedBox(height: 30),
      Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(
            AppLocalizations.of(context).t('Budget maximum'),
            style: Theme.of(
              context,
            ).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w800),
          ),
          Text(
            budget >= 250
                ? AppLocalizations.of(context).t('Sans limite')
                : AppLocalizations.of(context).price(budget),
            style: const TextStyle(
              fontWeight: FontWeight.w900,
              color: AppColors.textPrimary,
              fontSize: 18,
            ),
          ),
        ],
      ),
      Slider(
        value: budget,
        min: 20,
        max: 250,
        divisions: 23,
        onChanged: onBudgetChanged,
      ),
      const Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [Text('20 €'), Text('250 € +')],
      ),
    ],
  );
}

class _SizeGroup extends StatelessWidget {
  const _SizeGroup({
    required this.title,
    required this.sizes,
    required this.selected,
    required this.onToggle,
  });

  final String title;
  final List<String> sizes;
  final Set<String> selected;
  final ValueChanged<String> onToggle;

  @override
  Widget build(BuildContext context) => Column(
    crossAxisAlignment: CrossAxisAlignment.start,
    children: [
      Text(title, style: const TextStyle(fontWeight: FontWeight.w800)),
      const SizedBox(height: 8),
      Wrap(
        spacing: 8,
        runSpacing: 8,
        children:
            sizes
                .map(
                  (size) => _ChoiceChip(
                    label: size,
                    selected: selected.contains(size),
                    onTap: () => onToggle(size),
                  ),
                )
                .toList(),
      ),
    ],
  );
}

class _ChoiceChip extends StatelessWidget {
  const _ChoiceChip({
    required this.label,
    required this.selected,
    required this.onTap,
  });

  final String label;
  final bool selected;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) => ChoiceChip(
    label: Text(label),
    selected: selected,
    onSelected: (_) => onTap(),
  );
}
