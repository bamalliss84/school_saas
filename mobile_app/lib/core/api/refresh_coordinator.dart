class RefreshCoordinator {
  Future<String>? _inFlight;

  Future<String> run(Future<String> Function() operation) {
    final running = _inFlight;
    if (running != null) return running;
    final future = operation();
    _inFlight = future;
    return future.whenComplete(() => _inFlight = null);
  }
}
