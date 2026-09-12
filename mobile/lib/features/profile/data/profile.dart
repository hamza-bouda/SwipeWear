class LockedAttribute {
  const LockedAttribute({
    required this.attribute,
    required this.value,
    this.weight = 1,
    this.locked = false,
  });

  final String attribute;
  final String value;
  final double weight;
  final bool locked;

  factory LockedAttribute.fromJson(Map<String, dynamic> json) =>
      LockedAttribute(
        attribute: json['attribute'] as String? ?? 'style',
        value: json['value'] as String? ?? '',
        weight: (json['weight'] as num?)?.toDouble() ?? 1,
        locked: json['locked'] as bool? ?? false,
      );
}

class ProfileSnapshot {
  const ProfileSnapshot({
    required this.userId,
    required this.sizes,
    required this.maxPrice,
    required this.gender,
    required this.likedBrands,
    required this.rejectedBrands,
    required this.lockedAttributes,
    required this.eventCount,
    required this.isColdStart,
  });

  final String userId;
  final List<String> sizes;
  final double? maxPrice;
  final String? gender;
  final List<String> likedBrands;
  final List<String> rejectedBrands;
  final List<LockedAttribute> lockedAttributes;
  final int eventCount;
  final bool isColdStart;

  factory ProfileSnapshot.fromJson(Map<String, dynamic> json) {
    final constraints = _map(json['hard_constraints']);
    final preferences = _map(json['editable_preferences']);
    final rawLocked = preferences['locked_attributes'];
    return ProfileSnapshot(
      userId: json['user_id'] as String? ?? '',
      sizes: _strings(constraints['sizes']),
      maxPrice: (constraints['max_price_eur'] as num?)?.toDouble(),
      gender: constraints['gender'] as String?,
      likedBrands: _strings(preferences['liked_brands']),
      rejectedBrands: _strings(preferences['rejected_brands']),
      lockedAttributes:
          rawLocked is List
              ? rawLocked
                  .whereType<Map<String, dynamic>>()
                  .map(LockedAttribute.fromJson)
                  .toList()
              : const [],
      eventCount: json['event_count'] as int? ?? 0,
      isColdStart: json['is_cold_start'] as bool? ?? true,
    );
  }

  ProfileSnapshot copyWith({
    List<String>? sizes,
    double? maxPrice,
    bool clearMaxPrice = false,
    String? gender,
  }) => ProfileSnapshot(
    userId: userId,
    sizes: sizes ?? this.sizes,
    maxPrice: clearMaxPrice ? null : (maxPrice ?? this.maxPrice),
    gender: gender ?? this.gender,
    likedBrands: likedBrands,
    rejectedBrands: rejectedBrands,
    lockedAttributes: lockedAttributes,
    eventCount: eventCount,
    isColdStart: isColdStart,
  );

  static Map<String, dynamic> _map(Object? value) =>
      value is Map<String, dynamic> ? value : const {};

  static List<String> _strings(Object? value) =>
      value is List
          ? value.whereType<String>().toList(growable: false)
          : const [];
}

class PreferenceItem {
  const PreferenceItem({
    required this.id,
    required this.attribute,
    required this.value,
    required this.source,
    required this.locked,
  });

  final String id;
  final String attribute;
  final String value;
  final String source;
  final bool locked;

  factory PreferenceItem.fromJson(Map<String, dynamic> json) => PreferenceItem(
    id: json['id'] as String? ?? '',
    attribute: json['attribute'] as String? ?? '',
    value: json['value'] as String? ?? '',
    source: json['source'] as String? ?? 'edited',
    locked: json['locked'] as bool? ?? false,
  );
}
