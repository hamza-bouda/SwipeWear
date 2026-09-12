import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter/services.dart';

import '../../../core/theme/app_theme.dart';
import '../../../core/localization/app_localizations.dart';
import '../../feed/presentation/feed_screen.dart';
import '../../alerts/presentation/alerts_screen.dart';
import '../../alerts/providers.dart';
import '../../dressing/presentation/dressing_screen.dart';
import '../../drop/presentation/drop_screen.dart';
import '../../profile/presentation/profile_screen.dart';

class AppShell extends ConsumerStatefulWidget {
  const AppShell({super.key});

  @override
  ConsumerState<AppShell> createState() => _AppShellState();
}

class _AppShellState extends ConsumerState<AppShell> {
  int _selectedIndex = 0;

  List<NavigationDestination> _destinations(
    int activeAlerts,
    AppLocalizations l,
  ) => [
    NavigationDestination(
      icon: Icon(Icons.swipe_outlined),
      selectedIcon: Icon(Icons.swipe),
      label: l.t('Swipe'),
    ),
    NavigationDestination(
      icon: Icon(Icons.local_fire_department_outlined),
      selectedIcon: Icon(Icons.local_fire_department),
      label: l.t('Drop'),
    ),
    NavigationDestination(
      icon: _AlertBadge(count: activeAlerts, icon: Icons.notifications_none),
      selectedIcon: _AlertBadge(count: activeAlerts, icon: Icons.notifications),
      label: l.t('Alertes'),
    ),
    NavigationDestination(
      icon: Icon(Icons.checkroom_outlined),
      selectedIcon: Icon(Icons.checkroom),
      label: l.t('Dressing'),
    ),
    NavigationDestination(
      icon: Icon(Icons.person_outline),
      selectedIcon: Icon(Icons.person),
      label: l.t('Profil'),
    ),
  ];

  @override
  Widget build(BuildContext context) {
    final activeAlerts =
        ref.watch(alertsProvider).valueOrNull?.activeCount ?? 0;
    final l = AppLocalizations.of(context);
    return AnnotatedRegion<SystemUiOverlayStyle>(
      value: const SystemUiOverlayStyle(
        statusBarColor: Colors.transparent,
        statusBarIconBrightness: Brightness.dark,
        systemNavigationBarColor: AppColors.background,
        systemNavigationBarIconBrightness: Brightness.dark,
        systemNavigationBarDividerColor: AppColors.background,
      ),
      child: Scaffold(
        backgroundColor: AppColors.background,
        body: DecoratedBox(
          decoration: const BoxDecoration(gradient: AppGradients.background),
          child: IndexedStack(
            index: _selectedIndex,
            children: [
              FeedScreen(
                onOpenAlerts: () => setState(() => _selectedIndex = 2),
              ),
              const DropScreen(),
              const AlertsScreen(),
              const DressingScreen(),
              const ProfileScreen(),
            ],
          ),
        ),
        bottomNavigationBar: SafeArea(
          top: false,
          child: Padding(
            padding: const EdgeInsets.fromLTRB(16, 2, 16, 10),
            child: DecoratedBox(
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(26),
                border: Border.all(color: AppColors.border),
                boxShadow: const [
                  BoxShadow(
                    color: Color(0x14000000),
                    blurRadius: 18,
                    offset: Offset(0, 6),
                  ),
                ],
              ),
              child: NavigationBar(
                selectedIndex: _selectedIndex,
                destinations: _destinations(activeAlerts, l),
                onDestinationSelected: (index) {
                  setState(() => _selectedIndex = index);
                },
              ),
            ),
          ),
        ),
      ),
    );
  }
}

class _AlertBadge extends StatelessWidget {
  const _AlertBadge({required this.count, required this.icon});

  final int count;
  final IconData icon;

  @override
  Widget build(BuildContext context) => Badge(
    isLabelVisible: count > 0,
    label: Text(count > 9 ? '9+' : '$count'),
    child: Icon(icon),
  );
}
