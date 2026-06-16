"""
Database migration script to add new course schema fields.
Run this script to update your existing database with the new columns.
"""
import sqlite3
import os

DB_PATH = "backend/learning_app.db"

def migrate_database():
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("Starting database migration...")
    
    # Add new columns to courses table
    new_course_columns = [
        ("course_description", "TEXT"),
        ("total_estimated_hours", "INTEGER"),
        ("target_user_summary", "TEXT"),
        ("course_goal", "TEXT"),
        ("learning_outcomes", "TEXT"),
        ("prerequisites", "TEXT"),
    ]
    
    for column_name, column_type in new_course_columns:
        try:
            cursor.execute(f"ALTER TABLE courses ADD COLUMN {column_name} {column_type}")
            print(f"✓ Added column '{column_name}' to courses table")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                print(f"⊘ Column '{column_name}' already exists in courses table")
            else:
                print(f"✗ Error adding column '{column_name}': {e}")
    
    # Add new columns to outline_items table
    new_item_columns = [
        ("session_id", "TEXT"),
        ("chapter_id", "TEXT"),
        ("description", "TEXT"),
        ("learning_objectives", "TEXT"),
        ("key_concepts", "TEXT"),
    ]
    
    for column_name, column_type in new_item_columns:
        try:
            cursor.execute(f"ALTER TABLE outline_items ADD COLUMN {column_name} {column_type}")
            print(f"✓ Added column '{column_name}' to outline_items table")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                print(f"⊘ Column '{column_name}' already exists in outline_items table")
            else:
                print(f"✗ Error adding column '{column_name}': {e}")
    
    conn.commit()
    conn.close()
    
    print("\n✓ Database migration completed successfully!")
    print("You can now run the application with the new schema.")

if __name__ == "__main__":
    migrate_database()
