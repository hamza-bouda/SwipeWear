import React from 'react';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import {
  OnboardingScreen,
  StyleSelectionScreen,
  ImageImportScreen,
  ConstraintsScreen,
  ProductDetailScreen,
} from '../screens';
import { MainTabs } from './MainTabs';
import { RootStackParamList } from './types';

const Stack = createNativeStackNavigator<RootStackParamList>();

export function RootNavigator() {
  return (
    <Stack.Navigator
      initialRouteName="Onboarding"
      screenOptions={{ headerShown: false }}
    >
      <Stack.Screen name="Onboarding" component={OnboardingScreen} />
      <Stack.Screen name="StyleSelection" component={StyleSelectionScreen} />
      <Stack.Screen name="ImageImport" component={ImageImportScreen} />
      <Stack.Screen name="Constraints" component={ConstraintsScreen} />
      <Stack.Screen name="Main" component={MainTabs} />
      <Stack.Screen name="ProductDetail" component={ProductDetailScreen} />
    </Stack.Navigator>
  );
}
