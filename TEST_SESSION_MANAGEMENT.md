# Session Management Bug Fixes - Testing Guide

## Implementation Checklist
- [x] Added `is_completed` field to IntentSession model
- [x] Updated delete logic to prevent in-progress session deletion
- [x] Added `mark_intent_session_completed()` service function
- [x] Added POST `/api/v1/sessions/{id}/complete` endpoint
- [x] Updated DELETE endpoint to return 409 for in-progress sessions
- [x] Added schema migration for new `is_completed` column
- [x] Frontend displays "当前会话" for untitled/in-progress sessions
- [x] Frontend disables delete button for in-progress sessions
- [x] Frontend marks session complete on successful compilation
- [x] Frontend refreshes session list after marking complete

## Test Scenarios

### Test 1: New Session Creation & "当前会话" Display
1. Click "创建会话" button
2. Verify new session appears in list with label "当前会话"
3. Verify is_completed=false in session object

### Test 2: Delete Button Disabled for In-Progress Sessions
1. Hover over delete button on "当前会话" session
2. Verify button is greyed out (disabled state)
3. Verify tooltip says "进行中的会话无法删除"
4. Click delete button - should do nothing (or show error message)

### Test 3: Compilation Completes Session
1. Create new session
2. Enter prompt in AI editor
3. Click compile
4. Submit and wait for rendering to complete
5. Verify:
   - Session marked as completed
   - Title auto-generated from prompt
   - Session list refreshed
   - Delete button becomes enabled

### Test 4: Delete Completed Session
1. After compilation completes, verify delete button is enabled
2. Click delete button
3. Confirm deletion in dialog
4. Verify session removed from list

### Test 5: API Endpoints
- GET `/api/v1/sessions` → Returns sessions with `is_completed` field
- POST `/api/v1/sessions` → Creates session with `is_completed=false`
- GET `/api/v1/sessions/{id}` → Returns session detail with `is_completed`
- PATCH `/api/v1/sessions/{id}` → Updates title without changing `is_completed`
- POST `/api/v1/sessions/{id}/complete` → Sets `is_completed=true`
- DELETE `/api/v1/sessions/{id}` → Returns 409 if `is_completed=false`, succeeds if `is_completed=true`

### Test 6: Database Migration
1. Stop dashboard
2. Delete SQLite database file (if exists): `runtime/studio.db`
3. Restart dashboard
4. Verify new tables created with `is_completed` column
5. Create a session and verify field is set to false by default

## Manual Test Commands (Optional)

```bash
# Start dashboard
python dashboard.py

# Test API in another terminal
curl http://localhost:8090/api/v1/sessions

# Create session
curl -X POST http://localhost:8090/api/v1/sessions \
  -H "Content-Type: application/json" \
  -d '{"title": null, "meta": null}'

# Get session detail
curl http://localhost:8090/api/v1/sessions/{session_id}

# Mark as completed
curl -X POST http://localhost:8090/api/v1/sessions/{session_id}/complete

# Try delete
curl -X DELETE http://localhost:8090/api/v1/sessions/{session_id}
```

## Expected Error Responses

### 409 Conflict - Deleting In-Progress Session
```json
{
  "detail": "Can only delete completed sessions; this session is still in progress"
}
```

### 404 Not Found - Session not found
```json
{
  "detail": "Session not found"
}
```

## Frontend Error Handling
- Delete error: Displayed in `studioSessionsError` toast
- Mark complete error: Silently logged to console (non-blocking)
- Session list refresh: Automatic after mark complete succeeds

## Known Limitations
- In-progress sessions cannot be permanently deleted (by design)
- Session state is only checked on delete action, not on UI render for real-time sync
- May need manual refresh if session is marked complete from another tab

## Rollback Plan
If issues arise:
1. Revert schema migration in `init.py` (remove is_completed migration)
2. Set `is_completed=true` as default in delete check (comment out the check)
3. Restart dashboard and database will auto-recreate tables without new field
