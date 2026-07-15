import sys
import os
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal, run_migrations
from app.services.profile_service import rebuild_user_cognitive_profile
from app.logger import logger

def run():
    run_migrations()
    db = SessionLocal()
    try:
        logger.log_info("Initiating historical user profile sync via unified profile service...")
        from app import models
        user = db.query(models.User).first()
        if not user:
            logger.log_error("No users found in database to sync.")
            return
        result = rebuild_user_cognitive_profile(db, user.id)
        logger.log_success(result.get("message", "Knowledge profile sync successfully completed!"))
    except Exception as e:
        logger.log_error(f"Knowledge sync script execution failed: {str(e)}")
    finally:
        db.close()

if __name__ == "__main__":
    run()
