import React from 'react';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { StyleSheet, View } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { FeedScreen, SavesScreen, ProfileScreen, AlertsScreen, DropScreen } from '../screens';
import { colors, typography } from '../theme';
import { MainTabParamList } from './types';

const Tab = createBottomTabNavigator<MainTabParamList>();

type IoniconName = React.ComponentProps<typeof Ionicons>['name'];

const TAB_CONFIG: Record<string, { icon: IoniconName; iconFocused: IoniconName; label: string }> = {
  Feed:     { icon: 'layers-outline',        iconFocused: 'layers',         label: 'Swipe' },
  Drop:     { icon: 'flash-outline',         iconFocused: 'flash',          label: 'Drop' },
  Alerts:   { icon: 'notifications-outline', iconFocused: 'notifications',  label: 'Alertes' },
  Dressing: { icon: 'shirt-outline',         iconFocused: 'shirt',          label: 'Dressing' },
  Profile:  { icon: 'person-outline',        iconFocused: 'person',         label: 'Profil' },
};

function TabIcon({ name, focused }: { name: string; focused: boolean }) {
  const cfg = TAB_CONFIG[name];
  if (!cfg) return null;
  return (
    <View style={focused ? styles.iconWrapFocused : styles.iconWrap}>
      <Ionicons
        name={focused ? cfg.iconFocused : cfg.icon}
        size={22}
        color={focused ? colors.accent : colors.disabled}
      />
    </View>
  );
}

export function MainTabs() {
  return (
    <Tab.Navigator
      screenOptions={({ route }) => ({
        headerShown: false,
        tabBarIcon: ({ focused }) => <TabIcon name={route.name} focused={focused} />,
        tabBarLabel: TAB_CONFIG[route.name]?.label ?? route.name,
        tabBarActiveTintColor: colors.accent,
        tabBarInactiveTintColor: colors.disabled,
        tabBarLabelStyle: styles.tabLabel,
        tabBarStyle: styles.tabBar,
        tabBarItemStyle: styles.tabItem,
      })}
    >
      <Tab.Screen name="Feed" component={FeedScreen} />
      <Tab.Screen name="Drop" component={DropScreen} />
      <Tab.Screen name="Alerts" component={AlertsScreen} />
      <Tab.Screen name="Dressing" component={SavesScreen} />
      <Tab.Screen name="Profile" component={ProfileScreen} />
    </Tab.Navigator>
  );
}

const styles = StyleSheet.create({
  iconWrap: {
    alignItems: 'center',
    justifyContent: 'center',
  },
  iconWrapFocused: {
    alignItems: 'center',
    justifyContent: 'center',
  },
  tabLabel: {
    ...typography.caption,
    fontSize: 10,
    fontWeight: '500',
  },
  tabBar: {
    position: 'absolute',
    backgroundColor: colors.surfaceElevated,
    borderTopWidth: 0,
    height: 70,
    left: 14,
    right: 14,
    bottom: 14,
    borderRadius: 22,
    paddingTop: 6,
    paddingBottom: 6,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.12,
    shadowRadius: 18,
    elevation: 10,
  },
  tabItem: {
    paddingTop: 4,
  },
});
