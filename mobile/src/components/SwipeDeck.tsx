import React, { useCallback, useRef, useState } from 'react';
import { View, StyleSheet, Dimensions } from 'react-native';
import { Gesture, GestureDetector } from 'react-native-gesture-handler';
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
import { SwipeCard, CARD_WIDTH, CARD_HEIGHT } from './SwipeCard';
import { spacing } from '../theme';

const { width: SCREEN_WIDTH } = Dimensions.get('window');
const SWIPE_THRESHOLD = SCREEN_WIDTH * 0.3;
const SWIPE_VELOCITY = 500;

export type SwipeDirection = 'left' | 'right';

interface SwipeDeckProps {
  products: Product[];
  onSwipeRight: (product: Product) => void;
  onSwipeLeft: (product: Product) => void;
  onTap: (product: Product) => void;
  onSave: (product: Product) => void;
  onDeckEmpty: () => void;
}

export function SwipeDeck({
  products,
  onSwipeRight,
  onSwipeLeft,
  onTap,
  onSave,
  onDeckEmpty,
}: SwipeDeckProps) {
  const [currentIndex, setCurrentIndex] = useState(0);
  const translateX = useSharedValue(0);
  const translateY = useSharedValue(0);
  const rotation = useSharedValue(0);
  const isAnimating = useRef(false);

  const handleSwipeComplete = useCallback(
    (direction: SwipeDirection) => {
      const product = products[currentIndex];
      if (!product) return;

      if (direction === 'right') {
        onSwipeRight(product);
      } else {
        onSwipeLeft(product);
      }

      setCurrentIndex((prev) => {
        const next = prev + 1;
        if (next >= products.length) {
          onDeckEmpty();
        }
        return next;
      });
      isAnimating.current = false;
    },
    [currentIndex, products, onSwipeRight, onSwipeLeft, onDeckEmpty],
  );

  const animateOut = useCallback(
    (direction: SwipeDirection) => {
      'worklet';
      const toX = direction === 'right' ? SCREEN_WIDTH * 1.5 : -SCREEN_WIDTH * 1.5;
      translateX.value = withTiming(toX, { duration: 300 }, () => {
        translateX.value = 0;
        translateY.value = 0;
        rotation.value = 0;
        runOnJS(handleSwipeComplete)(direction);
      });
    },
    [translateX, translateY, rotation, handleSwipeComplete],
  );

  const gesture = Gesture.Pan()
    .onUpdate((event) => {
      if (isAnimating.current) return;
      translateX.value = event.translationX;
      translateY.value = event.translationY * 0.5;
      rotation.value = interpolate(
        event.translationX,
        [-SCREEN_WIDTH / 2, 0, SCREEN_WIDTH / 2],
        [-15, 0, 15],
        Extrapolation.CLAMP,
      );
    })
    .onEnd((event) => {
      if (isAnimating.current) return;
      const shouldSwipe =
        Math.abs(event.translationX) > SWIPE_THRESHOLD ||
        Math.abs(event.velocityX) > SWIPE_VELOCITY;

      if (shouldSwipe) {
        isAnimating.current = true;
        const direction: SwipeDirection =
          event.translationX > 0 ? 'right' : 'left';
        animateOut(direction);
      } else {
        translateX.value = withSpring(0, { damping: 15 });
        translateY.value = withSpring(0, { damping: 15 });
        rotation.value = withSpring(0, { damping: 15 });
      }
    });

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

  if (currentIndex >= products.length) return null;

  const visibleCards = products.slice(currentIndex, currentIndex + 2);

  return (
    <View style={styles.container}>
      {visibleCards.map((product, i) => {
        const isTop = i === 0;
        return (
          <Animated.View
            key={product.id}
            style={[
              styles.cardWrapper,
              isTop ? topCardStyle : nextCardStyle,
              { zIndex: visibleCards.length - i },
            ]}
          >
            {isTop ? (
              <GestureDetector gesture={gesture}>
                <Animated.View>
                  <SwipeCard
                    product={product}
                    onTap={() => onTap(product)}
                    onSave={() => onSave(product)}
                  />
                  <Animated.View style={[styles.label, styles.likeLabel, rightLabelStyle]}>
                    <Animated.Text style={styles.labelText}>LIKE</Animated.Text>
                  </Animated.View>
                  <Animated.View style={[styles.label, styles.nopeLabel, leftLabelStyle]}>
                    <Animated.Text style={styles.labelText}>NOPE</Animated.Text>
                  </Animated.View>
                </Animated.View>
              </GestureDetector>
            ) : (
              <SwipeCard product={product} />
            )}
          </Animated.View>
        );
      })}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
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
    borderWidth: 3,
    borderRadius: 8,
  },
  likeLabel: {
    left: spacing.lg,
    borderColor: '#34C759',
  },
  nopeLabel: {
    right: spacing.lg,
    borderColor: '#FF3B30',
  },
  labelText: {
    fontSize: 28,
    fontWeight: '800',
    color: '#FFF',
  },
});
