import 'package:flutter_test/flutter_test.dart';

import 'package:swipewear/features/dressing/data/saves_repository.dart';
import 'package:swipewear/features/drop/data/drop_repository.dart';

void main() {
  test('cached Drop data is explicitly marked offline', () {
    const snapshot = DropSnapshot(items: [], isOffline: true);

    expect(snapshot.items, isEmpty);
    expect(snapshot.isOffline, isTrue);
  });

  test('cached dressing data is explicitly marked offline', () {
    const snapshot = SavesSnapshot(products: [], isOffline: true);

    expect(snapshot.products, isEmpty);
    expect(snapshot.isOffline, isTrue);
  });
}
