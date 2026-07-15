import json
from sqlalchemy.orm import Session
from app import models, database
from app.logger import logger
from app.services import agent_service, vector_service

def run_profiling_background_task(user_id: int):
    """
    Executes asynchronous double-loop profiling adjustments.
    1. Checks for un-embedded learning event logs, generates embeddings via fallback vector engines, and stores them.
    2. Runs the Cognitive Profiler Agent to dynamically adjust global velocity, attention spans, retention rates, and updates mastery scores.
    """
    logger.log_info(f"Starting Cognitive Background Task for user_id {user_id}...")
    db = database.SessionLocal()
    try:
        user_profile = db.query(models.UserProfile).filter(models.UserProfile.user_id == user_id).first()
        if not user_profile:
            user_obj = db.query(models.User).filter(models.User.id == user_id).first()
            name = user_obj.username if user_obj else "Guest User"
            logger.log_info(f"No UserProfile found. Creating profile for user {name}...")
            user_profile = models.UserProfile(user_id=user_id, name=name, primary_goals="General Learning")
            db.add(user_profile)
            db.commit()
            db.refresh(user_profile)

        _us = db.query(models.UserSettings).filter(models.UserSettings.user_id == user_id).first()
        user_api_key = _us.gemini_api_key if _us else None
        user_knowledge_model = _us.knowledge_model if _us else None
            
        if not user_profile.cognitive_profile:
            logger.log_info("No CognitiveProfile found. Creating default empty profile...")
            cp = models.CognitiveProfile(user_id=user_profile.id, cognitive_data_json="{}", interests_json="[]")
            db.add(cp)
            db.commit()
            db.refresh(user_profile)
            
        # 1. Update Vectors for any un-embedded logs (Asynchronous generation)
        logger.log_process_start("Semantic Vectorization", "Checking for un-embedded learning logs")
        unembedded_logs = db.query(models.LearningEventLog).filter(
            models.LearningEventLog.user_id == user_profile.id,
            models.LearningEventLog.vector_embedding_json == None
        ).all()
        if unembedded_logs:
            logger.log_info(f"Found {len(unembedded_logs)} un-embedded logs. Extracting embeddings...")
            embedder = vector_service.get_embeddings_model(google_api_key=user_api_key)
            for log in unembedded_logs:
                text_to_embed = f"Event: {log.event_type} | Course: {log.course_title} | Session: {log.session_title} | Duration: {log.study_duration_seconds}s | Details: {log.raw_interaction_text or ''}"
                try:
                    vector = embedder.embed_query(text_to_embed)
                    log.vector_embedding_json = json.dumps(vector)
                    
                    logger.log_ai_call(
                        step_name="Semantic Vectorization",
                        model_name=getattr(embedder, 'model', 'DynamicFallbackEmbeddings'),
                        system_prompt="Generate vector embedding for the following learning log event.",
                        user_input=text_to_embed,
                        result=f"Vector generated with {len(vector)} dimensions. Sample: {str(vector[:3])}..."
                    )
                    logger.log_success(f"Generated semantic vector for event '{log.session_title}'")
                except Exception as e:
                    logger.log_error(f"Vector embedding failed for log {log.id}: {str(e)}")
            db.commit()
            logger.log_success("All pending logs have been vectorized successfully.")
        else:
            logger.log_info("All logs are already vectorized. No new embeddings required.")
        logger.log_process_end("Semantic Vectorization", 0)
            
        # 2. Extract traits and update conceptual mastery nodes via incremental delta profiling
        cog_profile = user_profile.cognitive_profile
        logger.log_process_start("Cognitive Profiling Pipeline", "Executing incremental delta-based profiling for the latest learning event")
        
        # Get all unprofiled learning events for the user
        unprofiled_events = db.query(models.LearningEventLog).filter(
            models.LearningEventLog.user_id == user_profile.id,
            models.LearningEventLog.is_profiled == False
        ).order_by(models.LearningEventLog.timestamp.asc()).all()
        
        if not unprofiled_events:
            logger.log_info("No unprofiled learning events found. Skipping incremental profiling.")
            logger.log_process_end("Cognitive Profiling Pipeline", 0)
            return

        # Fetch existing knowledge nodes in detail to feed to the AI context
        existing_nodes = db.query(models.KnowledgeNode).filter(models.KnowledgeNode.user_id == user_profile.id).all()
        existing_nodes_str = "\n".join([
            f"- {n.concept} (Category: {n.category}) | Mastery: {n.mastery_score:.2f} | Prerequisites: {json.loads(n.dependencies_json).get('prerequisites', []) if n.dependencies_json else []}" 
            for n in existing_nodes
        ]) if existing_nodes else "None"
        
        # Serialize biography and current cognitive state
        profile_str = f"Name: {user_profile.name}, Age: {user_profile.age}, Goals: {user_profile.primary_goals}, Education: {user_profile.education_level or 'N/A'}, Experience: {user_profile.background_experience or 'N/A'}"
        
        strengths = json.loads(cog_profile.strength_areas_json) if cog_profile.strength_areas_json else []
        interests = json.loads(cog_profile.interests_json) if cog_profile.interests_json else []
        recommended = json.loads(cog_profile.recommended_topics_json) if cog_profile.recommended_topics_json else []
        
        current_state_str = f"""
        Velocity: {cog_profile.global_learning_velocity}
        Learning Style Summary: {cog_profile.learning_style_summary or 'None'}
        Personality Summary: {cog_profile.personality_summary or 'None'}
        Key Strengths: {strengths}
        Interests: {interests}
        Recommended Next Topics: {recommended}
        """

        events_info = []
        for idx, event in enumerate(unprofiled_events, 1):
            events_info.append(f"""Event #{idx}:
        Event Type: {event.event_type}
        Course Title: {event.course_title or 'N/A'}
        Session Title: {event.session_title or 'N/A'}
        Study Duration: {event.study_duration_seconds} seconds
        Details: {event.raw_interaction_text or 'N/A'}
        Timestamp: {event.timestamp}""")
        
        new_event_str = "\n\n".join(events_info)

        # Run the LangChain-powered Incremental Cognitive Profiler Agent
        updated_data = agent_service.run_incremental_cognitive_profiler(
            profile_str, current_state_str, existing_nodes_str, new_event_str, api_key=user_api_key, knowledge_model=user_knowledge_model
        )
        
        if updated_data:
            # 1. Update Cognitive Profile only if requested and fields are provided
            if updated_data.should_update_cognitive_profile:
                logger.log_info("Applying refined cognitive traits updates returned by AI Agent...")
                if updated_data.global_learning_velocity is not None:
                    cog_profile.global_learning_velocity = updated_data.global_learning_velocity
                
                if updated_data.learning_style_summary_update:
                    cog_profile.learning_style_summary = updated_data.learning_style_summary_update
                if updated_data.personality_summary_update:
                    cog_profile.personality_summary = updated_data.personality_summary_update
                
                # Overwrite lists with complete updated consolidated lists
                if updated_data.strength_areas is not None:
                    cog_profile.strength_areas_json = json.dumps(updated_data.strength_areas, ensure_ascii=False)
                
                if updated_data.interests is not None:
                    cog_profile.interests_json = json.dumps(updated_data.interests, ensure_ascii=False)
                
                if updated_data.recommended_topics is not None:
                    cog_profile.recommended_topics_json = json.dumps(updated_data.recommended_topics, ensure_ascii=False)
            
            # 2. Add or Refine concept masteries and prerequisites inside our knowledge graph
            logger.log_info(f"AI Profiler returned {len(updated_data.updated_knowledge_nodes)} incremental concept changes.")
            for kn_update in updated_data.updated_knowledge_nodes:
                node = db.query(models.KnowledgeNode).filter(
                    models.KnowledgeNode.user_id == user_profile.id, 
                    models.KnowledgeNode.concept == kn_update.concept
                ).first()
                
                prereqs = kn_update.prerequisites or []
                diff_lvl = kn_update.difficulty_level or "مقدماتی"
                k_terms = kn_update.key_terms or []
                
                if kn_update.action == "add" or not node:
                    if not node:
                        node = models.KnowledgeNode(
                            user_id=user_profile.id,
                            concept=kn_update.concept,
                            category=kn_update.category,
                            mastery_score=min(0.98, max(0.0, kn_update.mastery_score_delta)),
                            dependencies_json=json.dumps({
                                "prerequisites": prereqs,
                                "difficulty_level": diff_lvl,
                                "key_terms": k_terms
                            }, ensure_ascii=False)
                        )
                        db.add(node)
                        logger.log_success(f"Incremental Profiler: Added new concept '{kn_update.concept}' ({node.mastery_score*100:.1f}%) [Level: {diff_lvl}]")
                elif kn_update.action == "refine":
                    old_score = node.mastery_score
                    node.mastery_score = min(0.98, node.mastery_score + kn_update.mastery_score_delta)
                    
                    existing_prereqs = []
                    existing_terms = []
                    if node.dependencies_json:
                        try:
                            dep_data = json.loads(node.dependencies_json)
                            existing_prereqs = dep_data.get("prerequisites", [])
                            existing_terms = dep_data.get("key_terms", [])
                        except Exception:
                            pass
                    for p in prereqs:
                        if p not in existing_prereqs:
                            existing_prereqs.append(p)
                    for kt in k_terms:
                        if kt not in existing_terms:
                            existing_terms.append(kt)
                    node.dependencies_json = json.dumps({
                        "prerequisites": existing_prereqs,
                        "difficulty_level": diff_lvl,
                        "key_terms": existing_terms
                    }, ensure_ascii=False)
                    logger.log_success(f"Incremental Profiler: Refined concept '{kn_update.concept}' mastery: {old_score*100:.1f}% -> {node.mastery_score*100:.1f}%")
            
            # Mark processed events as profiled
            for event in unprofiled_events:
                event.is_profiled = True
            db.commit()
            logger.log_success(f"All {len(unprofiled_events)} incremental events marked as profiled and cognitive states updated successfully!")
        else:
            logger.log_error("Profiler returned None. AI failed to return valid incremental schema.")
        logger.log_process_end("Cognitive Profiling Pipeline", 0)
    except Exception as e:
        logger.log_error(f"Background profiling failed: {str(e)}")
    finally:
        db.close()

def rebuild_user_cognitive_profile(db: Session, user_id: int) -> dict:
    """
    Core rebuilding pipeline. Completely recreates learner cognitive parameters
    and mastery scores by performing a full historical aggregation.
    Guarantees consistency across web routes and CLI sync scripts.
    """
    logger.log_process_start("Full Profile Rebuild", f"Aggregating all historical user data to rebuild knowledge bases for user {user_id}")
    
    try:
        # 1. Ensure user profile exists
        user_profile = db.query(models.UserProfile).filter(models.UserProfile.user_id == user_id).first()
        if not user_profile:
            user_settings = db.query(models.UserSettings).filter(models.UserSettings.user_id == user_id).first()
            if user_settings:
                name = user_settings.name
                bg = user_settings.background_experience
            else:
                user_obj = db.query(models.User).filter(models.User.id == user_id).first()
                name = user_obj.username if user_obj else "کاربر"
                bg = ""
            user_profile = models.UserProfile(user_id=user_id, name=name, background_experience=bg, primary_goals="یادگیری و توسعه فردی")
            db.add(user_profile)
            db.commit()
            db.refresh(user_profile)
            logger.log_success(f"Created UserProfile for: {name}")

        # 2. Sync settings -> profile
        user_settings = db.query(models.UserSettings).filter(models.UserSettings.user_id == user_id).first()
        if user_settings:
            user_profile.name = user_settings.name or user_profile.name
            user_profile.age = user_settings.age or user_profile.age
            user_profile.education_level = user_settings.education or user_profile.education_level
            user_profile.background_experience = user_settings.background_experience or user_profile.background_experience
            db.commit()
            logger.log_success("Synced UserSettings -> UserProfile")

        # 3. Ensure cognitive profile exists
        if not user_profile.cognitive_profile:
            cp = models.CognitiveProfile(
                user_id=user_profile.id,
                cognitive_data_json="{}",
                interests_json="[]",
                recommended_topics_json="[]",
                strength_areas_json="[]"
            )
            db.add(cp)
            db.commit()
            db.refresh(user_profile)

        # 4. Clear old knowledge nodes to prevent historical drift on rebuild
        deleted = db.query(models.KnowledgeNode).filter(models.KnowledgeNode.user_id == user_profile.id).delete()
        
        # Mark all existing event logs for this user as profiled
        db.query(models.LearningEventLog).filter(
            models.LearningEventLog.user_id == user_profile.id
        ).update({models.LearningEventLog.is_profiled: True})
        
        db.commit()
        logger.log_info(f"Cleared {deleted} old knowledge nodes and marked all existing event logs as profiled.")

        # 5. Gather ALL historical learning data for the user
        all_courses = db.query(models.Course).filter(models.Course.user_id == user_id).all()
        
        # Aggregate courses information
        courses_info = []
        for c in all_courses:
            total_study_time = sum(item.study_time for item in c.items)
            session_count = len(c.items)
            completed_count = sum(1 for item in c.items if item.is_completed)
            progress_percentage = (completed_count / session_count * 100) if session_count > 0 else 0.0
            outline_titles = [item.title for item in sorted(c.items, key=lambda x: x.order)]
            outline_str = ", ".join(outline_titles) if outline_titles else "فاقد سرفصل"
            courses_info.append(
                f"- دوره: '{c.title}' | سطح: '{c.level or 'نامشخص'}' | درصد پیشرفت: {progress_percentage:.1f}% | "
                f"توضیحات: '{c.description or ''}' | کل زمان مطالعه دوره: {total_study_time} ثانیه | "
                f"تعداد کل جلسات: {session_count} | سرفصل‌های کل دوره: [{outline_str}]"
            )
        courses_str = "\n".join(courses_info) if courses_info else "هیچ دوره‌ای ثبت نشده است."

        # Aggregate outline items completed (filtered by user's courses)
        completed_items = db.query(models.OutlineItem).join(models.Course).filter(
            models.Course.user_id == user_id, 
            models.OutlineItem.is_completed == True
        ).all()
        
        sessions_info = []
        for item in completed_items:
            sessions_info.append(
                f"- جلسه سرفصل تکمیل‌شده: '{item.title}' | دوره: '{item.course.title if item.course else 'نامشخص'}' | زمان مطالعه: {item.study_time} ثانیه"
            )
        sessions_str = "\n".join(sessions_info) if sessions_info else "هیچ سرفصل تکمیل‌شده‌ای وجود ندارد."

        # Aggregate coach conversations (filtered by user's courses)
        all_chats = db.query(models.CourseChatMessage).join(models.Course).filter(
            models.Course.user_id == user_id
        ).all()
        
        chats_info = []
        for chat in all_chats:
            role_fa = "مربی هوشمند" if chat.role == "assistant" else "کاربر"
            course_title = chat.course.title if chat.course else "نامشخص"
            chats_info.append(
                f"- [{role_fa}] در دوره '{course_title}': {chat.content}"
            )
        chats_str = "\n".join(chats_info) if chats_info else "هیچ گفتگویی ثبت نشده است."

        # Aggregate event log histories
        all_logs = db.query(models.LearningEventLog).filter(models.LearningEventLog.user_id == user_profile.id).all()
        logs_info = []
        for log in all_logs:
            logs_info.append(
                f"- رویداد: '{log.event_type}' | دوره: '{log.course_title or ''}' | جلسه: '{log.session_title or ''}' | زمان مطالعه: {log.study_duration_seconds} ثانیه | جزئیات تعامل: {log.raw_interaction_text or ''}"
            )
        logs_str = "\n".join(logs_info) if logs_info else "لاگ رویداد آموزشی یافت نشد."

        # Build complete context block for profiler
        profile_str = (
            f"نام: {user_profile.name or 'کاربر'}, سن: {user_profile.age or 'نامشخص'}, "
            f"تحصیلات: {user_profile.education_level or 'نامشخص'}, "
            f"پیش‌زمینه: {user_profile.background_experience or ''}, "
            f"اهداف: {user_profile.primary_goals or 'یادگیری و توسعه فردی'}"
        )
        
        cog_profile = user_profile.cognitive_profile
        current_state_str = "وضعیت شناختی قبلی وجود ندارد. سرعت یادگیری، تمرکز، و شاخص حفظ اطلاعات را کاملاً از نو بر اساس لاگ‌ها و سرفصل‌های تکمیل‌شده از نو دقیقاً محاسبه کنید."

        super_history_str = f"""
=== دوره‌های کاربر (User Courses) ===
{courses_str}

=== وضعیت سرفصل‌ها و جلسات تکمیل‌شده (Completed Outline Items) ===
{sessions_str}

=== گفتگوها با مربی هوشمند (Smart Coach Chats) ===
{chats_str}

=== لاگ رویدادهای آموزشی (Learning Event Logs) ===
{logs_str}
"""

        # Verbose terminal debugging logs
        logger.log_info("=" * 70)
        logger.log_info(f"🚨 COMPREHENSIVE REBUILD INITIATED FOR USER {user_id} 🚨")
        logger.log_info(f"User Profile Info:\n{profile_str}")
        logger.log_info(f"Current State:\n{current_state_str}")
        logger.log_info(f"Aggregated Courses: {len(all_courses)}")
        logger.log_info(f"Aggregated Completed Sessions: {len(completed_items)}")
        logger.log_info(f"Aggregated Chats: {len(all_chats)}")
        logger.log_info(f"Aggregated Event Logs: {len(all_logs)}")
        logger.log_info("-" * 70)
        logger.log_info("📜 FULL HISTORICAL TEXT COMPILED FOR AI:")
        logger.log_info(super_history_str.strip())
        logger.log_info("=" * 70)

        # 6. Execute AI cognitive analysis
        _us2 = db.query(models.UserSettings).filter(models.UserSettings.user_id == user_id).first()
        _rebuild_api_key = _us2.gemini_api_key if _us2 else None
        _rebuild_knowledge_model = _us2.knowledge_model if _us2 else None
        updated_data = agent_service.run_cognitive_profiler(profile_str, current_state_str, super_history_str, api_key=_rebuild_api_key, knowledge_model=_rebuild_knowledge_model)

        if not updated_data:
            logger.log_error("Profiler returned None. AI Rebuild Failed.")
            raise ValueError("AI profiler failed to generate cognitive profile.")

        # 7. Write new traits updates
        cog_profile.global_learning_velocity = updated_data.global_learning_velocity
        
        cognitive_data_dict = {
            "learning_style": {
                "hands_on": updated_data.ls_hands_on,
                "visual": updated_data.ls_visual,
                "theoretical": updated_data.ls_theoretical,
                "self_directed": updated_data.ls_self_directed
            }
        }
        cog_profile.cognitive_data_json = json.dumps(cognitive_data_dict, ensure_ascii=False)
        cog_profile.interests_json = json.dumps(updated_data.interests, ensure_ascii=False)
        cog_profile.learning_style_summary = updated_data.learning_style_summary
        cog_profile.personality_summary = updated_data.personality_summary
        cog_profile.strength_areas_json = json.dumps(updated_data.strength_areas, ensure_ascii=False)
        cog_profile.recommended_topics_json = json.dumps(updated_data.recommended_topics, ensure_ascii=False)

        logger.log_success(f"Saved rebuilt cognitive profile. Got {len(updated_data.updated_knowledge_nodes)} knowledge nodes.")
        
        # 8. Re-register conceptual mastery nodes
        for kn in updated_data.updated_knowledge_nodes:
            node = models.KnowledgeNode(
                user_id=user_profile.id,
                concept=kn.concept,
                category=kn.category,
                mastery_score=min(0.98, max(0.0, kn.mastery_score_delta)),
                dependencies_json=json.dumps({
                    "prerequisites": kn.prerequisites or [],
                    "difficulty_level": kn.difficulty_level or "مقدماتی",
                    "key_terms": kn.key_terms or []
                }, ensure_ascii=False)
            )
            db.add(node)
            logger.log_success(f"  ✦ {kn.concept} ({kn.category}) — {node.mastery_score*100:.0f}% [Level: {kn.difficulty_level}]")

        db.commit()
        logger.log_success("=== Complete Rebuild Sync Complete! All widgets refreshed! ===")
        
        return {"status": "success", "message": "Knowledge base rebuilt successfully."}

    except Exception as e:
        logger.log_error(f"Manual rebuild failed for user {user_id}: {str(e)}")
        db.rollback()
        raise e

async def nightly_profile_updater():
    """
    Asynchronous background scheduler that wakes up at 00:00 Asia/Tehran time
    every day to update profiles for users who have unprofiled learning logs.
    """
    import asyncio
    import datetime
    try:
        import zoneinfo
    except ImportError:
        from backports import zoneinfo  # Fallback for old python versions if any, though python 3.9+ has it.
        
    tehran_tz = zoneinfo.ZoneInfo("Asia/Tehran")
    logger.log_info("Nightly profile updater background scheduler started.")
    
    while True:
        try:
            now = datetime.datetime.now(tehran_tz)
            # Calculate duration to next 00:00 (end of day) in Tehran TZ
            tomorrow = now + datetime.timedelta(days=1)
            next_run = datetime.datetime(tomorrow.year, tomorrow.month, tomorrow.day, 0, 0, 0, tzinfo=tehran_tz)
            sleep_seconds = (next_run - now).total_seconds()
            
            logger.log_info(f"Nightly updater scheduled: sleeping for {sleep_seconds:.1f} seconds until 00:00 Tehran time.")
            await asyncio.sleep(sleep_seconds)
            
            # Woken up! Run profiling for all users with unprofiled events
            logger.log_info("Nightly updater: Waking up to process unprofiled learning event logs...")
            db = database.SessionLocal()
            try:
                # Find all user IDs with unprofiled logs
                unprofiled_users = db.query(models.LearningEventLog.user_id).filter(
                    models.LearningEventLog.is_profiled == False
                ).distinct().all()
                
                if unprofiled_users:
                    logger.log_info(f"Nightly updater: Found {len(unprofiled_users)} users with unprofiled events. Starting updates...")
                    for (user_profile_id,) in unprofiled_users:
                        # Map user_profile_id back to user_id
                        prof = db.query(models.UserProfile).filter(models.UserProfile.id == user_profile_id).first()
                        if prof:
                            logger.log_info(f"Nightly updater: Triggering incremental profiling for user_id {prof.user_id}...")
                            try:
                                run_profiling_background_task(prof.user_id)
                            except Exception as run_ex:
                                logger.log_error(f"Nightly updater: Profiling failed for user_id {prof.user_id}: {str(run_ex)}")
                else:
                    logger.log_info("Nightly updater: No unprofiled events found.")
            except Exception as db_ex:
                logger.log_error(f"Nightly updater database error: {str(db_ex)}")
            finally:
                db.close()
                
        except Exception as loop_ex:
            logger.log_error(f"Nightly updater loop error: {str(loop_ex)}")
            await asyncio.sleep(60)  # Sleep 1 minute before retrying on general errors to avoid tight looping
