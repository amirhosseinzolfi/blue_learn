import sys, os, json
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import database, models, agents
from logger import logger

def run():
    db = database.SessionLocal()
    try:
        # 1. Ensure user profile exists
        user_profile = db.query(models.UserProfile).first()
        if not user_profile:
            user_settings = db.query(models.UserSettings).first()
            name = user_settings.name if user_settings else "کاربر"
            bg = user_settings.background_experience if user_settings else ""
            user_profile = models.UserProfile(name=name, background_experience=bg, primary_goals="یادگیری و توسعه فردی")
            db.add(user_profile)
            db.commit()
            db.refresh(user_profile)
            logger.log_success(f"Created UserProfile for: {name}")

        # 2. Sync settings -> profile
        user_settings = db.query(models.UserSettings).first()
        if user_settings:
            user_profile.name = user_settings.name or user_profile.name
            user_profile.age = user_settings.age or user_profile.age
            user_profile.education_level = user_settings.education or user_profile.education_level
            user_profile.background_experience = user_settings.background_experience or user_profile.background_experience
            db.commit()
            logger.log_success("Synced UserSettings -> UserProfile")

        # 3. Ensure cognitive profile exists
        if not user_profile.cognitive_profile:
            cp = models.CognitiveProfile(user_id=user_profile.id, cognitive_data_json="{}", interests_json="[]",
                                          recommended_topics_json="[]", strength_areas_json="[]")
            db.add(cp)
            db.commit()
            db.refresh(user_profile)

        # 4. Delete old nodes to rebuild fresh
        deleted = db.query(models.KnowledgeNode).filter(models.KnowledgeNode.user_id == user_profile.id).delete()
        db.commit()
        logger.log_info(f"Cleared {deleted} old knowledge nodes for fresh rebuild.")

        # 5. Gather ALL historical data
        completed_items = db.query(models.OutlineItem).filter(models.OutlineItem.is_completed == True).all()
        all_courses = db.query(models.Course).all()
        logger.log_info(f"Analyzing {len(completed_items)} completed sessions across {len(all_courses)} courses...")

        if not completed_items:
            logger.log_error("No completed sessions found. Complete some lessons first!")
            return

        courses_info = []
        for c in all_courses:
            total_study_time = sum(item.study_time for item in c.items)
            session_count = len(c.items)
            outline_titles = [item.title for item in sorted(c.items, key=lambda x: x.order)]
            outline_str = ", ".join(outline_titles) if outline_titles else "فاقد سرفصل"
            courses_info.append(
                f"- دوره: '{c.title}' | سطح: '{c.level or 'نامشخص'}' | توضیحات: '{c.description or ''}' | "
                f"کل زمان مطالعه دوره: {total_study_time} ثانیه | تعداد کل جلسات: {session_count} | "
                f"سرفصل‌های کل دوره: [{outline_str}]"
            )
        courses_str = "\n".join(courses_info) if courses_info else "هیچ دوره‌ای ثبت نشده است."

        completed_sessions_str = "\n".join([
            f"- درس تکمیل‌شده: '{item.title}' | دوره: '{item.course.title}' | زمان مطالعه: {item.study_time}s"
            for item in completed_items
        ])
        
        logs_str = f"""
=== دوره‌های کاربر (User Courses) ===
{courses_str}

=== وضعیت جلسات تکمیل‌شده (Completed Outline Items) ===
{completed_sessions_str}
"""
        
        profile_str = (
            f"نام: {user_profile.name}, سن: {user_profile.age}, "
            f"تحصیلات: {user_profile.education_level}, "
            f"پیش‌زمینه: {user_profile.background_experience}, "
            f"اهداف: {user_profile.primary_goals}"
        )
        cog_profile = user_profile.cognitive_profile
        # Clear cognitive profile items to prevent anchoring bias during a manual rebuild/refresh
        current_state_str = "وضعیت شناختی قبلی وجود ندارد. سرعت یادگیری، تمرکز، و شاخص حفظ اطلاعات را کاملاً از نو بر اساس لاگ‌ها و سرفصل‌های تکمیل‌شده از نو دقیقاً محاسبه کنید."

        logger.log_process_start("Historical Cognitive Profiling", f"Analyzing ALL {len(completed_items)} sessions for full Persian knowledge base")

        updated_data = agents.run_cognitive_profiler(profile_str, current_state_str, logs_str)

        if not updated_data:
            logger.log_error("Profiler returned None. Check the API key and model.")
            return

        # 6. Save all new rich fields
        cog_profile.global_learning_velocity = updated_data.global_learning_velocity
        cog_profile.attention_span_minutes = updated_data.attention_span_minutes
        cog_profile.retention_index = updated_data.retention_index
        cognitive_data_dict = {
            "learning_style": {
                "hands_on": updated_data.ls_hands_on,
                "visual": updated_data.ls_visual,
                "theoretical": updated_data.ls_theoretical,
                "self_directed": updated_data.ls_self_directed
            },
            "personality_traits": {
                "persistence": updated_data.pt_persistence,
                "patience_with_errors": updated_data.pt_patience,
                "learning_curiosity": updated_data.pt_curiosity,
                "preferred_session_length": updated_data.pt_session_length
            }
        }
        cog_profile.cognitive_data_json = json.dumps(cognitive_data_dict, ensure_ascii=False)
        cog_profile.interests_json = json.dumps(updated_data.new_interests, ensure_ascii=False)
        cog_profile.learning_style_summary = updated_data.learning_style_summary
        cog_profile.personality_summary = updated_data.personality_summary
        cog_profile.strength_areas_json = json.dumps(updated_data.strength_areas, ensure_ascii=False)
        cog_profile.recommended_topics_json = json.dumps(updated_data.recommended_topics, ensure_ascii=False)

        logger.log_success(f"Saved cognitive profile. Got {len(updated_data.updated_knowledge_nodes)} knowledge nodes.")
        logger.log_info(f"Interests: {updated_data.new_interests}")
        logger.log_info(f"Strengths: {updated_data.strength_areas}")
        logger.log_info(f"Recommendations: {updated_data.recommended_topics}")

        # 7. Register all knowledge nodes
        for kn in updated_data.updated_knowledge_nodes:
            node = models.KnowledgeNode(
                user_id=user_profile.id,
                concept=kn.concept,
                category=kn.category,
                mastery_score=min(1.0, kn.mastery_score_delta),
                confidence_level=kn.confidence_score
            )
            db.add(node)
            logger.log_success(f"  ✦ {kn.concept} ({kn.category}) — {kn.mastery_score_delta*100:.0f}%")

        db.commit()
        logger.log_success("=== Historical sync complete! All widgets are now populated with rich Persian data ===")

    except Exception as e:
        import traceback
        logger.log_error(f"Sync failed: {str(e)}")
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    run()
