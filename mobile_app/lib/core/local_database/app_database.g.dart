// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'app_database.dart';

// ignore_for_file: type=lint
class $CachedContextsTable extends CachedContexts
    with TableInfo<$CachedContextsTable, CachedContext> {
  @override
  final GeneratedDatabase attachedDatabase;
  final String? _alias;
  $CachedContextsTable(this.attachedDatabase, [this._alias]);
  static const VerificationMeta _localUserKeyMeta =
      const VerificationMeta('localUserKey');
  @override
  late final GeneratedColumn<String> localUserKey = GeneratedColumn<String>(
      'local_user_key', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _membershipIdMeta =
      const VerificationMeta('membershipId');
  @override
  late final GeneratedColumn<int> membershipId = GeneratedColumn<int>(
      'membership_id', aliasedName, false,
      type: DriftSqlType.int, requiredDuringInsert: true);
  static const VerificationMeta _academicYearKeyMeta =
      const VerificationMeta('academicYearKey');
  @override
  late final GeneratedColumn<String> academicYearKey = GeneratedColumn<String>(
      'academic_year_key', aliasedName, false,
      type: DriftSqlType.string,
      requiredDuringInsert: false,
      defaultValue: const Constant(''));
  static const VerificationMeta _resourceIdMeta =
      const VerificationMeta('resourceId');
  @override
  late final GeneratedColumn<String> resourceId = GeneratedColumn<String>(
      'resource_id', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _payloadJsonMeta =
      const VerificationMeta('payloadJson');
  @override
  late final GeneratedColumn<String> payloadJson = GeneratedColumn<String>(
      'payload_json', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _isHistoricalMeta =
      const VerificationMeta('isHistorical');
  @override
  late final GeneratedColumn<bool> isHistorical = GeneratedColumn<bool>(
      'is_historical', aliasedName, false,
      type: DriftSqlType.bool,
      requiredDuringInsert: false,
      defaultConstraints: GeneratedColumn.constraintIsAlways(
          'CHECK ("is_historical" IN (0, 1))'),
      defaultValue: const Constant(false));
  static const VerificationMeta _cachedAtMeta =
      const VerificationMeta('cachedAt');
  @override
  late final GeneratedColumn<DateTime> cachedAt = GeneratedColumn<DateTime>(
      'cached_at', aliasedName, false,
      type: DriftSqlType.dateTime, requiredDuringInsert: true);
  static const VerificationMeta _lastSyncedAtMeta =
      const VerificationMeta('lastSyncedAt');
  @override
  late final GeneratedColumn<DateTime> lastSyncedAt = GeneratedColumn<DateTime>(
      'last_synced_at', aliasedName, false,
      type: DriftSqlType.dateTime, requiredDuringInsert: true);
  @override
  List<GeneratedColumn> get $columns => [
        localUserKey,
        membershipId,
        academicYearKey,
        resourceId,
        payloadJson,
        isHistorical,
        cachedAt,
        lastSyncedAt
      ];
  @override
  String get aliasedName => _alias ?? actualTableName;
  @override
  String get actualTableName => $name;
  static const String $name = 'cached_contexts';
  @override
  VerificationContext validateIntegrity(Insertable<CachedContext> instance,
      {bool isInserting = false}) {
    final context = VerificationContext();
    final data = instance.toColumns(true);
    if (data.containsKey('local_user_key')) {
      context.handle(
          _localUserKeyMeta,
          localUserKey.isAcceptableOrUnknown(
              data['local_user_key']!, _localUserKeyMeta));
    } else if (isInserting) {
      context.missing(_localUserKeyMeta);
    }
    if (data.containsKey('membership_id')) {
      context.handle(
          _membershipIdMeta,
          membershipId.isAcceptableOrUnknown(
              data['membership_id']!, _membershipIdMeta));
    } else if (isInserting) {
      context.missing(_membershipIdMeta);
    }
    if (data.containsKey('academic_year_key')) {
      context.handle(
          _academicYearKeyMeta,
          academicYearKey.isAcceptableOrUnknown(
              data['academic_year_key']!, _academicYearKeyMeta));
    }
    if (data.containsKey('resource_id')) {
      context.handle(
          _resourceIdMeta,
          resourceId.isAcceptableOrUnknown(
              data['resource_id']!, _resourceIdMeta));
    } else if (isInserting) {
      context.missing(_resourceIdMeta);
    }
    if (data.containsKey('payload_json')) {
      context.handle(
          _payloadJsonMeta,
          payloadJson.isAcceptableOrUnknown(
              data['payload_json']!, _payloadJsonMeta));
    } else if (isInserting) {
      context.missing(_payloadJsonMeta);
    }
    if (data.containsKey('is_historical')) {
      context.handle(
          _isHistoricalMeta,
          isHistorical.isAcceptableOrUnknown(
              data['is_historical']!, _isHistoricalMeta));
    }
    if (data.containsKey('cached_at')) {
      context.handle(_cachedAtMeta,
          cachedAt.isAcceptableOrUnknown(data['cached_at']!, _cachedAtMeta));
    } else if (isInserting) {
      context.missing(_cachedAtMeta);
    }
    if (data.containsKey('last_synced_at')) {
      context.handle(
          _lastSyncedAtMeta,
          lastSyncedAt.isAcceptableOrUnknown(
              data['last_synced_at']!, _lastSyncedAtMeta));
    } else if (isInserting) {
      context.missing(_lastSyncedAtMeta);
    }
    return context;
  }

  @override
  Set<GeneratedColumn> get $primaryKey =>
      {localUserKey, membershipId, academicYearKey, resourceId};
  @override
  CachedContext map(Map<String, dynamic> data, {String? tablePrefix}) {
    final effectivePrefix = tablePrefix != null ? '$tablePrefix.' : '';
    return CachedContext(
      localUserKey: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}local_user_key'])!,
      membershipId: attachedDatabase.typeMapping
          .read(DriftSqlType.int, data['${effectivePrefix}membership_id'])!,
      academicYearKey: attachedDatabase.typeMapping.read(
          DriftSqlType.string, data['${effectivePrefix}academic_year_key'])!,
      resourceId: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}resource_id'])!,
      payloadJson: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}payload_json'])!,
      isHistorical: attachedDatabase.typeMapping
          .read(DriftSqlType.bool, data['${effectivePrefix}is_historical'])!,
      cachedAt: attachedDatabase.typeMapping
          .read(DriftSqlType.dateTime, data['${effectivePrefix}cached_at'])!,
      lastSyncedAt: attachedDatabase.typeMapping.read(
          DriftSqlType.dateTime, data['${effectivePrefix}last_synced_at'])!,
    );
  }

  @override
  $CachedContextsTable createAlias(String alias) {
    return $CachedContextsTable(attachedDatabase, alias);
  }
}

class CachedContext extends DataClass implements Insertable<CachedContext> {
  final String localUserKey;
  final int membershipId;
  final String academicYearKey;
  final String resourceId;
  final String payloadJson;
  final bool isHistorical;
  final DateTime cachedAt;
  final DateTime lastSyncedAt;
  const CachedContext(
      {required this.localUserKey,
      required this.membershipId,
      required this.academicYearKey,
      required this.resourceId,
      required this.payloadJson,
      required this.isHistorical,
      required this.cachedAt,
      required this.lastSyncedAt});
  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    map['local_user_key'] = Variable<String>(localUserKey);
    map['membership_id'] = Variable<int>(membershipId);
    map['academic_year_key'] = Variable<String>(academicYearKey);
    map['resource_id'] = Variable<String>(resourceId);
    map['payload_json'] = Variable<String>(payloadJson);
    map['is_historical'] = Variable<bool>(isHistorical);
    map['cached_at'] = Variable<DateTime>(cachedAt);
    map['last_synced_at'] = Variable<DateTime>(lastSyncedAt);
    return map;
  }

  CachedContextsCompanion toCompanion(bool nullToAbsent) {
    return CachedContextsCompanion(
      localUserKey: Value(localUserKey),
      membershipId: Value(membershipId),
      academicYearKey: Value(academicYearKey),
      resourceId: Value(resourceId),
      payloadJson: Value(payloadJson),
      isHistorical: Value(isHistorical),
      cachedAt: Value(cachedAt),
      lastSyncedAt: Value(lastSyncedAt),
    );
  }

  factory CachedContext.fromJson(Map<String, dynamic> json,
      {ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return CachedContext(
      localUserKey: serializer.fromJson<String>(json['localUserKey']),
      membershipId: serializer.fromJson<int>(json['membershipId']),
      academicYearKey: serializer.fromJson<String>(json['academicYearKey']),
      resourceId: serializer.fromJson<String>(json['resourceId']),
      payloadJson: serializer.fromJson<String>(json['payloadJson']),
      isHistorical: serializer.fromJson<bool>(json['isHistorical']),
      cachedAt: serializer.fromJson<DateTime>(json['cachedAt']),
      lastSyncedAt: serializer.fromJson<DateTime>(json['lastSyncedAt']),
    );
  }
  @override
  Map<String, dynamic> toJson({ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return <String, dynamic>{
      'localUserKey': serializer.toJson<String>(localUserKey),
      'membershipId': serializer.toJson<int>(membershipId),
      'academicYearKey': serializer.toJson<String>(academicYearKey),
      'resourceId': serializer.toJson<String>(resourceId),
      'payloadJson': serializer.toJson<String>(payloadJson),
      'isHistorical': serializer.toJson<bool>(isHistorical),
      'cachedAt': serializer.toJson<DateTime>(cachedAt),
      'lastSyncedAt': serializer.toJson<DateTime>(lastSyncedAt),
    };
  }

  CachedContext copyWith(
          {String? localUserKey,
          int? membershipId,
          String? academicYearKey,
          String? resourceId,
          String? payloadJson,
          bool? isHistorical,
          DateTime? cachedAt,
          DateTime? lastSyncedAt}) =>
      CachedContext(
        localUserKey: localUserKey ?? this.localUserKey,
        membershipId: membershipId ?? this.membershipId,
        academicYearKey: academicYearKey ?? this.academicYearKey,
        resourceId: resourceId ?? this.resourceId,
        payloadJson: payloadJson ?? this.payloadJson,
        isHistorical: isHistorical ?? this.isHistorical,
        cachedAt: cachedAt ?? this.cachedAt,
        lastSyncedAt: lastSyncedAt ?? this.lastSyncedAt,
      );
  CachedContext copyWithCompanion(CachedContextsCompanion data) {
    return CachedContext(
      localUserKey: data.localUserKey.present
          ? data.localUserKey.value
          : this.localUserKey,
      membershipId: data.membershipId.present
          ? data.membershipId.value
          : this.membershipId,
      academicYearKey: data.academicYearKey.present
          ? data.academicYearKey.value
          : this.academicYearKey,
      resourceId:
          data.resourceId.present ? data.resourceId.value : this.resourceId,
      payloadJson:
          data.payloadJson.present ? data.payloadJson.value : this.payloadJson,
      isHistorical: data.isHistorical.present
          ? data.isHistorical.value
          : this.isHistorical,
      cachedAt: data.cachedAt.present ? data.cachedAt.value : this.cachedAt,
      lastSyncedAt: data.lastSyncedAt.present
          ? data.lastSyncedAt.value
          : this.lastSyncedAt,
    );
  }

  @override
  String toString() {
    return (StringBuffer('CachedContext(')
          ..write('localUserKey: $localUserKey, ')
          ..write('membershipId: $membershipId, ')
          ..write('academicYearKey: $academicYearKey, ')
          ..write('resourceId: $resourceId, ')
          ..write('payloadJson: $payloadJson, ')
          ..write('isHistorical: $isHistorical, ')
          ..write('cachedAt: $cachedAt, ')
          ..write('lastSyncedAt: $lastSyncedAt')
          ..write(')'))
        .toString();
  }

  @override
  int get hashCode => Object.hash(localUserKey, membershipId, academicYearKey,
      resourceId, payloadJson, isHistorical, cachedAt, lastSyncedAt);
  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      (other is CachedContext &&
          other.localUserKey == this.localUserKey &&
          other.membershipId == this.membershipId &&
          other.academicYearKey == this.academicYearKey &&
          other.resourceId == this.resourceId &&
          other.payloadJson == this.payloadJson &&
          other.isHistorical == this.isHistorical &&
          other.cachedAt == this.cachedAt &&
          other.lastSyncedAt == this.lastSyncedAt);
}

class CachedContextsCompanion extends UpdateCompanion<CachedContext> {
  final Value<String> localUserKey;
  final Value<int> membershipId;
  final Value<String> academicYearKey;
  final Value<String> resourceId;
  final Value<String> payloadJson;
  final Value<bool> isHistorical;
  final Value<DateTime> cachedAt;
  final Value<DateTime> lastSyncedAt;
  final Value<int> rowid;
  const CachedContextsCompanion({
    this.localUserKey = const Value.absent(),
    this.membershipId = const Value.absent(),
    this.academicYearKey = const Value.absent(),
    this.resourceId = const Value.absent(),
    this.payloadJson = const Value.absent(),
    this.isHistorical = const Value.absent(),
    this.cachedAt = const Value.absent(),
    this.lastSyncedAt = const Value.absent(),
    this.rowid = const Value.absent(),
  });
  CachedContextsCompanion.insert({
    required String localUserKey,
    required int membershipId,
    this.academicYearKey = const Value.absent(),
    required String resourceId,
    required String payloadJson,
    this.isHistorical = const Value.absent(),
    required DateTime cachedAt,
    required DateTime lastSyncedAt,
    this.rowid = const Value.absent(),
  })  : localUserKey = Value(localUserKey),
        membershipId = Value(membershipId),
        resourceId = Value(resourceId),
        payloadJson = Value(payloadJson),
        cachedAt = Value(cachedAt),
        lastSyncedAt = Value(lastSyncedAt);
  static Insertable<CachedContext> custom({
    Expression<String>? localUserKey,
    Expression<int>? membershipId,
    Expression<String>? academicYearKey,
    Expression<String>? resourceId,
    Expression<String>? payloadJson,
    Expression<bool>? isHistorical,
    Expression<DateTime>? cachedAt,
    Expression<DateTime>? lastSyncedAt,
    Expression<int>? rowid,
  }) {
    return RawValuesInsertable({
      if (localUserKey != null) 'local_user_key': localUserKey,
      if (membershipId != null) 'membership_id': membershipId,
      if (academicYearKey != null) 'academic_year_key': academicYearKey,
      if (resourceId != null) 'resource_id': resourceId,
      if (payloadJson != null) 'payload_json': payloadJson,
      if (isHistorical != null) 'is_historical': isHistorical,
      if (cachedAt != null) 'cached_at': cachedAt,
      if (lastSyncedAt != null) 'last_synced_at': lastSyncedAt,
      if (rowid != null) 'rowid': rowid,
    });
  }

  CachedContextsCompanion copyWith(
      {Value<String>? localUserKey,
      Value<int>? membershipId,
      Value<String>? academicYearKey,
      Value<String>? resourceId,
      Value<String>? payloadJson,
      Value<bool>? isHistorical,
      Value<DateTime>? cachedAt,
      Value<DateTime>? lastSyncedAt,
      Value<int>? rowid}) {
    return CachedContextsCompanion(
      localUserKey: localUserKey ?? this.localUserKey,
      membershipId: membershipId ?? this.membershipId,
      academicYearKey: academicYearKey ?? this.academicYearKey,
      resourceId: resourceId ?? this.resourceId,
      payloadJson: payloadJson ?? this.payloadJson,
      isHistorical: isHistorical ?? this.isHistorical,
      cachedAt: cachedAt ?? this.cachedAt,
      lastSyncedAt: lastSyncedAt ?? this.lastSyncedAt,
      rowid: rowid ?? this.rowid,
    );
  }

  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    if (localUserKey.present) {
      map['local_user_key'] = Variable<String>(localUserKey.value);
    }
    if (membershipId.present) {
      map['membership_id'] = Variable<int>(membershipId.value);
    }
    if (academicYearKey.present) {
      map['academic_year_key'] = Variable<String>(academicYearKey.value);
    }
    if (resourceId.present) {
      map['resource_id'] = Variable<String>(resourceId.value);
    }
    if (payloadJson.present) {
      map['payload_json'] = Variable<String>(payloadJson.value);
    }
    if (isHistorical.present) {
      map['is_historical'] = Variable<bool>(isHistorical.value);
    }
    if (cachedAt.present) {
      map['cached_at'] = Variable<DateTime>(cachedAt.value);
    }
    if (lastSyncedAt.present) {
      map['last_synced_at'] = Variable<DateTime>(lastSyncedAt.value);
    }
    if (rowid.present) {
      map['rowid'] = Variable<int>(rowid.value);
    }
    return map;
  }

  @override
  String toString() {
    return (StringBuffer('CachedContextsCompanion(')
          ..write('localUserKey: $localUserKey, ')
          ..write('membershipId: $membershipId, ')
          ..write('academicYearKey: $academicYearKey, ')
          ..write('resourceId: $resourceId, ')
          ..write('payloadJson: $payloadJson, ')
          ..write('isHistorical: $isHistorical, ')
          ..write('cachedAt: $cachedAt, ')
          ..write('lastSyncedAt: $lastSyncedAt, ')
          ..write('rowid: $rowid')
          ..write(')'))
        .toString();
  }
}

class $CacheMetadataTable extends CacheMetadata
    with TableInfo<$CacheMetadataTable, CacheMetadataData> {
  @override
  final GeneratedDatabase attachedDatabase;
  final String? _alias;
  $CacheMetadataTable(this.attachedDatabase, [this._alias]);
  static const VerificationMeta _localUserKeyMeta =
      const VerificationMeta('localUserKey');
  @override
  late final GeneratedColumn<String> localUserKey = GeneratedColumn<String>(
      'local_user_key', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _membershipIdMeta =
      const VerificationMeta('membershipId');
  @override
  late final GeneratedColumn<int> membershipId = GeneratedColumn<int>(
      'membership_id', aliasedName, false,
      type: DriftSqlType.int, requiredDuringInsert: true);
  static const VerificationMeta _academicYearKeyMeta =
      const VerificationMeta('academicYearKey');
  @override
  late final GeneratedColumn<String> academicYearKey = GeneratedColumn<String>(
      'academic_year_key', aliasedName, false,
      type: DriftSqlType.string,
      requiredDuringInsert: false,
      defaultValue: const Constant(''));
  static const VerificationMeta _resourceTypeMeta =
      const VerificationMeta('resourceType');
  @override
  late final GeneratedColumn<String> resourceType = GeneratedColumn<String>(
      'resource_type', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _cachedAtMeta =
      const VerificationMeta('cachedAt');
  @override
  late final GeneratedColumn<DateTime> cachedAt = GeneratedColumn<DateTime>(
      'cached_at', aliasedName, false,
      type: DriftSqlType.dateTime, requiredDuringInsert: true);
  static const VerificationMeta _lastSyncedAtMeta =
      const VerificationMeta('lastSyncedAt');
  @override
  late final GeneratedColumn<DateTime> lastSyncedAt = GeneratedColumn<DateTime>(
      'last_synced_at', aliasedName, false,
      type: DriftSqlType.dateTime, requiredDuringInsert: true);
  @override
  List<GeneratedColumn> get $columns => [
        localUserKey,
        membershipId,
        academicYearKey,
        resourceType,
        cachedAt,
        lastSyncedAt
      ];
  @override
  String get aliasedName => _alias ?? actualTableName;
  @override
  String get actualTableName => $name;
  static const String $name = 'cache_metadata';
  @override
  VerificationContext validateIntegrity(Insertable<CacheMetadataData> instance,
      {bool isInserting = false}) {
    final context = VerificationContext();
    final data = instance.toColumns(true);
    if (data.containsKey('local_user_key')) {
      context.handle(
          _localUserKeyMeta,
          localUserKey.isAcceptableOrUnknown(
              data['local_user_key']!, _localUserKeyMeta));
    } else if (isInserting) {
      context.missing(_localUserKeyMeta);
    }
    if (data.containsKey('membership_id')) {
      context.handle(
          _membershipIdMeta,
          membershipId.isAcceptableOrUnknown(
              data['membership_id']!, _membershipIdMeta));
    } else if (isInserting) {
      context.missing(_membershipIdMeta);
    }
    if (data.containsKey('academic_year_key')) {
      context.handle(
          _academicYearKeyMeta,
          academicYearKey.isAcceptableOrUnknown(
              data['academic_year_key']!, _academicYearKeyMeta));
    }
    if (data.containsKey('resource_type')) {
      context.handle(
          _resourceTypeMeta,
          resourceType.isAcceptableOrUnknown(
              data['resource_type']!, _resourceTypeMeta));
    } else if (isInserting) {
      context.missing(_resourceTypeMeta);
    }
    if (data.containsKey('cached_at')) {
      context.handle(_cachedAtMeta,
          cachedAt.isAcceptableOrUnknown(data['cached_at']!, _cachedAtMeta));
    } else if (isInserting) {
      context.missing(_cachedAtMeta);
    }
    if (data.containsKey('last_synced_at')) {
      context.handle(
          _lastSyncedAtMeta,
          lastSyncedAt.isAcceptableOrUnknown(
              data['last_synced_at']!, _lastSyncedAtMeta));
    } else if (isInserting) {
      context.missing(_lastSyncedAtMeta);
    }
    return context;
  }

  @override
  Set<GeneratedColumn> get $primaryKey =>
      {localUserKey, membershipId, academicYearKey, resourceType};
  @override
  CacheMetadataData map(Map<String, dynamic> data, {String? tablePrefix}) {
    final effectivePrefix = tablePrefix != null ? '$tablePrefix.' : '';
    return CacheMetadataData(
      localUserKey: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}local_user_key'])!,
      membershipId: attachedDatabase.typeMapping
          .read(DriftSqlType.int, data['${effectivePrefix}membership_id'])!,
      academicYearKey: attachedDatabase.typeMapping.read(
          DriftSqlType.string, data['${effectivePrefix}academic_year_key'])!,
      resourceType: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}resource_type'])!,
      cachedAt: attachedDatabase.typeMapping
          .read(DriftSqlType.dateTime, data['${effectivePrefix}cached_at'])!,
      lastSyncedAt: attachedDatabase.typeMapping.read(
          DriftSqlType.dateTime, data['${effectivePrefix}last_synced_at'])!,
    );
  }

  @override
  $CacheMetadataTable createAlias(String alias) {
    return $CacheMetadataTable(attachedDatabase, alias);
  }
}

class CacheMetadataData extends DataClass
    implements Insertable<CacheMetadataData> {
  final String localUserKey;
  final int membershipId;
  final String academicYearKey;
  final String resourceType;
  final DateTime cachedAt;
  final DateTime lastSyncedAt;
  const CacheMetadataData(
      {required this.localUserKey,
      required this.membershipId,
      required this.academicYearKey,
      required this.resourceType,
      required this.cachedAt,
      required this.lastSyncedAt});
  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    map['local_user_key'] = Variable<String>(localUserKey);
    map['membership_id'] = Variable<int>(membershipId);
    map['academic_year_key'] = Variable<String>(academicYearKey);
    map['resource_type'] = Variable<String>(resourceType);
    map['cached_at'] = Variable<DateTime>(cachedAt);
    map['last_synced_at'] = Variable<DateTime>(lastSyncedAt);
    return map;
  }

  CacheMetadataCompanion toCompanion(bool nullToAbsent) {
    return CacheMetadataCompanion(
      localUserKey: Value(localUserKey),
      membershipId: Value(membershipId),
      academicYearKey: Value(academicYearKey),
      resourceType: Value(resourceType),
      cachedAt: Value(cachedAt),
      lastSyncedAt: Value(lastSyncedAt),
    );
  }

  factory CacheMetadataData.fromJson(Map<String, dynamic> json,
      {ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return CacheMetadataData(
      localUserKey: serializer.fromJson<String>(json['localUserKey']),
      membershipId: serializer.fromJson<int>(json['membershipId']),
      academicYearKey: serializer.fromJson<String>(json['academicYearKey']),
      resourceType: serializer.fromJson<String>(json['resourceType']),
      cachedAt: serializer.fromJson<DateTime>(json['cachedAt']),
      lastSyncedAt: serializer.fromJson<DateTime>(json['lastSyncedAt']),
    );
  }
  @override
  Map<String, dynamic> toJson({ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return <String, dynamic>{
      'localUserKey': serializer.toJson<String>(localUserKey),
      'membershipId': serializer.toJson<int>(membershipId),
      'academicYearKey': serializer.toJson<String>(academicYearKey),
      'resourceType': serializer.toJson<String>(resourceType),
      'cachedAt': serializer.toJson<DateTime>(cachedAt),
      'lastSyncedAt': serializer.toJson<DateTime>(lastSyncedAt),
    };
  }

  CacheMetadataData copyWith(
          {String? localUserKey,
          int? membershipId,
          String? academicYearKey,
          String? resourceType,
          DateTime? cachedAt,
          DateTime? lastSyncedAt}) =>
      CacheMetadataData(
        localUserKey: localUserKey ?? this.localUserKey,
        membershipId: membershipId ?? this.membershipId,
        academicYearKey: academicYearKey ?? this.academicYearKey,
        resourceType: resourceType ?? this.resourceType,
        cachedAt: cachedAt ?? this.cachedAt,
        lastSyncedAt: lastSyncedAt ?? this.lastSyncedAt,
      );
  CacheMetadataData copyWithCompanion(CacheMetadataCompanion data) {
    return CacheMetadataData(
      localUserKey: data.localUserKey.present
          ? data.localUserKey.value
          : this.localUserKey,
      membershipId: data.membershipId.present
          ? data.membershipId.value
          : this.membershipId,
      academicYearKey: data.academicYearKey.present
          ? data.academicYearKey.value
          : this.academicYearKey,
      resourceType: data.resourceType.present
          ? data.resourceType.value
          : this.resourceType,
      cachedAt: data.cachedAt.present ? data.cachedAt.value : this.cachedAt,
      lastSyncedAt: data.lastSyncedAt.present
          ? data.lastSyncedAt.value
          : this.lastSyncedAt,
    );
  }

  @override
  String toString() {
    return (StringBuffer('CacheMetadataData(')
          ..write('localUserKey: $localUserKey, ')
          ..write('membershipId: $membershipId, ')
          ..write('academicYearKey: $academicYearKey, ')
          ..write('resourceType: $resourceType, ')
          ..write('cachedAt: $cachedAt, ')
          ..write('lastSyncedAt: $lastSyncedAt')
          ..write(')'))
        .toString();
  }

  @override
  int get hashCode => Object.hash(localUserKey, membershipId, academicYearKey,
      resourceType, cachedAt, lastSyncedAt);
  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      (other is CacheMetadataData &&
          other.localUserKey == this.localUserKey &&
          other.membershipId == this.membershipId &&
          other.academicYearKey == this.academicYearKey &&
          other.resourceType == this.resourceType &&
          other.cachedAt == this.cachedAt &&
          other.lastSyncedAt == this.lastSyncedAt);
}

class CacheMetadataCompanion extends UpdateCompanion<CacheMetadataData> {
  final Value<String> localUserKey;
  final Value<int> membershipId;
  final Value<String> academicYearKey;
  final Value<String> resourceType;
  final Value<DateTime> cachedAt;
  final Value<DateTime> lastSyncedAt;
  final Value<int> rowid;
  const CacheMetadataCompanion({
    this.localUserKey = const Value.absent(),
    this.membershipId = const Value.absent(),
    this.academicYearKey = const Value.absent(),
    this.resourceType = const Value.absent(),
    this.cachedAt = const Value.absent(),
    this.lastSyncedAt = const Value.absent(),
    this.rowid = const Value.absent(),
  });
  CacheMetadataCompanion.insert({
    required String localUserKey,
    required int membershipId,
    this.academicYearKey = const Value.absent(),
    required String resourceType,
    required DateTime cachedAt,
    required DateTime lastSyncedAt,
    this.rowid = const Value.absent(),
  })  : localUserKey = Value(localUserKey),
        membershipId = Value(membershipId),
        resourceType = Value(resourceType),
        cachedAt = Value(cachedAt),
        lastSyncedAt = Value(lastSyncedAt);
  static Insertable<CacheMetadataData> custom({
    Expression<String>? localUserKey,
    Expression<int>? membershipId,
    Expression<String>? academicYearKey,
    Expression<String>? resourceType,
    Expression<DateTime>? cachedAt,
    Expression<DateTime>? lastSyncedAt,
    Expression<int>? rowid,
  }) {
    return RawValuesInsertable({
      if (localUserKey != null) 'local_user_key': localUserKey,
      if (membershipId != null) 'membership_id': membershipId,
      if (academicYearKey != null) 'academic_year_key': academicYearKey,
      if (resourceType != null) 'resource_type': resourceType,
      if (cachedAt != null) 'cached_at': cachedAt,
      if (lastSyncedAt != null) 'last_synced_at': lastSyncedAt,
      if (rowid != null) 'rowid': rowid,
    });
  }

  CacheMetadataCompanion copyWith(
      {Value<String>? localUserKey,
      Value<int>? membershipId,
      Value<String>? academicYearKey,
      Value<String>? resourceType,
      Value<DateTime>? cachedAt,
      Value<DateTime>? lastSyncedAt,
      Value<int>? rowid}) {
    return CacheMetadataCompanion(
      localUserKey: localUserKey ?? this.localUserKey,
      membershipId: membershipId ?? this.membershipId,
      academicYearKey: academicYearKey ?? this.academicYearKey,
      resourceType: resourceType ?? this.resourceType,
      cachedAt: cachedAt ?? this.cachedAt,
      lastSyncedAt: lastSyncedAt ?? this.lastSyncedAt,
      rowid: rowid ?? this.rowid,
    );
  }

  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    if (localUserKey.present) {
      map['local_user_key'] = Variable<String>(localUserKey.value);
    }
    if (membershipId.present) {
      map['membership_id'] = Variable<int>(membershipId.value);
    }
    if (academicYearKey.present) {
      map['academic_year_key'] = Variable<String>(academicYearKey.value);
    }
    if (resourceType.present) {
      map['resource_type'] = Variable<String>(resourceType.value);
    }
    if (cachedAt.present) {
      map['cached_at'] = Variable<DateTime>(cachedAt.value);
    }
    if (lastSyncedAt.present) {
      map['last_synced_at'] = Variable<DateTime>(lastSyncedAt.value);
    }
    if (rowid.present) {
      map['rowid'] = Variable<int>(rowid.value);
    }
    return map;
  }

  @override
  String toString() {
    return (StringBuffer('CacheMetadataCompanion(')
          ..write('localUserKey: $localUserKey, ')
          ..write('membershipId: $membershipId, ')
          ..write('academicYearKey: $academicYearKey, ')
          ..write('resourceType: $resourceType, ')
          ..write('cachedAt: $cachedAt, ')
          ..write('lastSyncedAt: $lastSyncedAt, ')
          ..write('rowid: $rowid')
          ..write(')'))
        .toString();
  }
}

class $CachedTimetableDatasetsTable extends CachedTimetableDatasets
    with TableInfo<$CachedTimetableDatasetsTable, CachedTimetableDataset> {
  @override
  final GeneratedDatabase attachedDatabase;
  final String? _alias;
  $CachedTimetableDatasetsTable(this.attachedDatabase, [this._alias]);
  static const VerificationMeta _localUserKeyMeta =
      const VerificationMeta('localUserKey');
  @override
  late final GeneratedColumn<String> localUserKey = GeneratedColumn<String>(
      'local_user_key', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _membershipIdMeta =
      const VerificationMeta('membershipId');
  @override
  late final GeneratedColumn<int> membershipId = GeneratedColumn<int>(
      'membership_id', aliasedName, false,
      type: DriftSqlType.int, requiredDuringInsert: true);
  static const VerificationMeta _academicYearKeyMeta =
      const VerificationMeta('academicYearKey');
  @override
  late final GeneratedColumn<String> academicYearKey = GeneratedColumn<String>(
      'academic_year_key', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _datasetKeyMeta =
      const VerificationMeta('datasetKey');
  @override
  late final GeneratedColumn<String> datasetKey = GeneratedColumn<String>(
      'dataset_key', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _payloadJsonMeta =
      const VerificationMeta('payloadJson');
  @override
  late final GeneratedColumn<String> payloadJson = GeneratedColumn<String>(
      'payload_json', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _lastSyncedAtMeta =
      const VerificationMeta('lastSyncedAt');
  @override
  late final GeneratedColumn<DateTime> lastSyncedAt = GeneratedColumn<DateTime>(
      'last_synced_at', aliasedName, false,
      type: DriftSqlType.dateTime, requiredDuringInsert: true);
  @override
  List<GeneratedColumn> get $columns => [
        localUserKey,
        membershipId,
        academicYearKey,
        datasetKey,
        payloadJson,
        lastSyncedAt
      ];
  @override
  String get aliasedName => _alias ?? actualTableName;
  @override
  String get actualTableName => $name;
  static const String $name = 'cached_timetable_datasets';
  @override
  VerificationContext validateIntegrity(
      Insertable<CachedTimetableDataset> instance,
      {bool isInserting = false}) {
    final context = VerificationContext();
    final data = instance.toColumns(true);
    if (data.containsKey('local_user_key')) {
      context.handle(
          _localUserKeyMeta,
          localUserKey.isAcceptableOrUnknown(
              data['local_user_key']!, _localUserKeyMeta));
    } else if (isInserting) {
      context.missing(_localUserKeyMeta);
    }
    if (data.containsKey('membership_id')) {
      context.handle(
          _membershipIdMeta,
          membershipId.isAcceptableOrUnknown(
              data['membership_id']!, _membershipIdMeta));
    } else if (isInserting) {
      context.missing(_membershipIdMeta);
    }
    if (data.containsKey('academic_year_key')) {
      context.handle(
          _academicYearKeyMeta,
          academicYearKey.isAcceptableOrUnknown(
              data['academic_year_key']!, _academicYearKeyMeta));
    } else if (isInserting) {
      context.missing(_academicYearKeyMeta);
    }
    if (data.containsKey('dataset_key')) {
      context.handle(
          _datasetKeyMeta,
          datasetKey.isAcceptableOrUnknown(
              data['dataset_key']!, _datasetKeyMeta));
    } else if (isInserting) {
      context.missing(_datasetKeyMeta);
    }
    if (data.containsKey('payload_json')) {
      context.handle(
          _payloadJsonMeta,
          payloadJson.isAcceptableOrUnknown(
              data['payload_json']!, _payloadJsonMeta));
    } else if (isInserting) {
      context.missing(_payloadJsonMeta);
    }
    if (data.containsKey('last_synced_at')) {
      context.handle(
          _lastSyncedAtMeta,
          lastSyncedAt.isAcceptableOrUnknown(
              data['last_synced_at']!, _lastSyncedAtMeta));
    } else if (isInserting) {
      context.missing(_lastSyncedAtMeta);
    }
    return context;
  }

  @override
  Set<GeneratedColumn> get $primaryKey =>
      {localUserKey, membershipId, academicYearKey, datasetKey};
  @override
  CachedTimetableDataset map(Map<String, dynamic> data, {String? tablePrefix}) {
    final effectivePrefix = tablePrefix != null ? '$tablePrefix.' : '';
    return CachedTimetableDataset(
      localUserKey: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}local_user_key'])!,
      membershipId: attachedDatabase.typeMapping
          .read(DriftSqlType.int, data['${effectivePrefix}membership_id'])!,
      academicYearKey: attachedDatabase.typeMapping.read(
          DriftSqlType.string, data['${effectivePrefix}academic_year_key'])!,
      datasetKey: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}dataset_key'])!,
      payloadJson: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}payload_json'])!,
      lastSyncedAt: attachedDatabase.typeMapping.read(
          DriftSqlType.dateTime, data['${effectivePrefix}last_synced_at'])!,
    );
  }

  @override
  $CachedTimetableDatasetsTable createAlias(String alias) {
    return $CachedTimetableDatasetsTable(attachedDatabase, alias);
  }
}

class CachedTimetableDataset extends DataClass
    implements Insertable<CachedTimetableDataset> {
  final String localUserKey;
  final int membershipId;
  final String academicYearKey;
  final String datasetKey;
  final String payloadJson;
  final DateTime lastSyncedAt;
  const CachedTimetableDataset(
      {required this.localUserKey,
      required this.membershipId,
      required this.academicYearKey,
      required this.datasetKey,
      required this.payloadJson,
      required this.lastSyncedAt});
  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    map['local_user_key'] = Variable<String>(localUserKey);
    map['membership_id'] = Variable<int>(membershipId);
    map['academic_year_key'] = Variable<String>(academicYearKey);
    map['dataset_key'] = Variable<String>(datasetKey);
    map['payload_json'] = Variable<String>(payloadJson);
    map['last_synced_at'] = Variable<DateTime>(lastSyncedAt);
    return map;
  }

  CachedTimetableDatasetsCompanion toCompanion(bool nullToAbsent) {
    return CachedTimetableDatasetsCompanion(
      localUserKey: Value(localUserKey),
      membershipId: Value(membershipId),
      academicYearKey: Value(academicYearKey),
      datasetKey: Value(datasetKey),
      payloadJson: Value(payloadJson),
      lastSyncedAt: Value(lastSyncedAt),
    );
  }

  factory CachedTimetableDataset.fromJson(Map<String, dynamic> json,
      {ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return CachedTimetableDataset(
      localUserKey: serializer.fromJson<String>(json['localUserKey']),
      membershipId: serializer.fromJson<int>(json['membershipId']),
      academicYearKey: serializer.fromJson<String>(json['academicYearKey']),
      datasetKey: serializer.fromJson<String>(json['datasetKey']),
      payloadJson: serializer.fromJson<String>(json['payloadJson']),
      lastSyncedAt: serializer.fromJson<DateTime>(json['lastSyncedAt']),
    );
  }
  @override
  Map<String, dynamic> toJson({ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return <String, dynamic>{
      'localUserKey': serializer.toJson<String>(localUserKey),
      'membershipId': serializer.toJson<int>(membershipId),
      'academicYearKey': serializer.toJson<String>(academicYearKey),
      'datasetKey': serializer.toJson<String>(datasetKey),
      'payloadJson': serializer.toJson<String>(payloadJson),
      'lastSyncedAt': serializer.toJson<DateTime>(lastSyncedAt),
    };
  }

  CachedTimetableDataset copyWith(
          {String? localUserKey,
          int? membershipId,
          String? academicYearKey,
          String? datasetKey,
          String? payloadJson,
          DateTime? lastSyncedAt}) =>
      CachedTimetableDataset(
        localUserKey: localUserKey ?? this.localUserKey,
        membershipId: membershipId ?? this.membershipId,
        academicYearKey: academicYearKey ?? this.academicYearKey,
        datasetKey: datasetKey ?? this.datasetKey,
        payloadJson: payloadJson ?? this.payloadJson,
        lastSyncedAt: lastSyncedAt ?? this.lastSyncedAt,
      );
  CachedTimetableDataset copyWithCompanion(
      CachedTimetableDatasetsCompanion data) {
    return CachedTimetableDataset(
      localUserKey: data.localUserKey.present
          ? data.localUserKey.value
          : this.localUserKey,
      membershipId: data.membershipId.present
          ? data.membershipId.value
          : this.membershipId,
      academicYearKey: data.academicYearKey.present
          ? data.academicYearKey.value
          : this.academicYearKey,
      datasetKey:
          data.datasetKey.present ? data.datasetKey.value : this.datasetKey,
      payloadJson:
          data.payloadJson.present ? data.payloadJson.value : this.payloadJson,
      lastSyncedAt: data.lastSyncedAt.present
          ? data.lastSyncedAt.value
          : this.lastSyncedAt,
    );
  }

  @override
  String toString() {
    return (StringBuffer('CachedTimetableDataset(')
          ..write('localUserKey: $localUserKey, ')
          ..write('membershipId: $membershipId, ')
          ..write('academicYearKey: $academicYearKey, ')
          ..write('datasetKey: $datasetKey, ')
          ..write('payloadJson: $payloadJson, ')
          ..write('lastSyncedAt: $lastSyncedAt')
          ..write(')'))
        .toString();
  }

  @override
  int get hashCode => Object.hash(localUserKey, membershipId, academicYearKey,
      datasetKey, payloadJson, lastSyncedAt);
  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      (other is CachedTimetableDataset &&
          other.localUserKey == this.localUserKey &&
          other.membershipId == this.membershipId &&
          other.academicYearKey == this.academicYearKey &&
          other.datasetKey == this.datasetKey &&
          other.payloadJson == this.payloadJson &&
          other.lastSyncedAt == this.lastSyncedAt);
}

class CachedTimetableDatasetsCompanion
    extends UpdateCompanion<CachedTimetableDataset> {
  final Value<String> localUserKey;
  final Value<int> membershipId;
  final Value<String> academicYearKey;
  final Value<String> datasetKey;
  final Value<String> payloadJson;
  final Value<DateTime> lastSyncedAt;
  final Value<int> rowid;
  const CachedTimetableDatasetsCompanion({
    this.localUserKey = const Value.absent(),
    this.membershipId = const Value.absent(),
    this.academicYearKey = const Value.absent(),
    this.datasetKey = const Value.absent(),
    this.payloadJson = const Value.absent(),
    this.lastSyncedAt = const Value.absent(),
    this.rowid = const Value.absent(),
  });
  CachedTimetableDatasetsCompanion.insert({
    required String localUserKey,
    required int membershipId,
    required String academicYearKey,
    required String datasetKey,
    required String payloadJson,
    required DateTime lastSyncedAt,
    this.rowid = const Value.absent(),
  })  : localUserKey = Value(localUserKey),
        membershipId = Value(membershipId),
        academicYearKey = Value(academicYearKey),
        datasetKey = Value(datasetKey),
        payloadJson = Value(payloadJson),
        lastSyncedAt = Value(lastSyncedAt);
  static Insertable<CachedTimetableDataset> custom({
    Expression<String>? localUserKey,
    Expression<int>? membershipId,
    Expression<String>? academicYearKey,
    Expression<String>? datasetKey,
    Expression<String>? payloadJson,
    Expression<DateTime>? lastSyncedAt,
    Expression<int>? rowid,
  }) {
    return RawValuesInsertable({
      if (localUserKey != null) 'local_user_key': localUserKey,
      if (membershipId != null) 'membership_id': membershipId,
      if (academicYearKey != null) 'academic_year_key': academicYearKey,
      if (datasetKey != null) 'dataset_key': datasetKey,
      if (payloadJson != null) 'payload_json': payloadJson,
      if (lastSyncedAt != null) 'last_synced_at': lastSyncedAt,
      if (rowid != null) 'rowid': rowid,
    });
  }

  CachedTimetableDatasetsCompanion copyWith(
      {Value<String>? localUserKey,
      Value<int>? membershipId,
      Value<String>? academicYearKey,
      Value<String>? datasetKey,
      Value<String>? payloadJson,
      Value<DateTime>? lastSyncedAt,
      Value<int>? rowid}) {
    return CachedTimetableDatasetsCompanion(
      localUserKey: localUserKey ?? this.localUserKey,
      membershipId: membershipId ?? this.membershipId,
      academicYearKey: academicYearKey ?? this.academicYearKey,
      datasetKey: datasetKey ?? this.datasetKey,
      payloadJson: payloadJson ?? this.payloadJson,
      lastSyncedAt: lastSyncedAt ?? this.lastSyncedAt,
      rowid: rowid ?? this.rowid,
    );
  }

  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    if (localUserKey.present) {
      map['local_user_key'] = Variable<String>(localUserKey.value);
    }
    if (membershipId.present) {
      map['membership_id'] = Variable<int>(membershipId.value);
    }
    if (academicYearKey.present) {
      map['academic_year_key'] = Variable<String>(academicYearKey.value);
    }
    if (datasetKey.present) {
      map['dataset_key'] = Variable<String>(datasetKey.value);
    }
    if (payloadJson.present) {
      map['payload_json'] = Variable<String>(payloadJson.value);
    }
    if (lastSyncedAt.present) {
      map['last_synced_at'] = Variable<DateTime>(lastSyncedAt.value);
    }
    if (rowid.present) {
      map['rowid'] = Variable<int>(rowid.value);
    }
    return map;
  }

  @override
  String toString() {
    return (StringBuffer('CachedTimetableDatasetsCompanion(')
          ..write('localUserKey: $localUserKey, ')
          ..write('membershipId: $membershipId, ')
          ..write('academicYearKey: $academicYearKey, ')
          ..write('datasetKey: $datasetKey, ')
          ..write('payloadJson: $payloadJson, ')
          ..write('lastSyncedAt: $lastSyncedAt, ')
          ..write('rowid: $rowid')
          ..write(')'))
        .toString();
  }
}

abstract class _$AppDatabase extends GeneratedDatabase {
  _$AppDatabase(QueryExecutor e) : super(e);
  $AppDatabaseManager get managers => $AppDatabaseManager(this);
  late final $CachedContextsTable cachedContexts = $CachedContextsTable(this);
  late final $CacheMetadataTable cacheMetadata = $CacheMetadataTable(this);
  late final $CachedTimetableDatasetsTable cachedTimetableDatasets =
      $CachedTimetableDatasetsTable(this);
  @override
  Iterable<TableInfo<Table, Object?>> get allTables =>
      allSchemaEntities.whereType<TableInfo<Table, Object?>>();
  @override
  List<DatabaseSchemaEntity> get allSchemaEntities =>
      [cachedContexts, cacheMetadata, cachedTimetableDatasets];
}

typedef $$CachedContextsTableCreateCompanionBuilder = CachedContextsCompanion
    Function({
  required String localUserKey,
  required int membershipId,
  Value<String> academicYearKey,
  required String resourceId,
  required String payloadJson,
  Value<bool> isHistorical,
  required DateTime cachedAt,
  required DateTime lastSyncedAt,
  Value<int> rowid,
});
typedef $$CachedContextsTableUpdateCompanionBuilder = CachedContextsCompanion
    Function({
  Value<String> localUserKey,
  Value<int> membershipId,
  Value<String> academicYearKey,
  Value<String> resourceId,
  Value<String> payloadJson,
  Value<bool> isHistorical,
  Value<DateTime> cachedAt,
  Value<DateTime> lastSyncedAt,
  Value<int> rowid,
});

class $$CachedContextsTableFilterComposer
    extends Composer<_$AppDatabase, $CachedContextsTable> {
  $$CachedContextsTableFilterComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnFilters<String> get localUserKey => $composableBuilder(
      column: $table.localUserKey, builder: (column) => ColumnFilters(column));

  ColumnFilters<int> get membershipId => $composableBuilder(
      column: $table.membershipId, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get academicYearKey => $composableBuilder(
      column: $table.academicYearKey,
      builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get resourceId => $composableBuilder(
      column: $table.resourceId, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get payloadJson => $composableBuilder(
      column: $table.payloadJson, builder: (column) => ColumnFilters(column));

  ColumnFilters<bool> get isHistorical => $composableBuilder(
      column: $table.isHistorical, builder: (column) => ColumnFilters(column));

  ColumnFilters<DateTime> get cachedAt => $composableBuilder(
      column: $table.cachedAt, builder: (column) => ColumnFilters(column));

  ColumnFilters<DateTime> get lastSyncedAt => $composableBuilder(
      column: $table.lastSyncedAt, builder: (column) => ColumnFilters(column));
}

class $$CachedContextsTableOrderingComposer
    extends Composer<_$AppDatabase, $CachedContextsTable> {
  $$CachedContextsTableOrderingComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnOrderings<String> get localUserKey => $composableBuilder(
      column: $table.localUserKey,
      builder: (column) => ColumnOrderings(column));

  ColumnOrderings<int> get membershipId => $composableBuilder(
      column: $table.membershipId,
      builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get academicYearKey => $composableBuilder(
      column: $table.academicYearKey,
      builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get resourceId => $composableBuilder(
      column: $table.resourceId, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get payloadJson => $composableBuilder(
      column: $table.payloadJson, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<bool> get isHistorical => $composableBuilder(
      column: $table.isHistorical,
      builder: (column) => ColumnOrderings(column));

  ColumnOrderings<DateTime> get cachedAt => $composableBuilder(
      column: $table.cachedAt, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<DateTime> get lastSyncedAt => $composableBuilder(
      column: $table.lastSyncedAt,
      builder: (column) => ColumnOrderings(column));
}

class $$CachedContextsTableAnnotationComposer
    extends Composer<_$AppDatabase, $CachedContextsTable> {
  $$CachedContextsTableAnnotationComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  GeneratedColumn<String> get localUserKey => $composableBuilder(
      column: $table.localUserKey, builder: (column) => column);

  GeneratedColumn<int> get membershipId => $composableBuilder(
      column: $table.membershipId, builder: (column) => column);

  GeneratedColumn<String> get academicYearKey => $composableBuilder(
      column: $table.academicYearKey, builder: (column) => column);

  GeneratedColumn<String> get resourceId => $composableBuilder(
      column: $table.resourceId, builder: (column) => column);

  GeneratedColumn<String> get payloadJson => $composableBuilder(
      column: $table.payloadJson, builder: (column) => column);

  GeneratedColumn<bool> get isHistorical => $composableBuilder(
      column: $table.isHistorical, builder: (column) => column);

  GeneratedColumn<DateTime> get cachedAt =>
      $composableBuilder(column: $table.cachedAt, builder: (column) => column);

  GeneratedColumn<DateTime> get lastSyncedAt => $composableBuilder(
      column: $table.lastSyncedAt, builder: (column) => column);
}

class $$CachedContextsTableTableManager extends RootTableManager<
    _$AppDatabase,
    $CachedContextsTable,
    CachedContext,
    $$CachedContextsTableFilterComposer,
    $$CachedContextsTableOrderingComposer,
    $$CachedContextsTableAnnotationComposer,
    $$CachedContextsTableCreateCompanionBuilder,
    $$CachedContextsTableUpdateCompanionBuilder,
    (
      CachedContext,
      BaseReferences<_$AppDatabase, $CachedContextsTable, CachedContext>
    ),
    CachedContext,
    PrefetchHooks Function()> {
  $$CachedContextsTableTableManager(
      _$AppDatabase db, $CachedContextsTable table)
      : super(TableManagerState(
          db: db,
          table: table,
          createFilteringComposer: () =>
              $$CachedContextsTableFilterComposer($db: db, $table: table),
          createOrderingComposer: () =>
              $$CachedContextsTableOrderingComposer($db: db, $table: table),
          createComputedFieldComposer: () =>
              $$CachedContextsTableAnnotationComposer($db: db, $table: table),
          updateCompanionCallback: ({
            Value<String> localUserKey = const Value.absent(),
            Value<int> membershipId = const Value.absent(),
            Value<String> academicYearKey = const Value.absent(),
            Value<String> resourceId = const Value.absent(),
            Value<String> payloadJson = const Value.absent(),
            Value<bool> isHistorical = const Value.absent(),
            Value<DateTime> cachedAt = const Value.absent(),
            Value<DateTime> lastSyncedAt = const Value.absent(),
            Value<int> rowid = const Value.absent(),
          }) =>
              CachedContextsCompanion(
            localUserKey: localUserKey,
            membershipId: membershipId,
            academicYearKey: academicYearKey,
            resourceId: resourceId,
            payloadJson: payloadJson,
            isHistorical: isHistorical,
            cachedAt: cachedAt,
            lastSyncedAt: lastSyncedAt,
            rowid: rowid,
          ),
          createCompanionCallback: ({
            required String localUserKey,
            required int membershipId,
            Value<String> academicYearKey = const Value.absent(),
            required String resourceId,
            required String payloadJson,
            Value<bool> isHistorical = const Value.absent(),
            required DateTime cachedAt,
            required DateTime lastSyncedAt,
            Value<int> rowid = const Value.absent(),
          }) =>
              CachedContextsCompanion.insert(
            localUserKey: localUserKey,
            membershipId: membershipId,
            academicYearKey: academicYearKey,
            resourceId: resourceId,
            payloadJson: payloadJson,
            isHistorical: isHistorical,
            cachedAt: cachedAt,
            lastSyncedAt: lastSyncedAt,
            rowid: rowid,
          ),
          withReferenceMapper: (p0) => p0
              .map((e) => (e.readTable(table), BaseReferences(db, table, e)))
              .toList(),
          prefetchHooksCallback: null,
        ));
}

typedef $$CachedContextsTableProcessedTableManager = ProcessedTableManager<
    _$AppDatabase,
    $CachedContextsTable,
    CachedContext,
    $$CachedContextsTableFilterComposer,
    $$CachedContextsTableOrderingComposer,
    $$CachedContextsTableAnnotationComposer,
    $$CachedContextsTableCreateCompanionBuilder,
    $$CachedContextsTableUpdateCompanionBuilder,
    (
      CachedContext,
      BaseReferences<_$AppDatabase, $CachedContextsTable, CachedContext>
    ),
    CachedContext,
    PrefetchHooks Function()>;
typedef $$CacheMetadataTableCreateCompanionBuilder = CacheMetadataCompanion
    Function({
  required String localUserKey,
  required int membershipId,
  Value<String> academicYearKey,
  required String resourceType,
  required DateTime cachedAt,
  required DateTime lastSyncedAt,
  Value<int> rowid,
});
typedef $$CacheMetadataTableUpdateCompanionBuilder = CacheMetadataCompanion
    Function({
  Value<String> localUserKey,
  Value<int> membershipId,
  Value<String> academicYearKey,
  Value<String> resourceType,
  Value<DateTime> cachedAt,
  Value<DateTime> lastSyncedAt,
  Value<int> rowid,
});

class $$CacheMetadataTableFilterComposer
    extends Composer<_$AppDatabase, $CacheMetadataTable> {
  $$CacheMetadataTableFilterComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnFilters<String> get localUserKey => $composableBuilder(
      column: $table.localUserKey, builder: (column) => ColumnFilters(column));

  ColumnFilters<int> get membershipId => $composableBuilder(
      column: $table.membershipId, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get academicYearKey => $composableBuilder(
      column: $table.academicYearKey,
      builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get resourceType => $composableBuilder(
      column: $table.resourceType, builder: (column) => ColumnFilters(column));

  ColumnFilters<DateTime> get cachedAt => $composableBuilder(
      column: $table.cachedAt, builder: (column) => ColumnFilters(column));

  ColumnFilters<DateTime> get lastSyncedAt => $composableBuilder(
      column: $table.lastSyncedAt, builder: (column) => ColumnFilters(column));
}

class $$CacheMetadataTableOrderingComposer
    extends Composer<_$AppDatabase, $CacheMetadataTable> {
  $$CacheMetadataTableOrderingComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnOrderings<String> get localUserKey => $composableBuilder(
      column: $table.localUserKey,
      builder: (column) => ColumnOrderings(column));

  ColumnOrderings<int> get membershipId => $composableBuilder(
      column: $table.membershipId,
      builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get academicYearKey => $composableBuilder(
      column: $table.academicYearKey,
      builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get resourceType => $composableBuilder(
      column: $table.resourceType,
      builder: (column) => ColumnOrderings(column));

  ColumnOrderings<DateTime> get cachedAt => $composableBuilder(
      column: $table.cachedAt, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<DateTime> get lastSyncedAt => $composableBuilder(
      column: $table.lastSyncedAt,
      builder: (column) => ColumnOrderings(column));
}

class $$CacheMetadataTableAnnotationComposer
    extends Composer<_$AppDatabase, $CacheMetadataTable> {
  $$CacheMetadataTableAnnotationComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  GeneratedColumn<String> get localUserKey => $composableBuilder(
      column: $table.localUserKey, builder: (column) => column);

  GeneratedColumn<int> get membershipId => $composableBuilder(
      column: $table.membershipId, builder: (column) => column);

  GeneratedColumn<String> get academicYearKey => $composableBuilder(
      column: $table.academicYearKey, builder: (column) => column);

  GeneratedColumn<String> get resourceType => $composableBuilder(
      column: $table.resourceType, builder: (column) => column);

  GeneratedColumn<DateTime> get cachedAt =>
      $composableBuilder(column: $table.cachedAt, builder: (column) => column);

  GeneratedColumn<DateTime> get lastSyncedAt => $composableBuilder(
      column: $table.lastSyncedAt, builder: (column) => column);
}

class $$CacheMetadataTableTableManager extends RootTableManager<
    _$AppDatabase,
    $CacheMetadataTable,
    CacheMetadataData,
    $$CacheMetadataTableFilterComposer,
    $$CacheMetadataTableOrderingComposer,
    $$CacheMetadataTableAnnotationComposer,
    $$CacheMetadataTableCreateCompanionBuilder,
    $$CacheMetadataTableUpdateCompanionBuilder,
    (
      CacheMetadataData,
      BaseReferences<_$AppDatabase, $CacheMetadataTable, CacheMetadataData>
    ),
    CacheMetadataData,
    PrefetchHooks Function()> {
  $$CacheMetadataTableTableManager(_$AppDatabase db, $CacheMetadataTable table)
      : super(TableManagerState(
          db: db,
          table: table,
          createFilteringComposer: () =>
              $$CacheMetadataTableFilterComposer($db: db, $table: table),
          createOrderingComposer: () =>
              $$CacheMetadataTableOrderingComposer($db: db, $table: table),
          createComputedFieldComposer: () =>
              $$CacheMetadataTableAnnotationComposer($db: db, $table: table),
          updateCompanionCallback: ({
            Value<String> localUserKey = const Value.absent(),
            Value<int> membershipId = const Value.absent(),
            Value<String> academicYearKey = const Value.absent(),
            Value<String> resourceType = const Value.absent(),
            Value<DateTime> cachedAt = const Value.absent(),
            Value<DateTime> lastSyncedAt = const Value.absent(),
            Value<int> rowid = const Value.absent(),
          }) =>
              CacheMetadataCompanion(
            localUserKey: localUserKey,
            membershipId: membershipId,
            academicYearKey: academicYearKey,
            resourceType: resourceType,
            cachedAt: cachedAt,
            lastSyncedAt: lastSyncedAt,
            rowid: rowid,
          ),
          createCompanionCallback: ({
            required String localUserKey,
            required int membershipId,
            Value<String> academicYearKey = const Value.absent(),
            required String resourceType,
            required DateTime cachedAt,
            required DateTime lastSyncedAt,
            Value<int> rowid = const Value.absent(),
          }) =>
              CacheMetadataCompanion.insert(
            localUserKey: localUserKey,
            membershipId: membershipId,
            academicYearKey: academicYearKey,
            resourceType: resourceType,
            cachedAt: cachedAt,
            lastSyncedAt: lastSyncedAt,
            rowid: rowid,
          ),
          withReferenceMapper: (p0) => p0
              .map((e) => (e.readTable(table), BaseReferences(db, table, e)))
              .toList(),
          prefetchHooksCallback: null,
        ));
}

typedef $$CacheMetadataTableProcessedTableManager = ProcessedTableManager<
    _$AppDatabase,
    $CacheMetadataTable,
    CacheMetadataData,
    $$CacheMetadataTableFilterComposer,
    $$CacheMetadataTableOrderingComposer,
    $$CacheMetadataTableAnnotationComposer,
    $$CacheMetadataTableCreateCompanionBuilder,
    $$CacheMetadataTableUpdateCompanionBuilder,
    (
      CacheMetadataData,
      BaseReferences<_$AppDatabase, $CacheMetadataTable, CacheMetadataData>
    ),
    CacheMetadataData,
    PrefetchHooks Function()>;
typedef $$CachedTimetableDatasetsTableCreateCompanionBuilder
    = CachedTimetableDatasetsCompanion Function({
  required String localUserKey,
  required int membershipId,
  required String academicYearKey,
  required String datasetKey,
  required String payloadJson,
  required DateTime lastSyncedAt,
  Value<int> rowid,
});
typedef $$CachedTimetableDatasetsTableUpdateCompanionBuilder
    = CachedTimetableDatasetsCompanion Function({
  Value<String> localUserKey,
  Value<int> membershipId,
  Value<String> academicYearKey,
  Value<String> datasetKey,
  Value<String> payloadJson,
  Value<DateTime> lastSyncedAt,
  Value<int> rowid,
});

class $$CachedTimetableDatasetsTableFilterComposer
    extends Composer<_$AppDatabase, $CachedTimetableDatasetsTable> {
  $$CachedTimetableDatasetsTableFilterComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnFilters<String> get localUserKey => $composableBuilder(
      column: $table.localUserKey, builder: (column) => ColumnFilters(column));

  ColumnFilters<int> get membershipId => $composableBuilder(
      column: $table.membershipId, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get academicYearKey => $composableBuilder(
      column: $table.academicYearKey,
      builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get datasetKey => $composableBuilder(
      column: $table.datasetKey, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get payloadJson => $composableBuilder(
      column: $table.payloadJson, builder: (column) => ColumnFilters(column));

  ColumnFilters<DateTime> get lastSyncedAt => $composableBuilder(
      column: $table.lastSyncedAt, builder: (column) => ColumnFilters(column));
}

class $$CachedTimetableDatasetsTableOrderingComposer
    extends Composer<_$AppDatabase, $CachedTimetableDatasetsTable> {
  $$CachedTimetableDatasetsTableOrderingComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnOrderings<String> get localUserKey => $composableBuilder(
      column: $table.localUserKey,
      builder: (column) => ColumnOrderings(column));

  ColumnOrderings<int> get membershipId => $composableBuilder(
      column: $table.membershipId,
      builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get academicYearKey => $composableBuilder(
      column: $table.academicYearKey,
      builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get datasetKey => $composableBuilder(
      column: $table.datasetKey, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get payloadJson => $composableBuilder(
      column: $table.payloadJson, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<DateTime> get lastSyncedAt => $composableBuilder(
      column: $table.lastSyncedAt,
      builder: (column) => ColumnOrderings(column));
}

class $$CachedTimetableDatasetsTableAnnotationComposer
    extends Composer<_$AppDatabase, $CachedTimetableDatasetsTable> {
  $$CachedTimetableDatasetsTableAnnotationComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  GeneratedColumn<String> get localUserKey => $composableBuilder(
      column: $table.localUserKey, builder: (column) => column);

  GeneratedColumn<int> get membershipId => $composableBuilder(
      column: $table.membershipId, builder: (column) => column);

  GeneratedColumn<String> get academicYearKey => $composableBuilder(
      column: $table.academicYearKey, builder: (column) => column);

  GeneratedColumn<String> get datasetKey => $composableBuilder(
      column: $table.datasetKey, builder: (column) => column);

  GeneratedColumn<String> get payloadJson => $composableBuilder(
      column: $table.payloadJson, builder: (column) => column);

  GeneratedColumn<DateTime> get lastSyncedAt => $composableBuilder(
      column: $table.lastSyncedAt, builder: (column) => column);
}

class $$CachedTimetableDatasetsTableTableManager extends RootTableManager<
    _$AppDatabase,
    $CachedTimetableDatasetsTable,
    CachedTimetableDataset,
    $$CachedTimetableDatasetsTableFilterComposer,
    $$CachedTimetableDatasetsTableOrderingComposer,
    $$CachedTimetableDatasetsTableAnnotationComposer,
    $$CachedTimetableDatasetsTableCreateCompanionBuilder,
    $$CachedTimetableDatasetsTableUpdateCompanionBuilder,
    (
      CachedTimetableDataset,
      BaseReferences<_$AppDatabase, $CachedTimetableDatasetsTable,
          CachedTimetableDataset>
    ),
    CachedTimetableDataset,
    PrefetchHooks Function()> {
  $$CachedTimetableDatasetsTableTableManager(
      _$AppDatabase db, $CachedTimetableDatasetsTable table)
      : super(TableManagerState(
          db: db,
          table: table,
          createFilteringComposer: () =>
              $$CachedTimetableDatasetsTableFilterComposer(
                  $db: db, $table: table),
          createOrderingComposer: () =>
              $$CachedTimetableDatasetsTableOrderingComposer(
                  $db: db, $table: table),
          createComputedFieldComposer: () =>
              $$CachedTimetableDatasetsTableAnnotationComposer(
                  $db: db, $table: table),
          updateCompanionCallback: ({
            Value<String> localUserKey = const Value.absent(),
            Value<int> membershipId = const Value.absent(),
            Value<String> academicYearKey = const Value.absent(),
            Value<String> datasetKey = const Value.absent(),
            Value<String> payloadJson = const Value.absent(),
            Value<DateTime> lastSyncedAt = const Value.absent(),
            Value<int> rowid = const Value.absent(),
          }) =>
              CachedTimetableDatasetsCompanion(
            localUserKey: localUserKey,
            membershipId: membershipId,
            academicYearKey: academicYearKey,
            datasetKey: datasetKey,
            payloadJson: payloadJson,
            lastSyncedAt: lastSyncedAt,
            rowid: rowid,
          ),
          createCompanionCallback: ({
            required String localUserKey,
            required int membershipId,
            required String academicYearKey,
            required String datasetKey,
            required String payloadJson,
            required DateTime lastSyncedAt,
            Value<int> rowid = const Value.absent(),
          }) =>
              CachedTimetableDatasetsCompanion.insert(
            localUserKey: localUserKey,
            membershipId: membershipId,
            academicYearKey: academicYearKey,
            datasetKey: datasetKey,
            payloadJson: payloadJson,
            lastSyncedAt: lastSyncedAt,
            rowid: rowid,
          ),
          withReferenceMapper: (p0) => p0
              .map((e) => (e.readTable(table), BaseReferences(db, table, e)))
              .toList(),
          prefetchHooksCallback: null,
        ));
}

typedef $$CachedTimetableDatasetsTableProcessedTableManager
    = ProcessedTableManager<
        _$AppDatabase,
        $CachedTimetableDatasetsTable,
        CachedTimetableDataset,
        $$CachedTimetableDatasetsTableFilterComposer,
        $$CachedTimetableDatasetsTableOrderingComposer,
        $$CachedTimetableDatasetsTableAnnotationComposer,
        $$CachedTimetableDatasetsTableCreateCompanionBuilder,
        $$CachedTimetableDatasetsTableUpdateCompanionBuilder,
        (
          CachedTimetableDataset,
          BaseReferences<_$AppDatabase, $CachedTimetableDatasetsTable,
              CachedTimetableDataset>
        ),
        CachedTimetableDataset,
        PrefetchHooks Function()>;

class $AppDatabaseManager {
  final _$AppDatabase _db;
  $AppDatabaseManager(this._db);
  $$CachedContextsTableTableManager get cachedContexts =>
      $$CachedContextsTableTableManager(_db, _db.cachedContexts);
  $$CacheMetadataTableTableManager get cacheMetadata =>
      $$CacheMetadataTableTableManager(_db, _db.cacheMetadata);
  $$CachedTimetableDatasetsTableTableManager get cachedTimetableDatasets =>
      $$CachedTimetableDatasetsTableTableManager(
          _db, _db.cachedTimetableDatasets);
}
