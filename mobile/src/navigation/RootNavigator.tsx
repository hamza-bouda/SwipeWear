import React from 'react';
import { ActivityIndicator, View } from 'react-native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import {
  GenderLanguageScreen,
  OnboardingScreen,
  StyleSelectionScreen,
  ImageImportScreen,
  ConstraintsScreen,
  LoginScreen,
  ProductDetailScreen,
  PriceLadderScreen,
  AlgorithmScreen,
} from '../screens';
import { MainTabs } from './MainTabs';
import { RootStackParamList } from './types';
import { useAuth } from '../context/AuthContext';
import { usePreferences } from '../context/PreferencesContext';
import { colors } from '../theme';

const Stack = createNativeStackNavigator<RootStackParamList>();

export function RootNavigator() {
  const { gender, onboardingCompleted, ready: prefsReady } = usePreferences();
  const { isAuthenticated, ready: authReady } = useAuth();

  // The first route used to be hardcoded to GenderLanguage, so a returning
  // user — signed in, gender chosen, profile built — was walked through the
  // whole onboarding again on every single launch.
  if (!prefsReady || !authReady) {
    return (
      <View style={{ flex: 1, alignItems: 'center', justifyContent: 'center', backgroundColor: colors.background }}>
        <ActivityIndicator size="large" color={colors.accent} />
      </View>
    );
  }

  let initialRouteName: keyof RootStackParamList = 'GenderLanguage';
  if (gender !== null) {
    // Being signed in implies the flow was completed at least once: the login
    // screen is only reachable from the profile tab, which lives inside Main.
    initialRouteName = onboardingCompleted || isAuthenticated ? 'Main' : 'Onboarding';
  }

  return (
    <Stack.Navigator
      initialRouteName={initialRouteName}
      screenOptions={{ headerShown: false }}
    >
      <Stack.Screen name="GenderLanguage" component={GenderLanguageScreen} />
      <Stack.Screen name="Onboarding" component={OnboardingScreen} />
      <Stack.Screen name="StyleSelection" component={StyleSelectionScreen} />
      <Stack.Screen name="ImageImport" component={ImageImportScreen} />
      <Stack.Screen name="Constraints" component={ConstraintsScreen} />
      <Stack.Screen name="Main" component={MainTabs} />
      <Stack.Screen name="ProductDetail" component={ProductDetailScreen} />
      <Stack.Screen name="PriceLadder" component={PriceLadderScreen} />
      <Stack.Screen name="Login" component={LoginScreen} />
      <Stack.Screen name="Algorithm" component={AlgorithmScreen} />
    </Stack.Navigator>
  );
}
