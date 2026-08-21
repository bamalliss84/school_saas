import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../core/local_database/app_database.dart';
import '../../../../core/offline/offline_error_policy.dart';
import '../data/communications_repository.dart';
import '../domain/communication_models.dart';
sealed class CommunicationsState { const CommunicationsState(); }
class CommunicationsLoading extends CommunicationsState { const CommunicationsLoading(); }
class CommunicationsFailure extends CommunicationsState { const CommunicationsFailure(this.message); final String message; }
class CommunicationsReady extends CommunicationsState { const CommunicationsReady(this.data,{this.selectedConversation,this.messages=const[],this.busy=false}); final CommunicationsSnapshot data; final ConversationSummary? selectedConversation; final List<ConversationMessage> messages; final bool busy; CommunicationsReady copyWith({CommunicationsSnapshot? data,ConversationSummary? selectedConversation,List<ConversationMessage>? messages,bool? busy,bool clearConversation=false})=>CommunicationsReady(data??this.data,selectedConversation:clearConversation?null:(selectedConversation??this.selectedConversation),messages:messages??this.messages,busy:busy??this.busy); }
class CommunicationsController extends StateNotifier<CommunicationsState>{ CommunicationsController(this.repo,this.scope):super(const CommunicationsLoading()); final StudentCommunicationsRepository repo; final CacheScope scope;
 Future<void> load() async {try{state=CommunicationsReady(await repo.load(scope));}catch(e){state=CommunicationsFailure(failureMessage(e,'تعذر تحميل بيانات التواصل'));}}
 Future<void> refresh() async {try{state=CommunicationsReady(await repo.refresh(scope));}catch(e){if(state is! CommunicationsReady)state=CommunicationsFailure(failureMessage(e,'تعذر تحديث بيانات التواصل'));}}
 Future<void> readNotification(int id) async {await repo.markNotificationRead(id);await refresh();}
 Future<void> readAll() async {await repo.markAllNotificationsRead();await refresh();}
 Future<void> readAnnouncement(int id) async {await repo.markAnnouncementRead(id);await refresh();}
 Future<void> openConversation(ConversationSummary c) async {final current=state;if(current is! CommunicationsReady)return; state=current.copyWith(selectedConversation:c,busy:true);try{final rows=await repo.messages(scope,c.id);await repo.markConversationRead(c.id);state=current.copyWith(selectedConversation:c,messages:rows,busy:false);}catch(e){state=current.copyWith(selectedConversation:c,messages:const[],busy:false);}}
 void closeConversation(){final s=state;if(s is CommunicationsReady)state=s.copyWith(clearConversation:true,messages:const[]);}
 Future<void> send(String body) async {final s=state;if(s is! CommunicationsReady||s.selectedConversation==null||body.trim().isEmpty)return;await repo.sendMessage(s.selectedConversation!.id,body.trim());await openConversation(s.selectedConversation!);}
 Future<void> createSupport(String category,String subject,String message) async {await repo.createSupport(category:category,subject:subject,message:message);await refresh();}
}
