import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from app.database import SessionLocal
from app import models
from app.logger import logger

def reset():
    db = SessionLocal()
    try:
        nodes_deleted = db.query(models.KnowledgeNode).delete()
        cp = db.query(models.CognitiveProfile).first()
        if cp:
            cp.cognitive_data_json = "{}"
            cp.interests_json = "[]"
            cp.global_learning_velocity = 1.0
        db.commit()
        logger.log_success(f"Deleted {nodes_deleted} old knowledge nodes and reset cognitive profile.")
    except Exception as e:
        logger.log_error(str(e))
    finally:
        db.close()

if __name__ == "__main__":
    reset()
