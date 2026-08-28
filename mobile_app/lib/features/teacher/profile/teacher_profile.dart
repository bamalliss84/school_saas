import 'package:dio/dio.dart';

class TeacherProfile {
  const TeacherProfile({
    required this.id,
    required this.fullName,
    required this.employeeCode,
    required this.isActive,
    this.email = '',
    this.phone = '',
    this.specialization = '',
    this.qualification = '',
    this.hireDate,
  });

  final int id;
  final String fullName;
  final String email;
  final String phone;
  final String employeeCode;
  final String specialization;
  final String qualification;
  final String? hireDate;
  final bool isActive;

  factory TeacherProfile.fromJson(Map<String, dynamic> json) => TeacherProfile(
        id: (json['id'] as num).toInt(),
        fullName: json['full_name']?.toString() ?? '',
        email: json['email']?.toString() ?? '',
        phone: json['phone']?.toString() ?? '',
        employeeCode: json['employee_code']?.toString() ?? '',
        specialization: json['specialization']?.toString() ?? '',
        qualification: json['qualification']?.toString() ?? '',
        hireDate: json['hire_date']?.toString(),
        isActive: json['is_active'] as bool? ?? false,
      );
}

class TeacherProfileRepository {
  const TeacherProfileRepository(this._dio);
  final Dio _dio;

  Future<TeacherProfile> getProfile() async {
    final response =
        await _dio.get<Map<String, dynamic>>('teachers/me/profile/');
    return TeacherProfile.fromJson(response.data!);
  }
}
