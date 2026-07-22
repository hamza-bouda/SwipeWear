import React from 'react';
import { View, Text, StyleSheet, Alert } from 'react-native';
import { useNavigation, CommonActions } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { Button } from '../components';
import { useAuth } from '../context/AuthContext';
import { colors, typography, spacing } from '../theme';
import type { RootStackParamList } from '../navigation/types';

export function ProfileScreen() {
  const navigation = useNavigation<NativeStackNavigationProp<RootStackParamList>>();
  const rootNav = navigation.getParent<NativeStackNavigationProp<RootStackParamList>>();
  const { isAuthenticated, email, logout } = useAuth();

  const handleLogout = () => {
    Alert.alert('Log out', 'Are you sure you want to log out?', [
      { text: 'Cancel', style: 'cancel' },
      {
        text: 'Log out',
        style: 'destructive',
        onPress: () => {
          logout();
          (rootNav ?? navigation).dispatch(
            CommonActions.reset({ index: 0, routes: [{ name: 'Onboarding' }] }),
          );
        },
      },
    ]);
  };

  const handleDeleteAccount = () => {
    Alert.alert(
      'Delete account',
      'This will permanently delete your account, profile, and all saved data. This action cannot be undone.',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Delete',
          style: 'destructive',
          onPress: () => {
            logout();
            navigation.dispatch(
              CommonActions.reset({ index: 0, routes: [{ name: 'Onboarding' }] }),
            );
          },
        },
      ],
    );
  };

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Profile</Text>

      {isAuthenticated ? (
        <View style={styles.section}>
          <Text style={styles.email}>{email}</Text>
          <Text style={styles.subtitle}>See and tune the preferences shaping your recommendations.</Text>
          <Button title="My algorithm" onPress={() => (rootNav ?? navigation).navigate('Algorithm' as never)} />

          <View style={styles.actions}>
            <Button title="Log out" onPress={handleLogout} variant="outline" />
            <Button
              title="Delete account"
              onPress={handleDeleteAccount}
              variant="ghost"
              style={styles.deleteButton}
            />
          </View>
        </View>
      ) : (
        <View style={styles.section}>
          <Text style={styles.subtitle}>
            Sign in to save your preferences across devices
          </Text>
          <Button
            title="Sign in"
            onPress={() => (rootNav ?? navigation).navigate('Login' as never)}
          />
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
    padding: spacing.lg,
    paddingTop: 80,
  },
  title: {
    ...typography.h1,
    color: colors.textPrimary,
    marginBottom: spacing.lg,
  },
  section: {
    flex: 1,
    gap: spacing.md,
  },
  email: {
    ...typography.bodyBold,
    color: colors.textPrimary,
  },
  subtitle: {
    ...typography.body,
    color: colors.textSecondary,
  },
  actions: {
    marginTop: 'auto' as any,
    marginBottom: spacing.xl,
    gap: spacing.sm,
  },
  deleteButton: {
    opacity: 0.6,
  },
});
