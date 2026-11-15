import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:school_saas_mobile/features/teacher/communications/data/teacher_communications_repository.dart';
import 'package:school_saas_mobile/features/teacher/communications/domain/teacher_communication_models.dart';

void main() {
  test('student draft keeps the teacher_student contract', () {
    const draft = TeacherStudentConversationDraft(assignmentId: 3, studentId: 9, subject: 'الواجب');
    expect(draft.toJson(), {
      'conversation_type': 'teacher_student', 'teacher_assignment_id': 3, 'student_id': 9, 'subject': 'الواجب',
    });
  });

  test('parent draft sends only the signed reference, never a membership id', () {
    const draft = TeacherStudentConversationDraft(
        assignmentId: 3, studentId: 9, subject: 'المستوى', parentRecipientRef: 'signed-ref');
    final json = draft.toJson();
    expect(json['conversation_type'], 'teacher_parent');
    expect(json['recipient_ref'], 'signed-ref');
    expect(json.containsKey('parent_membership_id'), isFalse);
  });

  test('parent options come from safe discovery for the chosen assignment and student', () async {
    final requests = <RequestOptions>[];
    final dio = Dio()
      ..interceptors.add(InterceptorsWrapper(onRequest: (options, handler) {
        requests.add(options);
        handler.resolve(Response(requestOptions: options, data: {
          'results': [
            {'display_name': 'سالم أحمد', 'role': 'parent', 'relationship': 'father', 'recipient_ref': 'r1'},
            {'display_name': 'ignored', 'role': 'teacher', 'recipient_ref': 'x'},
          ],
        }));
      }));
    final options = await TeacherCommunicationsRepository(dio).parentOptions(studentId: 9, assignmentId: 3);
    expect(requests.single.path, 'communication/recipient-options/');
    expect(requests.single.queryParameters, {'student_id': 9, 'teacher_assignment_id': 3});
    expect(options.single.name, 'سالم أحمد');
    expect(options.single.relationshipLabel, 'الأب');
    expect(options.single.recipientRef, 'r1');
  });
}
