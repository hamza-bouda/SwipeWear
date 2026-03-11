import React from 'react';
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

const Stack = createNativeStackNavigator<RootStackParamList>();

export function RootNavigator() {
  return (
    <Stack.Navigator
      initialRouteName="GenderLanguage"
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
