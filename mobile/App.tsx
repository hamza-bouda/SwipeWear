import React from 'react';
import { StatusBar } from 'expo-status-bar';
import { GestureHandlerRootView } from 'react-native-gesture-handler';
import { NavigationContainer } from '@react-navigation/native';
import { AuthProvider } from './src/context/AuthContext';
import { PreferencesProvider } from './src/context/PreferencesContext';
import { SavesProvider } from './src/context/SavesContext';
import { AlgorithmProvider } from './src/context/AlgorithmContext';
import { RootNavigator } from './src/navigation';

export default function App() {
  return (
    <GestureHandlerRootView style={{ flex: 1 }}>
      <PreferencesProvider>
        <AuthProvider>
          <SavesProvider>
            <AlgorithmProvider>
              <NavigationContainer>
                <StatusBar style="auto" />
                <RootNavigator />
              </NavigationContainer>
            </AlgorithmProvider>
          </SavesProvider>
        </AuthProvider>
      </PreferencesProvider>
    </GestureHandlerRootView>
  );
}
