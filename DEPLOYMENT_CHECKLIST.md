# ✅ Deployment Checklist

## Pre-Deployment

- [ ] Read `DEPLOYMENT_GUIDE.md`
- [ ] Backup database: `copy backend\learning_app.db backend\learning_app.db.backup`
- [ ] Ensure Python 3.12+ is installed
- [ ] Ensure all dependencies are installed: `pip install -r requirements.txt`

## Database Migration

- [ ] Run migration script: `python migrate_schema.py`
- [ ] Verify all columns added successfully
- [ ] Check for any error messages
- [ ] Confirm migration completed message appears

## Application Restart

- [ ] Stop any running instances
- [ ] Start application: `uvicorn main:app --reload --port 8082`
- [ ] Verify no startup errors in console
- [ ] Check `server.log` for any issues
- [ ] Confirm application accessible at http://localhost:8082

## Frontend Testing

### Test 1: Course Creation
- [ ] Click "ساخت اولین دوره با هوش مصنوعی بلو"
- [ ] Complete step 1: Topic clarification
- [ ] Complete step 2: Course structure
- [ ] Complete step 3: Personalization
- [ ] Verify step 4: Course preview shows all new fields
- [ ] Accept and create course
- [ ] Verify course created successfully

### Test 2: Course Hero View
- [ ] Open newly created course
- [ ] Verify course title displays
- [ ] Verify target user summary shows (👤)
- [ ] Verify course goal shows in highlighted box (🎯)
- [ ] Verify learning outcomes list displays
- [ ] Verify prerequisites list displays
- [ ] Verify level, hours, sessions badges show
- [ ] Verify progress bar displays

### Test 3: Session View
- [ ] Click on any session
- [ ] Verify session title displays
- [ ] Verify session description shows
- [ ] Verify "Learning Objectives" section displays
- [ ] Verify "Key Concepts" tags display
- [ ] Generate content if not generated
- [ ] Verify main content renders correctly
- [ ] Verify navigation buttons work

### Test 4: Roadmap View
- [ ] Go back to course overview
- [ ] Verify session cards display
- [ ] Verify session descriptions show
- [ ] Verify key concept tags appear (first 3 + counter)
- [ ] Verify chapter badges display
- [ ] Verify completion status shows correctly

### Test 5: Old Courses
- [ ] Open an old course (if any exist)
- [ ] Verify it still displays correctly
- [ ] Verify no errors in console
- [ ] Verify fallbacks work (description, hours)

## API Testing

### Test Course Creation Endpoint
- [ ] POST `/courses/` with new schema
- [ ] Verify response includes all new fields
- [ ] Verify database stores all fields correctly

### Test Course Retrieval
- [ ] GET `/courses/`
- [ ] Verify response includes new fields
- [ ] Verify JSON arrays parse correctly

### Test Single Course
- [ ] GET `/courses/{id}`
- [ ] Verify all new fields present
- [ ] Verify items include session metadata

## Browser Compatibility

- [ ] Test in Chrome/Edge
- [ ] Test in Firefox
- [ ] Test in Safari (if available)
- [ ] Test mobile view (responsive)
- [ ] Test tablet view

## Performance Checks

- [ ] Course list loads quickly
- [ ] Course detail loads quickly
- [ ] Session content generates in reasonable time
- [ ] No console errors
- [ ] No memory leaks
- [ ] Smooth scrolling and animations

## Data Validation

- [ ] Learning outcomes are arrays
- [ ] Prerequisites are arrays
- [ ] Session objectives are arrays
- [ ] Key concepts are arrays
- [ ] All text fields display correctly
- [ ] English content uses LTR
- [ ] Persian content uses RTL

## Edge Cases

- [ ] Course with no learning outcomes
- [ ] Course with no prerequisites
- [ ] Session with no objectives
- [ ] Session with no key concepts
- [ ] Very long course titles
- [ ] Very long descriptions
- [ ] Many learning outcomes (10+)
- [ ] Many key concepts (10+)

## Rollback Plan (If Needed)

- [ ] Stop application
- [ ] Restore backup: `copy backend\learning_app.db.backup backend\learning_app.db`
- [ ] Revert code changes (git)
- [ ] Restart application
- [ ] Verify old version works

## Documentation Review

- [ ] Read `SCHEMA_UPDATE_GUIDE.md`
- [ ] Read `IMPLEMENTATION_SUMMARY.md`
- [ ] Read `FRONTEND_INTEGRATION.md`
- [ ] Read `FRONTEND_CHANGES.md`
- [ ] Read `QUICK_START.md`

## Final Verification

- [ ] All tests passed
- [ ] No errors in logs
- [ ] No console errors
- [ ] UI looks correct
- [ ] Data saves correctly
- [ ] Old courses still work
- [ ] New courses have rich metadata
- [ ] Mobile responsive
- [ ] Performance acceptable

## Post-Deployment

- [ ] Monitor logs for errors
- [ ] Check user feedback
- [ ] Verify AI generates correct structure
- [ ] Monitor database size
- [ ] Check API response times
- [ ] Verify all features working

## Success Criteria

✅ All checklist items completed
✅ No critical errors
✅ New courses display rich metadata
✅ Old courses still functional
✅ UI/UX improved
✅ Performance maintained

## Notes

Date Deployed: _______________
Deployed By: _______________
Issues Found: _______________
Resolution: _______________

---

## Quick Commands Reference

```bash
# Backup
copy backend\learning_app.db backend\learning_app.db.backup

# Migrate
python migrate_schema.py

# Start
uvicorn main:app --reload --port 8082

# Rollback
copy backend\learning_app.db.backup backend\learning_app.db
```

## Support Contacts

- Documentation: See `DEPLOYMENT_GUIDE.md`
- Issues: Check `server.log` and browser console
- Rollback: Follow rollback plan above
