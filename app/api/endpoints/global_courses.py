import json
import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app import models, database
from app.logger import logger
from app.schemas import GlobalCourseOut, CourseOut, CourseRatingRequest
from app.api.endpoints.auth import get_current_user

router = APIRouter()


def _serialize_global_course(course: models.Course, db: Session, current_user_id: int, include_items: bool = False) -> dict:
    """Serialize a published Course into the GlobalCourseOut payload, including
    rating aggregates, the current user's own rating, and enrollment status.
    When include_items is True, also returns the outline items (for detail page)."""
    # Author username
    author_name = None
    if course.user_id:
        author = db.query(models.User).filter(models.User.id == course.user_id).first()
        if author:
            author_name = author.username

    # Enrollment count for this source course
    enrollment_count = db.query(models.CourseEnrollment).filter(
        models.CourseEnrollment.source_course_id == course.id
    ).count()

    # Is the current user enrolled?
    is_enrolled = db.query(models.CourseEnrollment).filter(
        models.CourseEnrollment.user_id == current_user_id,
        models.CourseEnrollment.source_course_id == course.id
    ).first() is not None

    # Rating aggregates
    rating_row = db.query(
        func.avg(models.CourseRating.rating),
        func.count(models.CourseRating.rating)
    ).filter(models.CourseRating.course_id == course.id).one()
    avg_rating = float(rating_row[0]) if rating_row[0] is not None else 0.0
    rating_count = int(rating_row[1] or 0)

    # Current user's own rating (if any)
    my_rating_row = db.query(models.CourseRating).filter(
        models.CourseRating.user_id == current_user_id,
        models.CourseRating.course_id == course.id
    ).first()
    my_rating = my_rating_row.rating if my_rating_row else None

    # Parse JSON list fields safely
    def _parse_list(raw):
        try:
            return json.loads(raw) if raw else []
        except Exception:
            return []

    result = {
        "id": course.id,
        "title": course.title,
        "short_title": course.short_title,
        "description": course.description,
        "course_description": course.course_description,
        "level": course.level,
        "sessions": course.sessions,
        "total_estimated_hours": course.total_estimated_hours,
        "target_user_summary": course.target_user_summary,
        "course_goal": course.course_goal,
        "learning_outcomes": _parse_list(course.learning_outcomes),
        "prerequisites": _parse_list(course.prerequisites),
        "color": course.color or "purple",
        "cover_image": course.cover_image,
        "author_name": author_name,
        "published_at": course.published_at.isoformat() if course.published_at else None,
        "enrollment_count": enrollment_count,
        "is_enrolled": is_enrolled,
        "avg_rating": round(avg_rating, 2),
        "rating_count": rating_count,
        "my_rating": my_rating,
        "items": None,
    }

    if include_items:
        result["items"] = [
            {
                "id": item.id,
                "session_id": item.session_id,
                "title": item.title,
                "chapter": item.chapter,
                "chapter_id": item.chapter_id,
                "description": item.description,
                "order": item.order,
            }
            for item in sorted(course.items, key=lambda x: x.order)
        ]

    return result


@router.get("/global-courses/", response_model=List[GlobalCourseOut])
def list_global_courses(
    search: Optional[str] = Query(None, description="Optional filter on title/description"),
    sort: str = Query("recent", description="Sort: recent | top_rated | most_enrolled"),
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Lists all globally-published courses authored by other users. Enrolled
    courses are kept in the list but flagged with is_enrolled=True so the user
    can see their status rather than having the card disappear.
    Supports sorting by most recent, highest rated, or most enrolled.
    """
    query = db.query(models.Course).filter(models.Course.is_published == True)

    # Exclude courses authored by the current user (they already own them)
    query = query.filter(models.Course.user_id != current_user.id)

    # Optional search filter on title/description
    if search and search.strip():
        term = f"%{search.strip()}%"
        query = query.filter(
            (models.Course.title.ilike(term)) | (models.Course.description.ilike(term))
        )

    courses = query.all()

    results = []
    for course in courses:
        results.append(_serialize_global_course(course, db, current_user.id))

    # Sort the in-memory payload. avg_rating/enrollment_count are computed above.
    if sort == "top_rated":
        results.sort(key=lambda c: (c["avg_rating"], c["rating_count"]), reverse=True)
    elif sort == "most_enrolled":
        results.sort(key=lambda c: c["enrollment_count"], reverse=True)
    else:  # "recent" — newest publishes first
        results.sort(key=lambda c: c["published_at"] or "", reverse=True)

    return results


@router.get("/global-courses/enrolled-ids")
def list_enrolled_ids(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Returns the original course IDs the current user has enrolled in,
    along with their cloned course IDs so the frontend can navigate to them."""
    enrollments = db.query(models.CourseEnrollment).filter(
        models.CourseEnrollment.user_id == current_user.id
    ).all()
    return [
        {"source_course_id": e.source_course_id, "cloned_course_id": e.cloned_course_id}
        for e in enrollments
    ]


@router.get("/global-courses/{course_id}", response_model=GlobalCourseOut)
def get_global_course(
    course_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Returns the full GlobalCourseOut payload for a single published course
    (used by the global course detail page)."""
    course = db.query(models.Course).filter(
        models.Course.id == course_id,
        models.Course.is_published == True
    ).first()
    if not course:
        raise HTTPException(status_code=404, detail="Global course not found")
    return _serialize_global_course(course, db, current_user.id, include_items=True)


@router.post("/global-courses/{course_id}/rate", response_model=GlobalCourseOut)
def rate_global_course(
    course_id: int,
    payload: CourseRatingRequest,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Submits or updates the current user's 1–5 star rating on a global course."""
    if payload.rating < 1 or payload.rating > 5:
        raise HTTPException(status_code=400, detail="Rating must be between 1 and 5")

    course = db.query(models.Course).filter(
        models.Course.id == course_id,
        models.Course.is_published == True
    ).first()
    if not course:
        raise HTTPException(status_code=404, detail="Global course not found")

    # Upsert: one rating per (user, course)
    existing = db.query(models.CourseRating).filter(
        models.CourseRating.user_id == current_user.id,
        models.CourseRating.course_id == course_id
    ).first()
    if existing:
        existing.rating = payload.rating
    else:
        db.add(models.CourseRating(
            user_id=current_user.id,
            course_id=course_id,
            rating=payload.rating,
            created_at=datetime.datetime.utcnow()
        ))
    db.commit()

    return _serialize_global_course(course, db, current_user.id)


@router.post("/courses/{course_id}/publish", response_model=CourseOut)
def publish_course(
    course_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Publishes a course owned by the current user to the global catalog."""
    course = db.query(models.Course).filter(
        models.Course.id == course_id,
        models.Course.user_id == current_user.id
    ).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    # Cloned courses (with a source_course_id) cannot be re-published globally
    if course.source_course_id is not None:
        raise HTTPException(status_code=400, detail="Cloned courses cannot be published globally")

    course.is_published = True
    course.published_at = datetime.datetime.utcnow()
    db.commit()
    db.refresh(course)
    logger.log_success(f"Course {course_id} published globally by user {current_user.id}")
    return _serialize_course_out(course)


@router.post("/courses/{course_id}/unpublish", response_model=CourseOut)
def unpublish_course(
    course_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Unpublishes a course from the global catalog. Existing enrollments
    (already-cloned copies) are kept intact."""
    course = db.query(models.Course).filter(
        models.Course.id == course_id,
        models.Course.user_id == current_user.id
    ).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    course.is_published = False
    course.published_at = None
    db.commit()
    db.refresh(course)
    logger.log_info(f"Course {course_id} unpublished by user {current_user.id}")
    return _serialize_course_out(course)


@router.post("/global-courses/{course_id}/enroll", response_model=GlobalCourseOut)
def enroll_global_course(
    course_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Enrolls the current user in a globally-published course by cloning it
    in a raw first-time state (no generated content, no progress) into their
    own Courses page. Re-enrollment is a no-op (returns the course with
    is_enrolled=True) so the card stays in the global list.
    """
    source = db.query(models.Course).filter(
        models.Course.id == course_id,
        models.Course.is_published == True
    ).first()
    if not source:
        raise HTTPException(status_code=404, detail="Global course not found")

    # Cannot enroll in your own authored course
    if source.user_id == current_user.id:
        raise HTTPException(status_code=400, detail="You cannot enroll in your own course")

    # Idempotent: if already enrolled, just return the (now is_enrolled) course
    existing = db.query(models.CourseEnrollment).filter(
        models.CourseEnrollment.user_id == current_user.id,
        models.CourseEnrollment.source_course_id == course_id
    ).first()
    if existing:
        db.refresh(source)
        return _serialize_global_course(source, db, current_user.id)

    logger.log_info(f"User {current_user.id} enrolling in global course {course_id}; cloning curriculum...")

    # Clone the course row (raw — not republished)
    cloned_course = models.Course(
        user_id=current_user.id,
        title=source.title,
        short_title=source.short_title,
        description=source.description,
        course_description=source.course_description,
        level=source.level,
        hours=source.hours,
        total_estimated_hours=source.total_estimated_hours,
        sessions=source.sessions,
        target_user_summary=source.target_user_summary,
        course_goal=source.course_goal,
        learning_outcomes=source.learning_outcomes,
        prerequisites=source.prerequisites,
        chat_summary=None,
        color=source.color,
        cover_image=source.cover_image,
        is_published=False,
        published_at=None,
        source_course_id=source.id
    )
    db.add(cloned_course)
    db.commit()
    db.refresh(cloned_course)

    # Clone outline items in raw first-time state (no content, no progress)
    order = 0
    for item in sorted(source.items, key=lambda x: x.order):
        cloned_item = models.OutlineItem(
            course_id=cloned_course.id,
            session_id=item.session_id,
            chapter=item.chapter,
            chapter_id=item.chapter_id,
            title=item.title,
            description=item.description,
            learning_objectives=item.learning_objectives,
            key_concepts=item.key_concepts,
            order=order,
            is_completed=False,
            content=None,
            study_time=0,
            completed_at=None
        )
        db.add(cloned_item)
        order += 1

    # Record enrollment for the guard + count
    enrollment = models.CourseEnrollment(
        user_id=current_user.id,
        source_course_id=source.id,
        cloned_course_id=cloned_course.id,
        enrolled_at=datetime.datetime.utcnow()
    )
    db.add(enrollment)
    db.commit()
    db.refresh(source)

    logger.log_success(f"User {current_user.id} enrolled in course {course_id}; cloned as course {cloned_course.id}")
    return _serialize_global_course(source, db, current_user.id)


def _serialize_course_out(course: models.Course) -> dict:
    """Serialize a Course (with items) into the full CourseOut payload.
    Mirrors the construction used in app/api/endpoints/courses.py."""
    completed = [i for i in course.items if i.is_completed]
    progress = (len(completed) / len(course.items) * 100) if course.items else 0

    def _parse_list(raw):
        try:
            return json.loads(raw) if raw else []
        except Exception:
            return []

    items_with_parsed_json = []
    for item in sorted(course.items, key=lambda x: x.order):
        items_with_parsed_json.append({
            "id": item.id,
            "session_id": item.session_id,
            "title": item.title,
            "chapter": item.chapter,
            "chapter_id": item.chapter_id,
            "description": item.description,
            "learning_objectives": _parse_list(item.learning_objectives),
            "key_concepts": _parse_list(item.key_concepts),
            "order": item.order,
            "is_completed": item.is_completed,
            "content": item.content,
            "study_time": item.study_time
        })

    return {
        "id": course.id,
        "title": course.title,
        "short_title": course.short_title,
        "description": course.description,
        "course_description": course.course_description,
        "level": course.level,
        "hours": course.hours,
        "total_estimated_hours": course.total_estimated_hours,
        "sessions": course.sessions,
        "target_user_summary": course.target_user_summary,
        "course_goal": course.course_goal,
        "learning_outcomes": _parse_list(course.learning_outcomes),
        "prerequisites": _parse_list(course.prerequisites),
        "progress": progress,
        "color": course.color or "purple",
        "cover_image": course.cover_image,
        "is_published": course.is_published,
        "published_at": course.published_at.isoformat() if course.published_at else None,
        "source_course_id": course.source_course_id,
        "items": items_with_parsed_json
    }
