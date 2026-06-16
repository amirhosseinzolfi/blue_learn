# Frontend Integration Guide

## Quick Reference: New Course Schema

### API Response Changes

#### GET /courses/ and GET /courses/{id}

**New fields in response:**
```javascript
{
  id: number,
  title: string,                    // Full title
  short_title: string,              // 3-6 words
  description: string,              // OLD field (kept for compatibility)
  course_description: string,       // NEW detailed description
  level: string,                    // "beginner", "intermediate", "advanced", "beginner_to_intermediate"
  hours: number,                    // OLD field (kept for compatibility)
  total_estimated_hours: number,    // NEW field
  sessions: number,                 // Total session count
  target_user_summary: string,      // NEW: "Python beginner building AI apps"
  course_goal: string,              // NEW: "Build a working agent"
  learning_outcomes: string[],      // NEW: Array of outcomes
  prerequisites: string[],          // NEW: Array of prerequisites
  progress: number,
  color: string,
  cover_image: string,
  items: [                          // Sessions array
    {
      id: number,
      session_id: string,           // NEW: "s_1", "s_2"
      title: string,
      chapter: string,
      chapter_id: string,           // NEW: "ch_1", "ch_2"
      description: string,          // NEW: Session description
      learning_objectives: string[], // NEW: Array of objectives
      key_concepts: string[],       // NEW: Array of concepts
      is_completed: boolean,
      content: string,
      study_time: number
    }
  ]
}
```

### POST /chat/course-generator Response

**New structure:**
```javascript
{
  is_complete: boolean,
  chat_response: string,
  course_data: {
    title: string,
    short_title: string,
    level: string,
    total_estimated_hours: number,
    target_user_summary: string,
    course_goal: string,
    course_description: string,
    learning_outcomes: string[],
    prerequisites: string[],
    chapters: [                     // RENAMED from "outline"
      {
        chapter_id: string,         // NEW
        title: string,
        description: string,
        sessions: [                 // RENAMED from "items"
          {
            session_id: string,     // NEW
            title: string,
            description: string,
            learning_objectives: string[],  // NEW
            key_concepts: string[]          // NEW
          }
        ]
      }
    ]
  }
}
```

## Code Migration Examples

### 1. Displaying Course Overview

**Before:**
```javascript
<div>
  <h1>{course.title}</h1>
  <p>{course.description}</p>
  <p>Level: {course.level}</p>
  <p>Duration: {course.hours} hours</p>
</div>
```

**After:**
```javascript
<div>
  <h1>{course.title}</h1>
  <p className="subtitle">{course.short_title}</p>
  
  <div className="course-meta">
    <span>🎯 {course.course_goal}</span>
    <span>👤 {course.target_user_summary}</span>
    <span>⏱️ {course.total_estimated_hours} hours</span>
    <span>📊 {course.level}</span>
  </div>
  
  <p>{course.course_description}</p>
  
  <div className="learning-outcomes">
    <h3>📚 What You'll Learn:</h3>
    <ul>
      {course.learning_outcomes?.map((outcome, i) => (
        <li key={i}>{outcome}</li>
      ))}
    </ul>
  </div>
  
  <div className="prerequisites">
    <h3>✅ Prerequisites:</h3>
    <ul>
      {course.prerequisites?.map((prereq, i) => (
        <li key={i}>{prereq}</li>
      ))}
    </ul>
  </div>
</div>
```

### 2. Displaying Session Card

**Before:**
```javascript
<div className="session-card">
  <h3>{session.title}</h3>
  <p>Chapter: {session.chapter}</p>
</div>
```

**After:**
```javascript
<div className="session-card">
  <div className="session-header">
    <span className="session-id">{session.session_id}</span>
    <span className="chapter-badge">{session.chapter}</span>
  </div>
  
  <h3>{session.title}</h3>
  <p className="session-description">{session.description}</p>
  
  {session.learning_objectives && (
    <div className="objectives">
      <h4>🎯 Learning Objectives:</h4>
      <ul>
        {session.learning_objectives.map((obj, i) => (
          <li key={i}>{obj}</li>
        ))}
      </ul>
    </div>
  )}
  
  {session.key_concepts && (
    <div className="concepts">
      <h4>🔑 Key Concepts:</h4>
      <div className="concept-tags">
        {session.key_concepts.map((concept, i) => (
          <span key={i} className="tag">#{concept}</span>
        ))}
      </div>
    </div>
  )}
</div>
```

### 3. Creating Course from Chat Response

**Before:**
```javascript
const createCourse = async (courseData) => {
  const payload = {
    short_title: courseData.short_title,
    description: courseData.description,
    level: courseData.level,
    hours: courseData.hours,
    sessions: courseData.sessions,
    outline: courseData.outline,  // Array of chapters
    generate_cover: true
  };
  
  await api.post('/courses/', payload);
};
```

**After:**
```javascript
const createCourse = async (courseData) => {
  const payload = {
    title: courseData.title,
    short_title: courseData.short_title,
    level: courseData.level,
    total_estimated_hours: courseData.total_estimated_hours,
    target_user_summary: courseData.target_user_summary,
    course_goal: courseData.course_goal,
    course_description: courseData.course_description,
    learning_outcomes: courseData.learning_outcomes,
    prerequisites: courseData.prerequisites,
    chapters: courseData.chapters,  // Array of chapters with sessions
    generate_cover: true
  };
  
  await api.post('/courses/', payload);
};
```

### 4. Grouping Sessions by Chapter

**Before:**
```javascript
const groupedSessions = course.items.reduce((acc, item) => {
  if (!acc[item.chapter]) acc[item.chapter] = [];
  acc[item.chapter].push(item);
  return acc;
}, {});
```

**After (with chapter_id):**
```javascript
const groupedSessions = course.items.reduce((acc, item) => {
  const key = item.chapter_id || item.chapter;
  if (!acc[key]) {
    acc[key] = {
      id: item.chapter_id,
      title: item.chapter,
      sessions: []
    };
  }
  acc[key].sessions.push(item);
  return acc;
}, {});
```

## UI Component Suggestions

### Course Card Component
```javascript
const CourseCard = ({ course }) => (
  <div className="course-card">
    <img src={course.cover_image} alt={course.title} />
    <div className="course-info">
      <h3>{course.short_title}</h3>
      <p className="target-user">{course.target_user_summary}</p>
      <div className="course-stats">
        <span>⏱️ {course.total_estimated_hours}h</span>
        <span>📚 {course.sessions} sessions</span>
        <span>📊 {course.level}</span>
      </div>
      <div className="progress-bar">
        <div style={{ width: `${course.progress}%` }} />
      </div>
    </div>
  </div>
);
```

### Session Detail Component
```javascript
const SessionDetail = ({ session }) => (
  <div className="session-detail">
    <div className="session-meta">
      <span className="badge">{session.session_id}</span>
      <span className="badge">{session.chapter}</span>
    </div>
    
    <h1>{session.title}</h1>
    <p className="description">{session.description}</p>
    
    <div className="objectives-section">
      <h2>🎯 Learning Objectives</h2>
      <ul>
        {session.learning_objectives?.map((obj, i) => (
          <li key={i}>{obj}</li>
        ))}
      </ul>
    </div>
    
    <div className="concepts-section">
      <h2>🔑 Key Concepts</h2>
      <div className="tags">
        {session.key_concepts?.map((concept, i) => (
          <span key={i} className="tag">{concept}</span>
        ))}
      </div>
    </div>
    
    <div className="content-section">
      <ReactMarkdown>{session.content}</ReactMarkdown>
    </div>
  </div>
);
```

## Backward Compatibility

For old courses without new fields, use fallbacks:
```javascript
const displayTitle = course.title || course.short_title;
const displayDescription = course.course_description || course.description;
const displayHours = course.total_estimated_hours || course.hours;
const displayOutcomes = course.learning_outcomes || [];
const displayPrereqs = course.prerequisites || [];
```

## Testing Checklist

- [ ] Course list displays new fields
- [ ] Course detail shows learning outcomes
- [ ] Course detail shows prerequisites
- [ ] Session cards show objectives
- [ ] Session cards show key concepts
- [ ] Course creation works with new structure
- [ ] Old courses still display correctly
- [ ] Progress tracking still works
- [ ] Search/filter works with new fields

## Common Issues & Solutions

**Issue:** `learning_outcomes` is undefined
**Solution:** Add null check: `course.learning_outcomes?.map(...)`

**Issue:** Old courses missing new fields
**Solution:** Use fallbacks or default values

**Issue:** JSON parsing errors
**Solution:** Backend handles JSON parsing, frontend receives arrays directly

**Issue:** Chapter grouping broken
**Solution:** Use `chapter_id` as primary key, fallback to `chapter` name
