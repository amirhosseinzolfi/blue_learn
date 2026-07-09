# Global Courses Feature — Implementation Plan

## Overview
Add a new "Global Courses" capability where users can publish their generated courses to a shared global catalog, and any logged-in user can browse/enroll in those courses. When enrolled, a raw clone (fresh state — no content generated, no progress) is added to the enrolling user's own Courses page.

Per your answers: entry point is a button on the Courses page (no sidebar item), publish action lives in the course card ⋮ menu, and after enroll the user stays on the Global page with an "Enrolled ✓" state.

---

## 1. Backend — Data Model & Migration

**`app/models.py`** — Add `is_published` and `published_at` columns to the `Course` model:
```python
is_published = Column(Boolean, default=False, nullable=False, index=True)
published_at = Column(DateTime, nullable=True)
```

**`app/database.py`** — Extend `run_migrations()` to add these columns to the existing `courses` table via `ALTER TABLE` (idempotent try/except, matching the existing pattern at lines 150–166):
```python
("is_published", "BOOLEAN DEFAULT 0"),
("published_at", "DATETIME"),
```
No data backfill needed — existing courses default to `is_published=0`.

---

## 2. Backend — Schemas

**`app/schemas.py`**:
- Extend `CourseOut` with `is_published: bool = False` and `published_at: Optional[str] = None`.
- Add a new `GlobalCourseOut` schema (lightweight card data — id, title, short_title, description, course_description, level, sessions, total_estimated_hours, target_user_summary, cover_image, author_name, published_at, enrollment_count). Used for the global browse list.

---

## 3. Backend — Endpoints (new file `app/api/endpoints/global_courses.py`)

All endpoints reuse `get_current_user` for auth. A helper serializes a course into `GlobalCourseOut` (joining the author's username from `User` and counting enrollments via `CourseEnrollment` — see model below).

1. `GET /global-courses/?search=...` — Browse published courses (any user). Optional search filter on title/description. Excludes courses the current user authored (they already own those) and courses the current user is already enrolled in (so they don't re-enroll). Returns `List[GlobalCourseOut]`.
2. `POST /courses/{course_id}/publish` — Owner publishes their course. Sets `is_published=True`, `published_at=now`. Only the owner can do this (404/403 otherwise). Returns updated `CourseOut`.
3. `POST /courses/{course_id}/unpublish` — Owner unpublishes. Sets flags back. Returns updated `CourseOut`. (Keeps existing enrollments intact — once enrolled, the clone is independent.)
4. `POST /global-courses/{course_id}/enroll` — Clone the course (raw state) for the current user:
   - Guard: if already enrolled (existing `CourseEnrollment` row OR already owns a course cloned from this `source_course_id`), return a friendly error.
   - Create a new `Course` row owned by the current user, copying all curriculum fields (title, short_title, description, course_description, level, hours, total_estimated_hours, sessions, target_user_summary, course_goal, learning_outcomes, prerequisites, color, cover_image) and setting `source_course_id` to the original.
   - Clone all `OutlineItem` rows with `content=None`, `is_completed=False`, `study_time=0`, `completed_at=None` (raw first-time state — exactly like a freshly generated course).
   - Create a `CourseEnrollment` record linking user → original course (for the "already enrolled" guard and enrollment count).
   - Return the new `CourseOut` so the frontend has full data.
5. `GET /global-courses/enrolled-ids` — Returns the list of original course IDs the current user has enrolled in. Used by the frontend to mark cards as "Enrolled ✓" without refetching.

**`app/api/router.py`** — `api_router.include_router(global_courses.router)`.

---

## 4. Backend — Enrollment-tracking model

Add to **`app/models.py`**:
```python
class CourseEnrollment(Base):
    __tablename__ = "course_enrollments"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    source_course_id = Column(Integer, ForeignKey("courses.id"), index=True, nullable=False)
    cloned_course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    enrolled_at = Column(DateTime, default=datetime.datetime.utcnow)
```
And add `source_course_id` column to `Course` (nullable, FK to courses) to track the lineage of cloned courses — this is what powers the "already enrolled" guard independent of the enrollment table.

Add `CREATE TABLE IF NOT EXISTS course_enrollments` + `ALTER TABLE courses ADD COLUMN source_course_id INTEGER` to `run_migrations()`.

---

## 5. Frontend — API layer (`static/js/api.js`)

Add methods:
```js
fetchGlobalCourses:    (search = '') => api.get(`/global-courses/?search=${encodeURIComponent(search)}`),
publishCourse:         (id) => api.post(`/courses/${id}/publish`),
unpublishCourse:       (id) => api.post(`/courses/${id}/unpublish`),
enrollGlobalCourse:    (id) => api.post(`/global-courses/${id}/enroll`),
fetchEnrolledIds:      () => api.get(`/global-courses/enrolled-ids`),
```

---

## 6. Frontend — New view `static/js/components/views/GlobalCoursesView.jsx`

A new view (RTL, matching the app's dark/glassmorphism theme — same classes as `CoursesView.jsx`):
- **Header**: title "دوره‌های عمومی" + a search input (filters live as you type, debounced).
- **Grid**: `GlobalCourseCard` components. Each card shows cover image, title, short description, level/sessions/hours chips (same style as `CourseCard`), author name, and enrollment count.
- **Card actions**:
  - If not enrolled → "ثبت‌نام در دوره" (enroll) button. On success, card flips to "ثبت‌نام شد ✓" + a secondary "مشاهده دوره" button (stays on page).
  - If already enrolled → disabled "ثبت‌نام شد ✓" state + "مشاهده دوره" button that navigates to the cloned course in the Courses view.
- **Empty state**: friendly message when no global courses match the search.
- Loading skeleton while fetching.

**Wire into `index.html`** — add `<script src="/assets/js/components/views/GlobalCoursesView.jsx">` after `CoursesView.jsx` (preserving load order).

---

## 7. Frontend — App integration (`static/js/app.jsx`)

- New view name: `'global'` (not in sidebar — reachable via button).
- New state: `globalCourses`, `enrolledIds`, `globalSearch`, `isGlobalLoading`.
- New handlers:
  - `openGlobalCourses()` — sets `currentView='global'`, fetches list + enrolled IDs.
  - `enrollCourse(courseId)` — calls `api.enrollGlobalCourse`, updates `enrolledIds`, shows toast, **does not** navigate (stays per your choice).
  - `viewEnrolledCourse(clonedCourseId)` — reuses `selectCourse` then switches to `currentView='courses'`.
- Render block: `{currentView === 'global' && <GlobalCoursesView ... />}` alongside the other views.
- Update `CoursesView.jsx` empty-state/list header to include a **"جستجوی دوره‌های عمومی"** button that calls `onOpenGlobalCourses`.

---

## 8. Frontend — Publish action in CourseCard dropdown (`CourseCard.jsx`)

- Add a "انتشار عمومی" (Publish globally) item to the ⋮ dropdown menu.
- Show dynamic label: if `course.is_published` → "لغو انتشار" (Unpublish) instead.
- Add `onPublish(course)` / `onUnpublish(course)` props passed through from `app.jsx`.
- Handler in `app.jsx`: calls `api.publishCourse`/`unpublishCourse`, refreshes the course list, shows a toast.

---

## 9. Files to change

**Backend (5 files):**
- `app/models.py` — add `is_published`, `published_at`, `source_course_id` on Course; new `CourseEnrollment` model.
- `app/database.py` — migration for new columns + enrollment table.
- `app/schemas.py` — extend `CourseOut`; add `GlobalCourseOut`.
- `app/api/endpoints/global_courses.py` — NEW: browse/publish/unpublish/enroll endpoints.
- `app/api/router.py` — register the new router.
- `app/api/endpoints/courses.py` — add `is_published`/`published_at` to the 3 `CourseOut` dict constructions (create/list/get).

**Frontend (5 files):**
- `static/js/api.js` — 5 new API methods.
- `static/js/components/views/GlobalCoursesView.jsx` — NEW: the global browse view + card.
- `static/js/components/views/CoursesView.jsx` — add "Search Global Courses" button.
- `static/js/components/views/CourseCard.jsx` — add publish/unpublish menu item.
- `static/js/app.jsx` — new view state, handlers, render block, pass-through props.
- `static/index.html` — add the new view script tag.

---

## Notes & edge cases handled
- **Raw clone**: enrolling copies the curriculum but resets every session to `content=None, is_completed=False, study_time=0` — identical to a freshly generated course, so the AI coach, micro-course generation, and study timer all work normally on the clone.
- **No re-enroll**: double guard via `CourseEnrollment` table + `source_course_id` lineage.
- **Author's own course**: hidden from their global list (they already own it).
- **Unpublish safety**: unpublishing does NOT delete already-cloned courses; enrolled users keep their copies.
- **Theme consistency**: all new UI uses the existing dark/`primary` purple glassmorphism classes, RTL Persian labels, `getCourseColor` for theming, and the existing toast/button/card patterns — no new CSS framework or design language.

This plan is fully self-contained and uses only the patterns already present in the codebase (SQLAlchemy models + manual migrations, FastAPI routers with `get_current_user`, React views loaded via babel script tags, axios `api` object).