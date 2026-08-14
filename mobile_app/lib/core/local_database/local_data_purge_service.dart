import 'app_database.dart';

class LocalDataPurgeService {
  const LocalDataPurgeService(this._database);
  final AppDatabase _database;

  Future<void> purgeCurrentUserData(String localUserKey) =>
      _database.purgeUser(localUserKey);
}
