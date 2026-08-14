abstract interface class RemoteReadDataSource<T> {
  Future<T> fetch();
}

abstract interface class LocalReadDataSource<T> {
  Future<T?> read();
  Future<void> replace(T value);
}

class OfflineUnavailable implements Exception {
  const OfflineUnavailable();
}

class OfflineReadRepository<T> {
  const OfflineReadRepository(this.remote, this.local);
  final RemoteReadDataSource<T> remote;
  final LocalReadDataSource<T> local;

  Future<T> refreshWithFallback() async {
    try {
      final fresh = await remote.fetch();
      await local.replace(fresh);
      return fresh;
    } catch (_) {
      final cached = await local.read();
      if (cached != null) return cached;
      throw const OfflineUnavailable();
    }
  }
}
