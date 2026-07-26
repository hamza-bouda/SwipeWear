import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  Image,
  TouchableOpacity,
  Alert,
} from 'react-native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import * as ImagePicker from 'expo-image-picker';
import { Button } from '../components';
import { colors, typography, spacing, borderRadius } from '../theme';
import { RootStackParamList } from '../navigation/types';

const MAX_IMAGES = 10;
const MIN_IMAGES = 3;

interface Props {
  navigation: NativeStackNavigationProp<RootStackParamList, 'ImageImport'>;
}

export function ImageImportScreen({ navigation }: Props) {
  const [images, setImages] = useState<string[]>([]);

  const pickImages = async () => {
    const { status } = await ImagePicker.requestMediaLibraryPermissionsAsync();
    if (status !== 'granted') {
      Alert.alert('Autorisation requise', 'Nous avons besoin d\'accéder à ta galerie photo.');
      return;
    }

    const remaining = MAX_IMAGES - images.length;
    if (remaining <= 0) {
      Alert.alert('Maximum atteint', `Tu peux sélectionner jusqu'à ${MAX_IMAGES} images.`);
      return;
    }

    const result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ['images'],
      allowsMultipleSelection: true,
      selectionLimit: remaining,
      quality: 0.8,
    });

    if (!result.canceled && result.assets) {
      const uris = result.assets.map((a) => a.uri);
      setImages((prev) => [...prev, ...uris].slice(0, MAX_IMAGES));
    }
  };

  const removeImage = (index: number) => {
    setImages((prev) => prev.filter((_, i) => i !== index));
  };

  const renderImage = ({ item, index }: { item: string; index: number }) => (
    <View style={styles.imageContainer}>
      <Image source={{ uri: item }} style={styles.image} />
      <TouchableOpacity style={styles.removeButton} onPress={() => removeImage(index)}>
        <Text style={styles.removeText}>✕</Text>
      </TouchableOpacity>
    </View>
  );

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Importe tes inspirations</Text>
        <Text style={styles.subtitle}>
          Sélectionne {MIN_IMAGES} à {MAX_IMAGES} images dans ta galerie
        </Text>
      </View>

      {images.length > 0 ? (
        <FlatList
          data={images}
          renderItem={renderImage}
          keyExtractor={(_, i) => i.toString()}
          numColumns={3}
          columnWrapperStyle={styles.row}
          contentContainerStyle={styles.grid}
          showsVerticalScrollIndicator={false}
        />
      ) : (
        <View style={styles.emptyState}>
          <Text style={styles.emptyIcon}>📸</Text>
          <Text style={styles.emptyText}>Aucune image sélectionnée</Text>
        </View>
      )}

      <View style={styles.footer}>
        <Button
          title={images.length < MAX_IMAGES ? 'Ajouter des images' : 'Maximum atteint'}
          variant="outline"
          onPress={pickImages}
          disabled={images.length >= MAX_IMAGES}
          style={styles.addButton}
        />
        <Button
          title={`Continuer (${images.length}/${MIN_IMAGES}+)`}
          onPress={() =>
            navigation.navigate('Constraints', {
              route: 'images',
              imageUris: images,
            })
          }
          disabled={images.length < MIN_IMAGES}
        />
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
  },
  header: {
    paddingHorizontal: spacing.lg,
    paddingTop: spacing.xxl,
    paddingBottom: spacing.md,
  },
  title: {
    ...typography.h1,
    color: colors.textPrimary,
  },
  subtitle: {
    ...typography.body,
    color: colors.textSecondary,
    marginTop: spacing.xs,
  },
  grid: {
    paddingHorizontal: spacing.lg,
    paddingBottom: spacing.lg,
  },
  row: {
    gap: spacing.sm,
    marginBottom: spacing.sm,
  },
  imageContainer: {
    flex: 1,
    aspectRatio: 1,
    maxWidth: '33%',
    borderRadius: borderRadius.sm,
    overflow: 'hidden',
  },
  image: {
    width: '100%',
    height: '100%',
  },
  removeButton: {
    position: 'absolute',
    top: spacing.xs,
    right: spacing.xs,
    width: 24,
    height: 24,
    borderRadius: 12,
    backgroundColor: colors.overlay,
    alignItems: 'center',
    justifyContent: 'center',
  },
  removeText: {
    color: colors.textInverse,
    fontSize: 12,
    fontWeight: '700',
  },
  emptyState: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  emptyIcon: {
    fontSize: 48,
    marginBottom: spacing.md,
  },
  emptyText: {
    ...typography.body,
    color: colors.textSecondary,
  },
  footer: {
    padding: spacing.lg,
    paddingBottom: spacing.xxl,
  },
  addButton: {
    marginBottom: spacing.sm,
  },
});
