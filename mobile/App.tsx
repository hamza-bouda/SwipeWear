import React, { useCallback, useRef } from 'react';
import { StatusBar } from 'expo-status-bar';
import { GestureHandlerRootView } from 'react-native-gesture-handler';
import { NavigationContainer, NavigationContainerRef } from '@react-navigation/native';
import { AuthProvider } from './src/context/AuthContext';
import { PreferencesProvider } from './src/context/PreferencesContext';
import { SavesProvider } from './src/context/SavesContext';
import { AlgorithmProvider } from './src/context/AlgorithmContext';
import { RootNavigator } from './src/navigation';
import { useNotifications } from './src/notifications/useNotifications';

function NotificationHandler({ navRef }: { navRef: React.RefObject<NavigationContainerRef<any> | null> }) {
  const navigate = useCallback((screen: string, params?: Record<string, string>) => {
    navRef.current?.navigate(screen as never, params as never);
  }, [navRef]);
  useNotifications(navigate);
  return null;
}

export default function App() {
  const navigationRef = useRef<NavigationContainerRef<any>>(null);

  return (
    <GestureHandlerRootView style={{ flex: 1 }}>
      <PreferencesProvider>
        <AuthProvider>
          <SavesProvider>
            <AlgorithmProvider>
              <NavigationContainer ref={navigationRef}>
                <StatusBar style="auto" />
                <NotificationHandler navRef={navigationRef} />
                <RootNavigator />
              </NavigationContainer>
            </AlgorithmProvider>
          </SavesProvider>
        </AuthProvider>
      </PreferencesProvider>
    </GestureHandlerRootView>
  );
}
