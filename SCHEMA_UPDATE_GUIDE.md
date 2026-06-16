# Course Schema Update Documentation

## Overview
The course generation system has been upgraded with a more detailed and structured schema that provides richer metadata for courses, chapters, and sessions.

## What Changed

### 1. Course Schema (CourseGenerationSchema)

**Old Fields:**
- `short_title`
- `level` (Persian)
- `hours`
- `sessions`
- `description`
- `outline` (list of chapters)

**New Fields:**
- `title` - Full descriptive course title
- `short_title` - Concise 3-6 word title
- `level` - English format (beginner, intermediate, advanced, beginner_to_intermediate)
- `total_estimated_hours` - Total hours needed
- `target_user_summary` - Brief description of ideal student
- `course_goal` - Main objective of the course
- `course_description` - Detailed explanation of what will be taught
- `learning_outcomes` - List of 4-6 key outcomes
- `prerequisites` - List of required knowledge/skills
- `chapters` - Array of chapters (renamed from `outline`)

### 2. Chapter Schema (OutlineChapterSchema)

**Old Fields:**
- `title`
- `description`
- `items` (list of sessions)

**New Fields:**
- `chapter_id` - Unique identifier (ch_1, ch_2, etc.)
- `title`
- `description`
- `sessions` - Array of sessions (renamed from `items`)

### 3. Session Schema (OutlineItemSchema)

**Old Fields:**
- `title`
- `description`

**New Fields:**
- `session_id` - Unique identifier (s_1, s_2, etc.)
- `title`
- `description`
- `learning_objectives` - List of 2-4 specific objectives
- `key_concepts` - List of 2-5 key concepts

## Database Changes

### New Columns in `courses` Table:
- `course_description` (TEXT)
- `total_estimated_hours` (INTEGER)
- `target_user_summary` (TEXT)
- `course_goal` (TEXT)
- `learning_outcomes` (TEXT) - JSON array
- `prerequisites` (TEXT) - JSON array

### New Columns in `outline_items` Table:
- `session_id` (TEXT)
- `chapter_id` (TEXT)
- `description` (TEXT)
- `learning_objectives` (TEXT) - JSON array
- `key_concepts` (TEXT) - JSON array

## Migration Steps

1. **Backup your database** (important!)
   ```bash
   cp backend/learning_app.db backend/learning_app.db.backup
   ```

2. **Run the migration script:**
   ```bash
   python migrate_schema.py
   ```

3. **Restart your application:**
   ```bash
   uvicorn main:app --reload --port 8082
   ```

## Example Course Structure

```json
{
  "title": "LangGraph Agent Development for AI Learning Apps",
  "short_title": "LangGraph Agent Development",
  "level": "beginner_to_intermediate",
  "total_estimated_hours": 8,
  "target_user_summary": "Python beginner building an AI learning platform",
  "course_goal": "Build a working course-generator assistant using LangGraph",
  "course_description": "A practical course that teaches how to design, build, and validate a stateful AI course builder agent.",
  "learning_outcomes": [
    "Understand LangGraph workflow design",
    "Create a CourseBrief state object",
    "Build multi-turn conversational course generation",
    "Generate structured course outlines",
    "Validate and save generated courses"
  ],
  "prerequisites": [
    "Basic Python",
    "Basic API knowledge",
    "Basic understanding of LLMs"
  ],
  "chapters": [
    {
      "chapter_id": "ch_1",
      "title": "Understanding the Course Builder Agent",
      "description": "Learn the product logic and architecture of a conversational course generator.",
      "sessions": [
        {
          "session_id": "s_1",
          "title": "Why Course Generation Needs a Workflow",
          "description": "Understand why a course builder must ask questions before generating content.",
          "learning_objectives": [
            "Differentiate simple prompting from workflow-based generation",
            "Understand the CourseBrief concept"
          ],
          "key_concepts": [
            "CourseBrief",
            "Stateful workflow",
            "User goal extraction"
          ]
        }
      ]
    }
  ]
}
```

## Frontend Updates Needed

The frontend needs to be updated to:

1. **Display new course metadata:**
   - Show `learning_outcomes` as a list
   - Show `prerequisites` as a list
   - Display `course_goal` and `target_user_summary`

2. **Display session details:**
   - Show `learning_objectives` for each session
   - Show `key_concepts` for each session
   - Display session `description`

3. **Update course creation flow:**
   - Handle the new `chapters` structure (instead of `outline`)
   - Handle `sessions` array (instead of `items`)

## API Changes

### POST /courses/
**Request body now expects:**
```json
{
  "title": "string",
  "short_title": "string",
  "level": "string",
  "total_estimated_hours": 0,
  "target_user_summary": "string",
  "course_goal": "string",
  "course_description": "string",
  "learning_outcomes": ["string"],
  "prerequisites": ["string"],
  "chapters": [
    {
      "chapter_id": "string",
      "title": "string",
      "description": "string",
      "sessions": [
        {
          "session_id": "string",
          "title": "string",
          "description": "string",
          "learning_objectives": ["string"],
          "key_concepts": ["string"]
        }
      ]
    }
  ],
  "generate_cover": false
}
```

### GET /courses/ and GET /courses/{course_id}
**Response now includes:**
- All new course fields
- All new session fields in `items` array

## Backward Compatibility

- Old courses will still work but won't have the new fields populated
- The migration script only adds columns, doesn't modify existing data
- Old `description` field is preserved and mapped to `course_description`
- Old `hours` field is preserved and mapped to `total_estimated_hours`

## Testing

After migration, test:
1. Creating a new course via chat
2. Viewing course details
3. Generating session content
4. Listing all courses

## Rollback

If you need to rollback:
1. Stop the application
2. Restore the backup: `cp backend/learning_app.db.backup backend/learning_app.db`
3. Revert code changes using git
