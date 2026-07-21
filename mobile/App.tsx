import React from 'react';
import { StatusBar } from 'expo-status-bar';
import { GestureHandlerRootView } from 'react-native-gesture-handler';
import { NavigationContainer } from '@react-navigation/native';
import { RootNavigator } from './src/navigation';
import { SavesProvider } from './src/context/SavesContext';

export default function App() {
  return (
    <GestureHandlerRootView style={{ flex: 1 }}>
      <SavesProvider>
        <NavigationContainer>
          <StatusBar style="auto" />
          <RootNavigator />
        </NavigationContainer>
      </SavesProvider>
    </GestureHandlerRootView>
  );
}
