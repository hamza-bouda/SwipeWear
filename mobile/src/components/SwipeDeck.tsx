import React, { useCallback, useMemo, useRef, useState } from 'react';
import { View, StyleSheet, Dimensions, Platform, Pressable, Text } from 'react-native';
import { Gesture, GestureDetector } from 'react-native-gesture-handler';
import { Ionicons } from '@expo/vector-icons';
import Animated, {
  useSharedValue,
  useAnimatedStyle,
  withSpring,
  withTiming,
  runOnJS,
  interpolate,
  Extrapolation,
} from 'react-native-reanimated';
import { Product } from '../types';
import { SwipeCard } from './SwipeCard';
import { spacing, colors, borderRadius } from '../theme';

const { width: SCREEN_WIDTH, height: SCREEN_HEIGHT } = Dimensions.get('window');
const SWIPE_THRESHOLD = SCREEN_WIDTH * 0.3;
const SWIPE_VELOCITY = 500;
// Vertical needs its own, smaller threshold: a card is far taller than it is
// wide, so reusing the horizontal one would make "up" a much longer drag.
const SWIPE_UP_THRESHOLD = SCREEN_HEIGHT * 0.15;
const TAP_MAX_DISTANCE = 8;

export type SwipeDirection = 'left' | 'right' | 'up';

interface SwipeDeckProps {
  products: Product[];
  onSwipeRight: (product: Product) => void;
  onSwipeLeft: (product: Product) => void;
  /** Swipe up — create an alert for this product. */
  onSwipeUp?: (product: Product) => void;
  onTap: (product: Product) => void;
  onSave: (product: Product) => void;
  onDeckEmpty: () => void;
  onAlert?: (product: Product) => void;
}

export function SwipeDeck({
  products,
  onSwipeRight,
  onSwipeLeft,
  onSwipeUp,
  onTap,
  onSave,
  onDeckEmpty,
  onAlert,
}: SwipeDeckProps) {
  const [currentIndex, setCurrentIndex] = useState(0);
  const indexRef = useRef(0);
  const translateX = useSharedValue(0);
  const translateY = useSharedValue(0);
  const rotation = useSharedValue(0);
  const isAnimating = useRef(false);
  const gestureRef = useRef<View>(null);

  const productsRef = useRef(products);
  productsRef.current = products;

  const callbacksRef = useRef({ onSwipeRight, onSwipeLeft, onSwipeUp, onTap, onDeckEmpty, onSave, onAlert });
  callbacksRef.current = { onSwipeRight, onSwipeLeft, onSwipeUp, onTap, onDeckEmpty, onSave, onAlert };

  const handleSwipeComplete = useCallback((direction: SwipeDirection) => {
    translateX.value = 0;
    translateY.value = 0;
    rotation.value = 0;

    const product = productsRef.current[indexRef.current];
    if (!product) return;

    if (direction === 'right') {
      callbacksRef.current.onSwipeRight(product);
    } else if (direction === 'up') {
      callbacksRef.current.onSwipeUp?.(product);
    } else {
      callbacksRef.current.onSwipeLeft(product);
    }

    const next = indexRef.current + 1;
    indexRef.current = next;
    setCurrentIndex(next);

    if (next >= productsRef.current.length) {
      callbacksRef.current.onDeckEmpty();
    }
    isAnimating.current = false;
  }, [translateX, translateY, rotation]);

  const animateOut = useCallback(
    (direction: SwipeDirection) => {
      if (direction === 'up') {
        translateY.value = withTiming(-SCREEN_HEIGHT, { duration: 300 }, (finished) => {
          if (finished) {
            runOnJS(handleSwipeComplete)(direction);
          }
        });
        return;
      }
      const toX = direction === 'right' ? SCREEN_WIDTH * 1.5 : -SCREEN_WIDTH * 1.5;
      translateX.value = withTiming(toX, { duration: 300 }, (finished) => {
        if (finished) {
          runOnJS(handleSwipeComplete)(direction);
        }
      });
    },
    [translateX, translateY, rotation, handleSwipeComplete],
  );

  const resetPosition = useCallback(() => {
    translateX.value = withSpring(0, { damping: 15 });
    translateY.value = withSpring(0, { damping: 15 });
    rotation.value = withSpring(0, { damping: 15 });
  }, [translateX, translateY, rotation]);

  const handleTapOnCard = useCallback(() => {
    const product = productsRef.current[indexRef.current];
    if (product) callbacksRef.current.onTap(product);
  }, []);

  const handleDrag = useCallback(
    (dx: number, dy: number) => {
      translateX.value = dx;
      // Upward drags follow the finger; downward ones stay damped, since only
      // up is a gesture — down is just the card resisting.
      translateY.value = dy < 0 ? dy : dy * 0.5;
      rotation.value = interpolate(
        dx,
        [-SCREEN_WIDTH / 2, 0, SCREEN_WIDTH / 2],
        [-15, 0, 15],
        Extrapolation.CLAMP,
      );
    },
    [translateX, translateY, rotation],
  );

  const handleRelease = useCallback(
    (dx: number, velocityX: number, dy = 0, velocityY = 0) => {
      if (isAnimating.current) return;

      // Vertical is judged first, and only when it dominates the horizontal
      // movement: every real swipe drifts a little sideways, and without the
      // comparison a hurried left-swipe would raise an alert instead.
      const wantsUp =
        dy < 0
        && (Math.abs(dy) > SWIPE_UP_THRESHOLD || velocityY < -SWIPE_VELOCITY)
        && Math.abs(dy) > Math.abs(dx);
      if (wantsUp && callbacksRef.current.onSwipeUp) {
        isAnimating.current = true;
        animateOut('up');
        return;
      }

      const shouldSwipe =
        Math.abs(dx) > SWIPE_THRESHOLD || Math.abs(velocityX) > SWIPE_VELOCITY;
      if (shouldSwipe) {
        isAnimating.current = true;
        animateOut(dx > 0 ? 'right' : 'left');
      } else {
        resetPosition();
      }
    },
    [animateOut, resetPosition],
  );

  const webCleanup = useRef<(() => void) | null>(null);

  const setGestureNode = useCallback(
    (view: View | null) => {
      (gestureRef as React.MutableRefObject<View | null>).current = view;
      if (Platform.OS !== 'web') return;

      if (webCleanup.current) {
        webCleanup.current();
        webCleanup.current = null;
      }

      const node = view as unknown as HTMLElement | null;
      if (!node || typeof node.addEventListener !== 'function') return;

      let dragging = false;
      let startX = 0;
      let startY = 0;
      let lastX = 0;
      let lastY = 0;
      let lastT = 0;
      let velocityX = 0;
      let velocityY = 0;

      const onDown = (e: PointerEvent) => {
        if (isAnimating.current) return;
        const target = e.target as HTMLElement;
        // Must stay in sync with SwipeCard's save button accessibilityLabel —
        // on web it renders as aria-label, and this is what stops a tap on the
        // heart from also starting a card drag.
        if (target.closest('[data-swipe-action]') || target.closest('[aria-label="Sauvegarder la pièce"]')) return;
        dragging = true;
        startX = e.clientX;
        startY = e.clientY;
        lastX = e.clientX;
        lastY = e.clientY;
        lastT = e.timeStamp;
        velocityX = 0;
        velocityY = 0;
        try {
          node.setPointerCapture(e.pointerId);
        } catch {
          // synthetic events may not support pointer capture
        }
        e.preventDefault();
      };

      const onMove = (e: PointerEvent) => {
        if (!dragging || isAnimating.current) return;
        const dt = e.timeStamp - lastT;
        if (dt > 0) {
          velocityX = ((e.clientX - lastX) / dt) * 1000;
          velocityY = ((e.clientY - lastY) / dt) * 1000;
        }
        lastX = e.clientX;
        lastY = e.clientY;
        lastT = e.timeStamp;
        handleDrag(e.clientX - startX, e.clientY - startY);
      };

      const onUp = (e: PointerEvent) => {
        if (!dragging) return;
        dragging = false;
        const dx = e.clientX - startX;
        const dy = e.clientY - startY;
        if (Math.abs(dx) < TAP_MAX_DISTANCE && Math.abs(dy) < TAP_MAX_DISTANCE) {
          resetPosition();
          handleTapOnCard();
          return;
        }
        handleRelease(dx, velocityX, dy, velocityY);
      };

      const onCancel = () => {
        if (!dragging) return;
        dragging = false;
        resetPosition();
      };

      const prevent = (e: Event) => e.preventDefault();

      node.style.touchAction = 'none';
      node.style.userSelect = 'none';
      node.style.cursor = 'grab';

      node.addEventListener('pointerdown', onDown);
      window.addEventListener('pointermove', onMove);
      window.addEventListener('pointerup', onUp);
      window.addEventListener('pointercancel', onCancel);
      node.addEventListener('dragstart', prevent);

      webCleanup.current = () => {
        node.removeEventListener('pointerdown', onDown);
        window.removeEventListener('pointermove', onMove);
        window.removeEventListener('pointerup', onUp);
        window.removeEventListener('pointercancel', onCancel);
        node.removeEventListener('dragstart', prevent);
      };
    },
    [handleDrag, handleRelease, handleTapOnCard, resetPosition],
  );

  const gesture = useMemo(() => {
    const pan = Gesture.Pan()
      // failOffsetY used to abort the pan as soon as it moved 20px vertically,
      // which is precisely why swiping up did nothing. Both axes activate now.
      .activeOffsetX([-10, 10])
      .activeOffsetY([-10, 10])
      .shouldCancelWhenOutside(false)
      .onUpdate((event) => {
        'worklet';
        translateX.value = event.translationX;
        translateY.value =
          event.translationY < 0 ? event.translationY : event.translationY * 0.5;
        rotation.value = interpolate(
          event.translationX,
          [-SCREEN_WIDTH / 2, 0, SCREEN_WIDTH / 2],
          [-15, 0, 15],
          Extrapolation.CLAMP,
        );
      })
      .onEnd((event) => {
        'worklet';
        runOnJS(handleRelease)(
          event.translationX, event.velocityX,
          event.translationY, event.velocityY,
        );
      });

    const tap = Gesture.Tap().onEnd(() => {
      runOnJS(handleTapOnCard)();
    });

    return Gesture.Race(pan, tap);
  }, [translateX, translateY, rotation, handleRelease, handleTapOnCard]);

  const topCardStyle = useAnimatedStyle(() => ({
    transform: [
      { translateX: translateX.value },
      { translateY: translateY.value },
      { rotate: `${rotation.value}deg` },
    ],
  }));

  const nextCardStyle = useAnimatedStyle(() => {
    const scale = interpolate(
      Math.abs(translateX.value),
      [0, SWIPE_THRESHOLD],
      [0.95, 1],
      Extrapolation.CLAMP,
    );
    const opacity = interpolate(
      Math.abs(translateX.value),
      [0, SWIPE_THRESHOLD],
      [0.7, 1],
      Extrapolation.CLAMP,
    );
    return { transform: [{ scale }], opacity };
  });

  const rightLabelStyle = useAnimatedStyle(() => ({
    opacity: interpolate(
      translateX.value,
      [0, SWIPE_THRESHOLD],
      [0, 1],
      Extrapolation.CLAMP,
    ),
  }));

  const leftLabelStyle = useAnimatedStyle(() => ({
    opacity: interpolate(
      translateX.value,
      [-SWIPE_THRESHOLD, 0],
      [1, 0],
      Extrapolation.CLAMP,
    ),
  }));

  const handlePressLeft = useCallback(() => {
    if (isAnimating.current || currentIndex >= productsRef.current.length) return;
    isAnimating.current = true;
    animateOut('left');
  }, [animateOut, currentIndex]);

  const handlePressRight = useCallback(() => {
    if (isAnimating.current || currentIndex >= productsRef.current.length) return;
    isAnimating.current = true;
    animateOut('right');
  }, [animateOut, currentIndex]);

  const handlePressAlert = useCallback(() => {
    const product = productsRef.current[indexRef.current];
    if (product && callbacksRef.current.onAlert) {
      callbacksRef.current.onAlert(product);
    }
  }, []);

  if (currentIndex >= products.length) return null;

  const topProduct = products[currentIndex];
  const nextProduct = currentIndex + 1 < products.length ? products[currentIndex + 1] : null;

  const cardContent = (
    <View ref={setGestureNode} collapsable={false}>
      <SwipeCard
        product={topProduct}
        onSave={() => callbacksRef.current.onSave(topProduct)}
      />
      <Animated.View style={[styles.label, styles.likeLabel, rightLabelStyle]}>
        <Text style={styles.labelText}>LIKE</Text>
      </Animated.View>
      <Animated.View style={[styles.label, styles.nopeLabel, leftLabelStyle]}>
        <Text style={styles.labelText}>NOPE</Text>
      </Animated.View>
    </View>
  );

  return (
    <View style={styles.container}>
      <View style={styles.deckArea}>
        {nextProduct && (
          <Animated.View
            key="next"
            style={[styles.cardWrapper, nextCardStyle, { zIndex: 1 }]}
          >
            <SwipeCard product={nextProduct} />
          </Animated.View>
        )}
        <Animated.View
          key="top"
          style={[styles.cardWrapper, topCardStyle, { zIndex: 2 }]}
        >
          {Platform.OS === 'web' ? (
            cardContent
          ) : (
            <GestureDetector gesture={gesture}>{cardContent}</GestureDetector>
          )}
        </Animated.View>
      </View>

      <View style={styles.actionRow} data-swipe-action>
        <Pressable
          style={[styles.actionBtn, styles.actionReject]}
          onPress={handlePressLeft}
          accessibilityRole="button"
          accessibilityLabel="Passer"
          // @ts-ignore — web only
          data-swipe-action="true"
        >
          <Ionicons name="close" size={22} color={colors.textSecondary} />
        </Pressable>
        <Pressable
          style={[styles.actionBtn, styles.actionAlert]}
          onPress={handlePressAlert}
          accessibilityRole="button"
          accessibilityLabel="Créer une alerte"
          // @ts-ignore — web only
          data-swipe-action="true"
        >
          <Ionicons name="notifications" size={22} color={colors.gold} />
        </Pressable>
        <Pressable
          style={[styles.actionBtn, styles.actionLike]}
          onPress={handlePressRight}
          accessibilityRole="button"
          accessibilityLabel="J'aime"
          // @ts-ignore — web only
          data-swipe-action="true"
        >
          <Ionicons name="heart" size={22} color={colors.accentText} />
        </Pressable>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  deckArea: {
    flex: 1,
    width: '100%',
    alignItems: 'center',
    justifyContent: 'center',
  },
  cardWrapper: {
    position: 'absolute',
  },
  label: {
    position: 'absolute',
    top: spacing.xl,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    borderWidth: 2.5,
    borderRadius: 8,
  },
  likeLabel: {
    left: spacing.lg,
    borderColor: colors.accent,
  },
  nopeLabel: {
    right: spacing.lg,
    borderColor: colors.error,
  },
  labelText: {
    fontSize: 26,
    fontWeight: '800',
    color: colors.textInverse,
    letterSpacing: 2,
  },
  actionRow: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    gap: 20,
    paddingVertical: spacing.md,
    paddingBottom: spacing.lg,
  },
  actionBtn: {
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: 99,
  },
  actionReject: {
    width: 56,
    height: 56,
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.border,
  },
  actionAlert: {
    width: 64,
    height: 64,
    backgroundColor: colors.goldBg,
    borderWidth: 1.5,
    borderColor: colors.gold,
  },
  actionLike: {
    width: 56,
    height: 56,
    backgroundColor: colors.accent,
  },
});
