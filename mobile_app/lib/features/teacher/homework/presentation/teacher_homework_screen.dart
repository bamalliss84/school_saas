import 'package:dio/dio.dart';
import 'package:file_selector/file_selector.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../core/design_system/role_visual_tokens.dart';
import '../../../../core/errors/app_failure.dart';
import '../../../../core/local_database/app_database.dart';
import '../../students/presentation/teacher_students_controller.dart';
import '../data/teacher_homework_repository.dart';
import '../domain/teacher_homework_models.dart';
import 'teacher_homework_controller.dart';

const _blue = RoleVisualTokens.teacher;
const _labels = {
  'draft': 'مسودة',
  'published': 'منشور',
  'closed': 'مغلق',
  'not_started': 'لم يبدأ',
  'submitted': 'تم التسليم',
  'graded': 'تم التصحيح',
  'reviewed': 'تمت المراجعة',
  'returned': 'معاد للتعديل',
};

class TeacherHomeworkScreen extends ConsumerStatefulWidget {
  const TeacherHomeworkScreen({
    super.key,
    required this.scope,
    required this.historical,
  });

  final CacheScope scope;
  final bool historical;

  @override
  ConsumerState<TeacherHomeworkScreen> createState() =>
      _TeacherHomeworkScreenState();
}

class _TeacherHomeworkScreenState extends ConsumerState<TeacherHomeworkScreen> {
  String filter = 'all', search = '';

  ({CacheScope scope, String filter, String search}) get query =>
      (scope: widget.scope, filter: filter, search: search);

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(teacherHomeworkProvider(query));
    return SafeArea(
      top: false,
      child: Stack(
        children: [
          Column(
            children: [
              if (widget.historical)
                Container(
                  width: double.infinity,
                  color: Colors.amber.shade100,
                  padding: const EdgeInsets.all(10),
                  child: const Text(
                    'سجل دراسي سابق — للعرض فقط',
                    textAlign: TextAlign.center,
                  ),
                ),
              const _HomeworkHeader(),
              Padding(
                padding: const EdgeInsets.fromLTRB(18, 2, 18, 8),
                child: TextField(
                  onChanged: (value) => setState(() => search = value),
                  decoration: InputDecoration(
                    hintText: 'بحث في الواجبات...',
                    prefixIcon: const Icon(Icons.search_rounded, color: _blue),
                    filled: true,
                    fillColor: const Color(0xfff7f9fe),
                    contentPadding: const EdgeInsets.symmetric(vertical: 16),
                    enabledBorder: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(18),
                      borderSide: const BorderSide(color: Color(0xffe1e7f2)),
                    ),
                    focusedBorder: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(18),
                      borderSide: const BorderSide(color: _blue, width: 1.4),
                    ),
                  ),
                ),
              ),
              SizedBox(
                height: 54,
                child: ListView(
                  scrollDirection: Axis.horizontal,
                  padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 5),
                  children: const {
                    'all': 'الكل',
                    'draft': 'مسودة',
                    'published': 'منشور',
                    'closed': 'مغلق',
                    'pending': 'يحتاج تصحيح',
                  }.entries.map((entry) {
                    final selected = filter == entry.key;
                    return Padding(
                      padding: const EdgeInsets.symmetric(horizontal: 4),
                      child: ChoiceChip(
                        label: Text(entry.value),
                        selected: selected,
                        onSelected: (_) => setState(() => filter = entry.key),
                        showCheckmark: false,
                        selectedColor: _blue,
                        backgroundColor: Colors.white,
                        side: BorderSide(
                          color: selected ? _blue : const Color(0xffdfe5ef),
                        ),
                        labelStyle: TextStyle(
                          color: selected ? Colors.white : const Color(0xff31415f),
                          fontWeight: selected ? FontWeight.w700 : FontWeight.w500,
                        ),
                        shape: const StadiumBorder(),
                      ),
                    );
                  }).toList(),
                ),
              ),
              Expanded(
                child: state.when(
                  loading: () => const Center(child: CircularProgressIndicator()),
                  error: (error, _) => _Error(
                    _message(error),
                    () => ref.invalidate(teacherHomeworkProvider(query)),
                  ),
                  data: (items) => items.isEmpty
                      ? const _HomeworkEmpty()
                      : RefreshIndicator(
                          onRefresh: () async =>
                              ref.invalidate(teacherHomeworkProvider(query)),
                          child: ListView.separated(
                            padding: EdgeInsets.fromLTRB(
                              16,
                              8,
                              16,
                              widget.historical ? 18 : 94,
                            ),
                            itemCount: items.length,
                            separatorBuilder: (_, __) => const SizedBox(height: 12),
                            itemBuilder: (context, index) => _HomeworkCard(
                              items[index],
                              () => _open(context, items[index]),
                              needsGrading: filter == 'pending',
                            ),
                          ),
                        ),
                ),
              ),
            ],
          ),
          if (!widget.historical)
            Positioned(
              left: 18,
              bottom: 10,
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  FloatingActionButton(
                    heroTag: 'teacher-homework-create',
                    tooltip: 'إنشاء واجب',
                    backgroundColor: _blue,
                    foregroundColor: Colors.white,
                    elevation: 5,
                    onPressed: () => _edit(context),
                    child: const Icon(Icons.add_rounded, size: 30),
                  ),
                  const SizedBox(height: 4),
                  Container(
                    padding:
                        const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                    decoration: BoxDecoration(
                      color: const Color(0xff26344f),
                      borderRadius: BorderRadius.circular(7),
                    ),
                    child: const Text(
                      'إنشاء واجب',
                      style: TextStyle(color: Colors.white, fontSize: 10),
                    ),
                  ),
                ],
              ),
            ),
        ],
      ),
    );
  }

  Future<void> _edit(BuildContext context, [TeacherHomework? item]) async {
    final changed = await Navigator.push<bool>(
      context,
      MaterialPageRoute(
        builder: (_) => TeacherHomeworkEditor(scope: widget.scope, item: item),
      ),
    );
    if (changed == true) ref.invalidate(teacherHomeworkProvider(query));
  }

  Future<void> _open(BuildContext context, TeacherHomework item) async {
    await Navigator.push(
      context,
      MaterialPageRoute(
        builder: (_) => TeacherHomeworkDetail(
          scope: widget.scope,
          id: item.id,
          historical: widget.historical,
          onEdit: () => _edit(context, item),
        ),
      ),
    );
    ref.invalidate(teacherHomeworkProvider(query));
  }
}

class _HomeworkHeader extends StatelessWidget {
  const _HomeworkHeader();

  @override
  Widget build(BuildContext context) => Padding(
        padding: const EdgeInsets.fromLTRB(18, 18, 18, 14),
        child: Row(
          children: [
            const Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('المهام والتقييم',
                      style: TextStyle(fontSize: 25, fontWeight: FontWeight.w800)),
                  SizedBox(height: 4),
                  Text(
                    'إدارة الواجبات ومتابعة تسليم الطلاب',
                    style: TextStyle(color: Color(0xff67728a), fontSize: 14),
                  ),
                ],
              ),
            ),
            const SizedBox(width: 12),
            Container(
              width: 62,
              height: 62,
              decoration: BoxDecoration(
                color: RoleVisualTokens.softSurface(AppVisualRole.teacher),
                borderRadius: BorderRadius.circular(20),
              ),
              child: Stack(
                alignment: Alignment.center,
                children: [
                  Icon(Icons.menu_book_rounded, size: 34, color: _blue.withOpacity(.9)),
                  const PositionedDirectional(
                    end: 7,
                    top: 7,
                    child: Icon(Icons.check_circle, size: 17, color: Color(0xff22a56b)),
                  ),
                ],
              ),
            ),
          ],
        ),
      );
}

class _HomeworkCard extends StatelessWidget {
  const _HomeworkCard(this.item, this.tap, {required this.needsGrading});
  final TeacherHomework item;
  final VoidCallback tap;
  final bool needsGrading;

  @override
  Widget build(BuildContext context) {
    final badge = needsGrading ? 'يحتاج تصحيح' : (_labels[item.status] ?? item.status);
    final colors = needsGrading
        ? (const Color(0xfffff0d7), const Color(0xffb76800))
        : switch (item.status) {
            'published' => (const Color(0xffe4f6ec), const Color(0xff16834f)),
            'draft' => (const Color(0xffedf2ff), _blue),
            _ => (const Color(0xffeef0f4), const Color(0xff606a7b)),
          };
    return Material(
      color: Colors.white,
      elevation: 1.5,
      shadowColor: const Color(0x220b2f73),
      borderRadius: BorderRadius.circular(20),
      child: InkWell(
        onTap: tap,
        borderRadius: BorderRadius.circular(20),
        child: Stack(
          children: [
            Padding(
              padding: const EdgeInsets.fromLTRB(15, 15, 15, 52),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
              Container(
                width: 48,
                height: 48,
                decoration: BoxDecoration(
                  color: RoleVisualTokens.softSurface(AppVisualRole.teacher),
                  borderRadius: BorderRadius.circular(15),
                ),
                child: const Icon(Icons.assignment_outlined, color: _blue),
              ),
              const SizedBox(width: 13),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(item.title,
                        softWrap: true,
                        style: const TextStyle(fontSize: 17, fontWeight: FontWeight.w700)),
                    const SizedBox(height: 5),
                    Text(item.subject,
                        maxLines: 2,
                        overflow: TextOverflow.ellipsis,
                        style: const TextStyle(color: Color(0xff66728a))),
                    const SizedBox(height: 7),
                    Row(
                      children: [
                        const Icon(Icons.schedule_rounded, size: 17, color: Color(0xff7d8799)),
                        const SizedBox(width: 5),
                        Flexible(
                          child: Text('موعد التسليم: ${_date(item.dueDate)}',
                              overflow: TextOverflow.ellipsis,
                              style: const TextStyle(color: Color(0xff59657b), fontSize: 13)),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
              const Padding(
                padding: EdgeInsets.only(top: 38),
                child: Icon(Icons.chevron_left_rounded, color: Color(0xff8791a4)),
              ),
                ],
              ),
            ),
            Positioned(
              left: 15,
              bottom: 13,
              child: Container(
                padding:
                    const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
                decoration: BoxDecoration(
                  color: colors.$1,
                  borderRadius: BorderRadius.circular(30),
                ),
                child: Text(
                  badge,
                  style: TextStyle(
                    color: colors.$2,
                    fontSize: 12,
                    fontWeight: FontWeight.w700,
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _HomeworkEmpty extends StatelessWidget {
  const _HomeworkEmpty();
  @override
  Widget build(BuildContext context) => const Center(
        child: Padding(
          padding: EdgeInsets.all(28),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(Icons.assignment_outlined, size: 48, color: Color(0xff9aa5b8)),
              SizedBox(height: 12),
              Text('لا توجد واجبات ضمن هذا العرض', textAlign: TextAlign.center),
            ],
          ),
        ),
      );
}

class TeacherHomeworkEditor extends ConsumerStatefulWidget{const TeacherHomeworkEditor({super.key,required this.scope,this.item});final CacheScope scope;final TeacherHomework? item;@override ConsumerState<TeacherHomeworkEditor>createState()=>_EditorState();}
class _EditorState extends ConsumerState<TeacherHomeworkEditor>{final form=GlobalKey<FormState>();late final TextEditingController title,description,max;int? assignment;DateTime? due;String type='text';bool saving=false,dirty=false;
 @override void initState(){super.initState();final i=widget.item;title=TextEditingController(text:i?.title);description=TextEditingController(text:i?.description);max=TextEditingController(text:i?.maxGrade?.toString()??'');assignment=i?.assignmentId;due=i?.dueDate;type=i?.submissionType??'text';}
 @override void dispose(){title.dispose();description.dispose();max.dispose();super.dispose();}
 Future<bool> _leave()async=>!dirty||await showDialog<bool>(context:context,builder:(c)=>AlertDialog(title:const Text('تجاهل التغييرات؟'),content:const Text('لديك تغييرات غير محفوظة.'),actions:[TextButton(onPressed:()=>Navigator.pop(c,false),child:const Text('متابعة التحرير')),FilledButton(onPressed:()=>Navigator.pop(c,true),child:const Text('تجاهل'))]))==true;
 @override
 Widget build(BuildContext context) {
  final assignments=ref.watch(teacherAssignmentsProvider(widget.scope));
  return PopScope(
   canPop:!dirty,
   onPopInvokedWithResult:(did,_)async{if(!did&&await _leave()&&mounted)Navigator.pop(context);},
   child:Scaffold(
    resizeToAvoidBottomInset:true,
    backgroundColor:const Color(0xfff7f9fd),
    appBar:AppBar(
     backgroundColor:Colors.white,
     surfaceTintColor:Colors.white,
     elevation:0,
     title:Text(widget.item==null?'إنشاء واجب':'تعديل الواجب',style:const TextStyle(fontWeight:FontWeight.w700)),
    ),
    body:SafeArea(
     top:false,
     child:assignments.when(
      loading:()=>const Center(child:CircularProgressIndicator()),
      error:(e,_)=>_Error(_message(e),()=>ref.invalidate(teacherAssignmentsProvider(widget.scope))),
      data:(rows)=>Form(
       key:form,
       onChanged:()=>dirty=true,
       child:ListView(
        keyboardDismissBehavior:ScrollViewKeyboardDismissBehavior.onDrag,
        padding:EdgeInsets.fromLTRB(16,20,16,24+MediaQuery.viewInsetsOf(context).bottom),
        children:[
         DropdownButtonFormField<int>(
          value:assignment,
          isExpanded:true,
          alignment:AlignmentDirectional.centerStart,
          icon:const Icon(Icons.keyboard_arrow_down_rounded,color:_blue),
          decoration:_field('التكليف والمادة',Icons.school_outlined),
          items:rows.where((e)=>e.isCurrent).map((e)=>DropdownMenuItem<int>(
           value:e.id,
           child:Text('${e.subject.name} • ${e.classroom.name} / ${e.section.name}',maxLines:1,overflow:TextOverflow.ellipsis,textAlign:TextAlign.start),
          )).toList(),
          onChanged:widget.item==null?(v)=>setState(()=>assignment=v):null,
          validator:(v)=>v==null?'اختر تكليفًا':null,
         ),
         const SizedBox(height:14),
         TextFormField(controller:title,decoration:_field('العنوان',Icons.title_rounded),validator:(v)=>v!.trim().isEmpty?'العنوان مطلوب':null),
         const SizedBox(height:14),
         TextFormField(controller:description,minLines:5,maxLines:8,textAlignVertical:TextAlignVertical.top,decoration:_field('التعليمات',Icons.notes_rounded,alignTop:true)),
         const SizedBox(height:14),
         Material(
          color:Colors.white,
          borderRadius:BorderRadius.circular(16),
          child:ListTile(
           minTileHeight:58,
           shape:RoundedRectangleBorder(side:const BorderSide(color:Color(0xffdce3ef)),borderRadius:BorderRadius.circular(16)),
           title:Text(due==null?'موعد التسليم':'موعد التسليم: ${_date(due!)}',maxLines:1,overflow:TextOverflow.ellipsis),
           leading:const Icon(Icons.calendar_month_outlined,color:_blue),
           trailing:const Icon(Icons.chevron_left_rounded,color:Color(0xff8791a4)),
           onTap:_pickDate,
          ),
         ),
         const SizedBox(height:14),
         DropdownButtonFormField<String>(
          value:type,
          isExpanded:true,
          alignment:AlignmentDirectional.centerStart,
          icon:const Icon(Icons.keyboard_arrow_down_rounded,color:_blue),
          decoration:_field('طريقة التسليم',Icons.upload_file_outlined),
          items:const [
           DropdownMenuItem(value:'none',child:Text('بدون تسليم إلكتروني',overflow:TextOverflow.ellipsis)),
           DropdownMenuItem(value:'text',child:Text('نص')),
           DropdownMenuItem(value:'attachment',child:Text('مرفق')),
           DropdownMenuItem(value:'text_and_attachment',child:Text('نص ومرفق')),
          ],
          onChanged:(v)=>setState(()=>type=v!),
         ),
         const SizedBox(height:14),
         TextFormField(controller:max,keyboardType:const TextInputType.numberWithOptions(decimal:true),decoration:_field('الدرجة القصوى (اختياري)',Icons.grade_outlined)),
         const SizedBox(height:24),
         SizedBox(
          height:52,
          child:FilledButton(
           style:FilledButton.styleFrom(backgroundColor:_blue,shape:RoundedRectangleBorder(borderRadius:BorderRadius.circular(16))),
           onPressed:saving?_noop:_save,
           child:Text(saving?'جارٍ الحفظ...':'حفظ كمسودة',style:const TextStyle(fontWeight:FontWeight.w700,fontSize:16)),
          ),
         ),
        ],
       ),
      ),
     ),
    ),
   ),
  );
 }
 InputDecoration _field(String label,IconData icon,{bool alignTop=false})=>InputDecoration(
  labelText:label,
  prefixIcon:Padding(padding:EdgeInsets.only(bottom:alignTop?92:0),child:Icon(icon,color:_blue,size:21)),
  filled:true,
  fillColor:Colors.white,
  contentPadding:const EdgeInsets.symmetric(horizontal:16,vertical:17),
  enabledBorder:OutlineInputBorder(borderRadius:BorderRadius.circular(16),borderSide:const BorderSide(color:Color(0xffdce3ef))),
  focusedBorder:OutlineInputBorder(borderRadius:BorderRadius.circular(16),borderSide:const BorderSide(color:_blue,width:1.5)),
  errorBorder:OutlineInputBorder(borderRadius:BorderRadius.circular(16),borderSide:const BorderSide(color:Colors.redAccent)),
 );
 void _noop(){} Future<void> _pickDate()async{final d=await showDatePicker(context:context,firstDate:DateTime.now(),lastDate:DateTime.now().add(const Duration(days:730)),initialDate:due??DateTime.now().add(const Duration(days:1)));if(d!=null&&mounted){final t=await showTimePicker(context:context,initialTime:TimeOfDay.fromDateTime(due??DateTime.now()));if(t!=null)setState((){due=DateTime(d.year,d.month,d.day,t.hour,t.minute);dirty=true;});}}
 Future<void> _save()async{if(!form.currentState!.validate()||due==null){if(due==null)_snack(context,'موعد التسليم مطلوب');return;}setState(()=>saving=true);try{final rows=await ref.read(teacherAssignmentsProvider(widget.scope).future);final a=rows.firstWhere((e)=>e.id==assignment);await ref.read(teacherHomeworkRepositoryProvider).save(id:widget.item?.id,assignmentId:a.id,academicYearId:a.academicYear.id,title:title.text.trim(),description:description.text.trim(),due:due!,type:type,maxGrade:double.tryParse(max.text));dirty=false;if(mounted)Navigator.pop(context,true);}catch(e){if(mounted)_snack(context,_message(e,fallback:'تعذر حفظ الواجب. تحقق من البيانات وحاول مرة أخرى.'));}finally{if(mounted)setState(()=>saving=false);}}
}

class TeacherHomeworkDetail extends ConsumerStatefulWidget{const TeacherHomeworkDetail({super.key,required this.scope,required this.id,required this.historical,required this.onEdit});final CacheScope scope;final int id;final bool historical;final VoidCallback onEdit;@override ConsumerState<TeacherHomeworkDetail>createState()=>_DetailState();}
class _DetailState extends ConsumerState<TeacherHomeworkDetail>{late Future<(TeacherHomework,Map<String,dynamic>)> future;@override void initState(){super.initState();_load();}void _load(){final r=ref.read(teacherHomeworkRepositoryProvider);future=Future.wait([r.detail(widget.id),r.summary(widget.id)]).then((v)=>(v[0] as TeacherHomework,v[1] as Map<String,dynamic>));}
 @override Widget build(BuildContext context)=>Scaffold(appBar:AppBar(title:const Text('تفاصيل الواجب')),body:FutureBuilder(future:future,builder:(c,s){if(!s.hasData)return s.hasError?_Error(_message(s.error!),(){setState(_load);}):const Center(child:CircularProgressIndicator());final (h,sum)=s.data!;return ListView(padding:const EdgeInsets.all(16),children:[if(widget.historical)const Card(color:Color(0xfffff3cd),child:Padding(padding:EdgeInsets.all(12),child:Text('للعرض فقط في السجل الدراسي السابق'))),Text(h.title,style:Theme.of(c).textTheme.headlineSmall),Text('${h.subject} • ${_labels[h.status]}'),if(h.submissionType=='none')const Chip(label:Text('لا يتطلب تسليم')),const Divider(),Text(h.description.isEmpty?'لا توجد تعليمات':h.description),ListTile(leading:const Icon(Icons.event),title:Text('موعد التسليم: ${_date(h.dueDate)}')),if(h.maxGrade!=null)Text('الدرجة القصوى: ${h.maxGrade}'),Wrap(spacing:8,children:[Chip(label:Text('المستهدفون ${sum['target_students']??0}')),Chip(label:Text('تم التسليم ${sum['submitted']??0}')),Chip(label:Text('بانتظار التصحيح ${sum['pending_grading_count']??0}'))]),...h.attachments.map((a)=>ListTile(leading:const Icon(Icons.attach_file),title:Text(a.name))),const SizedBox(height:12),FilledButton.icon(onPressed:()=>Navigator.push(c,MaterialPageRoute(builder:(_)=>TeacherHomeworkStudents(homework:h,historical:widget.historical))),icon:const Icon(Icons.groups),label:const Text('عرض أعمال الطلاب')),if(!widget.historical)Wrap(spacing:8,children:[if(h.canEdit)OutlinedButton(onPressed:widget.onEdit,child:const Text('تعديل')),if(h.canPublish)FilledButton(onPressed:()=>_action('publish'),child:const Text('نشر')),if(h.canClose)FilledButton(onPressed:()=>_action('close'),child:const Text('إغلاق')),if(h.canEdit)TextButton(onPressed:_delete,child:const Text('حذف'))]),if(!widget.historical&&h.canEdit)OutlinedButton.icon(onPressed:()=>_upload(h.id),icon:const Icon(Icons.upload_file),label:const Text('إضافة مرفقات'))]);}));
 Future<void> _action(String a)async{try{await ref.read(teacherHomeworkRepositoryProvider).action(widget.id,a);setState(_load);}catch(e){if(mounted)_snack(context,_message(e));}}
 Future<void> _delete()async{final ok=await showDialog<bool>(context:context,builder:(c)=>AlertDialog(title:const Text('حذف المسودة؟'),actions:[TextButton(onPressed:()=>Navigator.pop(c,false),child:const Text('إلغاء')),FilledButton(onPressed:()=>Navigator.pop(c,true),child:const Text('حذف'))]))==true;if(ok){try{await ref.read(teacherHomeworkRepositoryProvider).delete(widget.id);if(mounted)Navigator.pop(context);}catch(e){if(mounted)_snack(context,_message(e));}}}
 Future<void> _upload(int id)async{const types=XTypeGroup(label:'homework attachments',extensions:['jpg','jpeg','png','pdf']);final files=await openFiles(acceptedTypeGroups:[types]);final paths=files.map((file)=>file.path).where((path)=>path.isNotEmpty).toList();if(paths.isEmpty)return;try{await ref.read(teacherHomeworkRepositoryProvider).upload(id,paths);setState(_load);}catch(e){if(mounted)_snack(context,_message(e));}}
}

class TeacherHomeworkStudents extends ConsumerStatefulWidget{const TeacherHomeworkStudents({super.key,required this.homework,required this.historical});final TeacherHomework homework;final bool historical;@override ConsumerState<TeacherHomeworkStudents>createState()=>_StudentsState();}
class _StudentsState extends ConsumerState<TeacherHomeworkStudents>{String? filter;String search='';late Future<TeacherStudentStatus> future;bool get viewOnly=>widget.homework.submissionType=='none';@override void initState(){super.initState();_load();}void _load(){future=ref.read(teacherHomeworkRepositoryProvider).students(widget.homework.id,status:viewOnly?null:filter,search:search);}
 @override Widget build(BuildContext c)=>Scaffold(appBar:AppBar(title:const Text('أعمال الطلاب')),body:Column(children:[Padding(padding:const EdgeInsets.all(12),child:TextField(onSubmitted:(v){search=v;setState(_load);},decoration:const InputDecoration(hintText:'بحث بالاسم أو الرقم',prefixIcon:Icon(Icons.search),border:OutlineInputBorder()))),if(viewOnly)const Padding(padding:EdgeInsets.symmetric(horizontal:12),child:Align(alignment:AlignmentDirectional.centerStart,child:Chip(label:Text('لا يتطلب تسليم'))))else SizedBox(height:48,child:ListView(scrollDirection:Axis.horizontal,children:{null:'الكل','not_started':'لم يبدأ','draft':'مسودة','submitted':'تم التسليم','graded':'تم التصحيح','reviewed':'تمت المراجعة','returned':'معاد'}.entries.map((e)=>ChoiceChip(label:Text(e.value),selected:filter==e.key,onSelected:(_){filter=e.key;setState(_load);})).toList())),Expanded(child:FutureBuilder(future:future,builder:(c,s){if(!s.hasData)return s.hasError?_Error(_message(s.error!),(){setState(_load);}):const Center(child:CircularProgressIndicator());final d=s.data!;return Column(children:[if(!viewOnly)Wrap(spacing:6,children:[Chip(label:Text('الكل ${d.count('total_students')}')),Chip(label:Text('لم يبدأ ${d.count('not_started_count')}')),Chip(label:Text('ينتظر ${d.count('pending_grading_count')}')),Chip(label:Text('تمت المراجعة ${d.count('reviewed_count')}'))]),Expanded(child:d.students.isEmpty?const Center(child:Text('لا توجد نتائج')):ListView.builder(itemCount:d.students.length,itemBuilder:(c,i){final x=d.students[i];return ListTile(onTap:viewOnly||x.submissionId==null?null:()=>Navigator.push(c,MaterialPageRoute(builder:(_)=>TeacherSubmissionScreen(student:x,homework:widget.homework,historical:widget.historical))).then((_)=>setState(_load)),title:Text(x.studentName),subtitle:Text('${x.studentCode}${x.isLate?' • متأخر':''}'),trailing:Chip(label:Text(viewOnly?'لا يتطلب تسليم':_labels[x.status]??x.status)));}))]);}))]));}

class TeacherSubmissionScreen extends ConsumerStatefulWidget{const TeacherSubmissionScreen({super.key,required this.student,required this.homework,required this.historical});final TeacherHomeworkStudent student;final TeacherHomework homework;final bool historical;@override ConsumerState<TeacherSubmissionScreen>createState()=>_SubmissionState();}
class _SubmissionState extends ConsumerState<TeacherSubmissionScreen>{late Future<TeacherSubmission> future;final grade=TextEditingController(),note=TextEditingController();@override void initState(){super.initState();future=ref.read(teacherHomeworkRepositoryProvider).submission(widget.student.submissionId!);grade.text=widget.student.grade?.toString()??'';note.text=widget.student.teacherNote;}@override void dispose(){grade.dispose();note.dispose();super.dispose();}
 @override Widget build(BuildContext c)=>Scaffold(appBar:AppBar(title:Text(widget.student.studentName)),body:FutureBuilder(future:future,builder:(c,s){if(!s.hasData)return s.hasError?_Error(_message(s.error!),(){}):const Center(child:CircularProgressIndicator());final x=s.data!;return ListView(padding:const EdgeInsets.all(16),children:[Text('${x.studentName} • ${x.studentCode}',style:Theme.of(c).textTheme.titleLarge),Chip(label:Text(_labels[x.status]??x.status)),const Text('الإجابة',style:TextStyle(fontWeight:FontWeight.bold)),SelectableText(x.answer.isEmpty?'لا توجد إجابة نصية':x.answer),...x.attachments.map((a)=>ListTile(leading:const Icon(Icons.attach_file),title:Text(a.name))),if(!widget.historical&&(widget.student.canGrade||widget.student.canReview||widget.student.canReturn))...[if(widget.student.canGrade)TextField(controller:grade,keyboardType:TextInputType.number,decoration:InputDecoration(labelText:'الدرجة من ${widget.student.maxGrade}')),TextField(controller:note,maxLines:3,decoration:const InputDecoration(labelText:'ملاحظات المعلم')),const SizedBox(height:12),if(widget.student.canGrade)FilledButton(onPressed:_grade,child:const Text('حفظ التصحيح')),if(widget.student.canReview)FilledButton(onPressed:_review,child:const Text('اعتماد المراجعة')),if(widget.student.canReturn)OutlinedButton(onPressed:_return,child:const Text('إعادة للتعديل'))]]);}));
 Future<void> _grade()async{final value=double.tryParse(grade.text);if(value==null){_snack(context,'أدخل درجة صحيحة');return;}try{await ref.read(teacherHomeworkRepositoryProvider).grade(widget.student.submissionId!,value,note.text);if(mounted)Navigator.pop(context);}catch(e){if(mounted)_snack(context,_message(e));}}
 Future<void> _review()async{try{await ref.read(teacherHomeworkRepositoryProvider).review(widget.student.submissionId!,note.text);if(mounted)Navigator.pop(context);}catch(e){if(mounted)_snack(context,_message(e));}}
 Future<void> _return()async{try{await ref.read(teacherHomeworkRepositoryProvider).returnWork(widget.student.submissionId!,note.text);if(mounted)Navigator.pop(context);}catch(e){if(mounted)_snack(context,_message(e));}}
}
class _Error extends StatelessWidget{const _Error(this.message,this.retry);final String message;final VoidCallback retry;@override Widget build(BuildContext c)=>Center(child:Padding(padding:const EdgeInsets.all(24),child:Column(mainAxisSize:MainAxisSize.min,children:[const Icon(Icons.error_outline,size:42),Text(message,textAlign:TextAlign.center),TextButton(onPressed:retry,child:const Text('إعادة المحاولة'))])));}
String _date(DateTime d)=>'${d.year}/${d.month.toString().padLeft(2,'0')}/${d.day.toString().padLeft(2,'0')} ${d.hour.toString().padLeft(2,'0')}:${d.minute.toString().padLeft(2,'0')}';
String _message(Object e,{String fallback='تعذر إكمال العملية. تحقق من الاتصال وحاول مرة أخرى.'}){
 if(e is DioException){
  final message=_serverMessage(e.response?.data);
  if(message!=null)return message;
  if(e.error is AppFailure)return (e.error! as AppFailure).message;
 }
 return fallback;
}
String? _serverMessage(Object? value){
 if(value is String){final message=value.trim();return message.isEmpty?null:message;}
 if(value is List){
  final messages=value.map(_serverMessage).whereType<String>().toSet().toList();
  return messages.isEmpty?null:messages.join('\n');
 }
 if(value is Map){
  for(final key in const ['detail','non_field_errors','errors']){
   final message=_serverMessage(value[key]);
   if(message!=null)return message;
  }
  final fieldMessages=<String>[];
  for(final entry in value.entries){
   if(const {'success','detail','message','non_field_errors','errors'}.contains(entry.key))continue;
   final message=_serverMessage(entry.value);
   if(message!=null)fieldMessages.add(message);
  }
  if(fieldMessages.isNotEmpty)return fieldMessages.toSet().join('\n');
  return _serverMessage(value['message']);
 }
 return null;
}
void _snack(BuildContext c,String m)=>ScaffoldMessenger.of(c).showSnackBar(SnackBar(content:Text(m)));
