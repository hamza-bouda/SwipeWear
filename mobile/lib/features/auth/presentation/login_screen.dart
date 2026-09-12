import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/network/api_client.dart';
import '../../../core/localization/app_localizations.dart';
import '../../../core/theme/app_theme.dart';
import '../providers.dart';

class LoginScreen extends ConsumerStatefulWidget {
  const LoginScreen({super.key});
  @override
  ConsumerState<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends ConsumerState<LoginScreen> {
  final _email = TextEditingController();
  final _password = TextEditingController();
  bool _register = false;
  bool _busy = false;
  String? _error;

  Future<void> _submit() async {
    final email = _email.text.trim();
    final password = _password.text;
    if (!email.contains('@') || password.length < 8) {
      setState(
        () =>
            _error = AppLocalizations.of(context).t(
              'Indique un email valide et un mot de passe de 8 caractères minimum.',
            ),
      );
      return;
    }
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      final repo = ref.read(authRepositoryProvider);
      final current = await ref.read(sessionProvider.future);
      if (_register) {
        await repo.register(email, password, current);
      } else {
        await repo.login(email, password);
      }
      ref.invalidate(sessionProvider);
      if (mounted) Navigator.pop(context);
    } on ApiException catch (error) {
      if (mounted) {
        setState(() {
          _busy = false;
          _error = error.message;
        });
      }
    } catch (_) {
      if (mounted) {
        setState(() {
          _busy = false;
          _error = AppLocalizations.of(
            context,
          ).t('Connexion impossible. Vérifie ton réseau.');
        });
      }
    }
  }

  Future<void> _googleLogin() async {
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      final current = await ref.read(sessionProvider.future);
      final session = await ref
          .read(authRepositoryProvider)
          .loginWithGoogle(current);
      if (session == null) {
        if (mounted) setState(() => _busy = false);
        return;
      }
      ref.invalidate(sessionProvider);
      if (mounted) Navigator.pop(context);
    } on ApiException catch (error) {
      if (mounted) {
        setState(() {
          _busy = false;
          _error = error.message;
        });
      }
    } catch (error) {
      if (mounted) {
        setState(() {
          _busy = false;
          _error = AppLocalizations.of(context).t(
            'Connexion Google impossible. Vérifie la configuration de l’application.',
          );
        });
      }
    }
  }

  @override
  void dispose() {
    _email.dispose();
    _password.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    return Scaffold(
      appBar: AppBar(),
      body: ListView(
        padding: const EdgeInsets.fromLTRB(24, 18, 24, 32),
        children: [
          Container(
            width: 58,
            height: 58,
            decoration: BoxDecoration(
              color: AppColors.accent,
              borderRadius: BorderRadius.circular(20),
            ),
            child: const Center(
              child: Text(
                'SW',
                style: TextStyle(fontWeight: FontWeight.w900, fontSize: 20),
              ),
            ),
          ),
          const SizedBox(height: 24),
          Text(
            _register ? l.t('Créer mon compte') : l.t('Bon retour'),
            style: Theme.of(
              context,
            ).textTheme.headlineMedium?.copyWith(fontWeight: FontWeight.w900),
          ),
          const SizedBox(height: 8),
          Text(
            _register
                ? l.t(
                  'Retrouve ton style et tes alertes sur tous tes appareils.',
                )
                : l.t('Connecte-toi pour garder ton dressing et ton profil.'),
            style: const TextStyle(color: AppColors.textSecondary, height: 1.4),
          ),
          const SizedBox(height: 28),
          TextField(
            controller: _email,
            keyboardType: TextInputType.emailAddress,
            autofillHints: const [AutofillHints.email],
            decoration: InputDecoration(labelText: l.t('Email')),
          ),
          const SizedBox(height: 12),
          TextField(
            controller: _password,
            obscureText: true,
            autofillHints: const [AutofillHints.password],
            decoration: InputDecoration(
              labelText: l.t('Mot de passe'),
              helperText: _register ? l.t('8 caractères minimum') : null,
            ),
          ),
          if (_error != null)
            Padding(
              padding: const EdgeInsets.only(top: 12),
              child: Text(
                _error!,
                style: const TextStyle(color: AppColors.error),
              ),
            ),
          const SizedBox(height: 24),
          FilledButton(
            onPressed: _busy ? null : _submit,
            child:
                _busy
                    ? const SizedBox(
                      width: 20,
                      height: 20,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    )
                    : Text(
                      _register ? l.t('Créer mon compte') : l.t('Se connecter'),
                    ),
          ),
          const SizedBox(height: 18),
          Row(
            children: [
              const Expanded(child: Divider()),
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 12),
                child: Text(
                  l.t('ou'),
                  style: const TextStyle(color: AppColors.textSecondary),
                ),
              ),
              const Expanded(child: Divider()),
            ],
          ),
          const SizedBox(height: 18),
          OutlinedButton.icon(
            onPressed: _busy ? null : _googleLogin,
            icon: const Icon(Icons.g_mobiledata_rounded, size: 28),
            label: Text(l.t('Continuer avec Google')),
          ),
          const SizedBox(height: 12),
          TextButton(
            onPressed:
                _busy
                    ? null
                    : () => setState(() {
                      _register = !_register;
                      _error = null;
                    }),
            child: Text(
              _register ? l.t('J’ai déjà un compte') : l.t('Créer un compte'),
            ),
          ),
        ],
      ),
    );
  }
}
