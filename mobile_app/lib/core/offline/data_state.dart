enum DataOrigin { remote, cache }

sealed class DataState<T> {
  const DataState();
}

class DataInitial<T> extends DataState<T> {
  const DataInitial();
}

class DataLoading<T> extends DataState<T> {
  const DataLoading();
}

class DataReady<T> extends DataState<T> {
  const DataReady(this.data,
      {required this.origin,
      required this.lastUpdated,
      this.refreshing = false});
  final T data;
  final DataOrigin origin;
  final DateTime lastUpdated;
  final bool refreshing;
  bool get isOfflineCache => origin == DataOrigin.cache;
}

class DataEmpty<T> extends DataState<T> {
  const DataEmpty({this.offline = false});
  final bool offline;
}

class DataError<T> extends DataState<T> {
  const DataError(this.message, {this.offline = false});
  final String message;
  final bool offline;
}
