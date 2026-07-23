/**
 * Paywall screen — shown when a free user tries to create a 4th alert
 * or activate instant-priority notifications (KAN-73).
 *
 * Never presented as an interstitial on first launch. Only triggered by a
 * concrete action that hits the free tier limit.
 *
 * Design: blanc/noir/jaune (existing SwipeWear theme).
 */

import React, { useState } from 'react';
import {
  ActivityIndicator,
  Linking,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';

import { usePremium } from '../billing';

interface Props {
  onSuccess?: () => void;
  onDismiss?: () => void;
}

const BENEFITS = [
  { icon: '⚡', title: 'Alertes instantanées', desc: 'Soyez notifié en temps réel — sans délai de 30 minutes.' },
  { icon: '∞', title: 'Alertes illimitées', desc: 'Créez autant d\'alertes que vous voulez, sans limite.' },
  { icon: '🔍', title: 'Matching prioritaire', desc: 'Vos alertes sont traitées en premier dans la file.' },
];

export default function PaywallScreen({ onSuccess, onDismiss }: Props) {
  const { purchase, restore } = usePremium();
  const [purchasing, setPurchasing] = useState(false);
  const [restoring, setRestoring] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  async function handlePurchase() {
    setPurchasing(true);
    setErrorMsg(null);
    const result = await purchase();
    setPurchasing(false);
    if (result.success && result.isActive) {
      onSuccess?.();
    } else if (result.error) {
      setErrorMsg(result.error);
    }
  }

  async function handleRestore() {
    setRestoring(true);
    setErrorMsg(null);
    const result = await restore();
    setRestoring(false);
    if (result.isActive) {
      onSuccess?.();
    } else {
      setErrorMsg('Aucun achat trouvé à restaurer.');
    }
  }

  return (
    <View style={styles.container}>
      {/* Close button */}
      {onDismiss && (
        <Pressable style={styles.closeButton} onPress={onDismiss} hitSlop={12}>
          <Text style={styles.closeText}>✕</Text>
        </Pressable>
      )}

      <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
        {/* Header */}
        <View style={styles.badge}>
          <Text style={styles.badgeText}>PREMIUM</Text>
        </View>
        <Text style={styles.headline}>Passez au niveau supérieur</Text>
        <Text style={styles.subheadline}>
          Alertes instantanées, illimitées et prioritaires.
        </Text>

        {/* Benefits */}
        <View style={styles.benefitsList}>
          {BENEFITS.map((b) => (
            <View key={b.title} style={styles.benefitRow}>
              <Text style={styles.benefitIcon}>{b.icon}</Text>
              <View style={styles.benefitText}>
                <Text style={styles.benefitTitle}>{b.title}</Text>
                <Text style={styles.benefitDesc}>{b.desc}</Text>
              </View>
            </View>
          ))}
        </View>

        {/* Pricing */}
        <View style={styles.pricingBlock}>
          <Text style={styles.price}>4,99 €<Text style={styles.pricePeriod}> / mois</Text></Text>
          <Text style={styles.trial}>7 jours d'essai gratuit — annulable à tout moment</Text>
        </View>

        {/* Error */}
        {errorMsg && <Text style={styles.errorText}>{errorMsg}</Text>}

        {/* CTA */}
        <Pressable
          style={({ pressed }) => [styles.ctaButton, pressed && styles.ctaPressed]}
          onPress={handlePurchase}
          disabled={purchasing}
        >
          {purchasing ? (
            <ActivityIndicator color="#000" />
          ) : (
            <Text style={styles.ctaText}>Essayer gratuitement</Text>
          )}
        </Pressable>

        <Pressable
          style={({ pressed }) => [styles.restoreButton, pressed && styles.restorePressed]}
          onPress={handleRestore}
          disabled={restoring}
        >
          <Text style={styles.restoreText}>
            {restoring ? 'Restauration…' : 'Restaurer mes achats'}
          </Text>
        </Pressable>

        {/* Legal links */}
        <View style={styles.legalRow}>
          <Pressable onPress={() => Linking.openURL('https://swipewear.app/cgu')}>
            <Text style={styles.legalLink}>CGU</Text>
          </Pressable>
          <Text style={styles.legalSep}>·</Text>
          <Pressable onPress={() => Linking.openURL('https://swipewear.app/confidentialite')}>
            <Text style={styles.legalLink}>Confidentialité</Text>
          </Pressable>
        </View>
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#FFFFFF',
  },
  closeButton: {
    position: 'absolute',
    top: 52,
    right: 20,
    zIndex: 10,
    padding: 8,
  },
  closeText: {
    fontSize: 18,
    color: '#666',
  },
  content: {
    paddingHorizontal: 28,
    paddingTop: 80,
    paddingBottom: 40,
    alignItems: 'center',
  },
  badge: {
    backgroundColor: '#FFE500',
    paddingHorizontal: 14,
    paddingVertical: 4,
    borderRadius: 4,
    marginBottom: 20,
  },
  badgeText: {
    fontSize: 11,
    fontWeight: '700',
    letterSpacing: 2,
    color: '#000',
  },
  headline: {
    fontSize: 28,
    fontWeight: '800',
    color: '#0A0A0A',
    textAlign: 'center',
    marginBottom: 10,
    lineHeight: 34,
  },
  subheadline: {
    fontSize: 15,
    color: '#555',
    textAlign: 'center',
    marginBottom: 32,
    lineHeight: 22,
  },
  benefitsList: {
    width: '100%',
    marginBottom: 28,
    gap: 18,
  },
  benefitRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 14,
  },
  benefitIcon: {
    fontSize: 22,
    width: 32,
    textAlign: 'center',
    marginTop: 2,
  },
  benefitText: {
    flex: 1,
  },
  benefitTitle: {
    fontSize: 15,
    fontWeight: '700',
    color: '#0A0A0A',
    marginBottom: 2,
  },
  benefitDesc: {
    fontSize: 13,
    color: '#666',
    lineHeight: 18,
  },
  pricingBlock: {
    alignItems: 'center',
    marginBottom: 20,
    paddingVertical: 20,
    borderTopWidth: 1,
    borderBottomWidth: 1,
    borderColor: '#F0F0F0',
    width: '100%',
  },
  price: {
    fontSize: 36,
    fontWeight: '800',
    color: '#0A0A0A',
    marginBottom: 6,
  },
  pricePeriod: {
    fontSize: 18,
    fontWeight: '400',
    color: '#555',
  },
  trial: {
    fontSize: 13,
    color: '#666',
    textAlign: 'center',
  },
  errorText: {
    color: '#E53E3E',
    fontSize: 13,
    textAlign: 'center',
    marginBottom: 12,
  },
  ctaButton: {
    backgroundColor: '#FFE500',
    borderRadius: 12,
    paddingVertical: 16,
    width: '100%',
    alignItems: 'center',
    marginBottom: 14,
  },
  ctaPressed: {
    opacity: 0.85,
  },
  ctaText: {
    fontSize: 16,
    fontWeight: '700',
    color: '#000',
  },
  restoreButton: {
    paddingVertical: 10,
    marginBottom: 24,
  },
  restorePressed: {
    opacity: 0.6,
  },
  restoreText: {
    fontSize: 14,
    color: '#555',
    textDecorationLine: 'underline',
  },
  legalRow: {
    flexDirection: 'row',
    gap: 8,
    alignItems: 'center',
  },
  legalLink: {
    fontSize: 12,
    color: '#999',
    textDecorationLine: 'underline',
  },
  legalSep: {
    fontSize: 12,
    color: '#CCC',
  },
});
