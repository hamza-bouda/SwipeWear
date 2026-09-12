import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../features/auth/providers.dart';
import 'providers.dart';

class AnalyticsScreenView extends ConsumerStatefulWidget {
  const AnalyticsScreenView({
    super.key,
    required this.name,
    required this.child,
    this.properties = const {},
  });

  final String name;
  final Map<String, dynamic> properties;
  final Widget child;

  @override
  ConsumerState<AnalyticsScreenView> createState() =>
      _AnalyticsScreenViewState();
}

class _AnalyticsScreenViewState extends ConsumerState<AnalyticsScreenView> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) => _track());
  }

  Future<void> _track() async {
    try {
      final session = await ref.read(sessionProvider.future);
      await ref
          .read(analyticsServiceProvider)
          .track(session, widget.name, properties: widget.properties);
    } catch (_) {}
  }

  @override
  Widget build(BuildContext context) => widget.child;
}
