# Scheduling microservice — frontend API reference

Base URL (Docker maps host **5010** → container **8000**): **`http://localhost:5010`**  
API prefix: **`/api/v1`**  
OpenAPI: **`GET /openapi.json`**, Swagger UI: **`GET /docs`**, ReDoc: **`GET /redoc`**  
Swagger **Authorize** (optional **HTTPBearer**): paste a JWT to send **`Authorization: Bearer …`** on **`/api/v1/...`** calls; the backend uses it for **Attendance** on that request (else **`ATTENDANCE_ACCESS_TOKEN`**). Scheduling routes stay callable without a token.

Unless noted, requests and responses use **JSON** with **`Content-Type: application/json`**. Field names are **snake_case** (e.g. `academic_year`, `schedule_run_id`).

---

## Overview

### Ports (Docker Compose)

| Item | Value |
|------|--------|
| Host URL | `http://localhost:5010` |
| Container | `uvicorn` listens on **`8000`** inside the image |
| PostgreSQL | Exposed as **`5431`→5432** by default (`POSTGRES_HOST_PORT`) |

Rebuild the API image after code changes (`docker compose build`) so `/docs` matches the running backend.

The container entrypoint runs **`alembic upgrade head`** before **`uvicorn`**, so PostgreSQL schema updates apply on startup.

### Environment variables

Configure via **`.env`** or Compose `environment` (see **`.env.example`**). Typical variables:

| Variable | Purpose |
|----------|---------|
| `DATABASE_URL` | SQLAlchemy PostgreSQL URL. |
| `USE_MOCK_DATA` | `false` (**default**): lessons from Attendance, rooms from Location, instructors from Auth (`role=Instructor`). Set `true` only to force local CSV mocks. |
| `ATTENDANCE_BASE_URL` | Attendance service origin, **no trailing slash** (default deploy: `http://13.60.31.141:5000/attendance`; local: `http://localhost:5008` or `http://host.docker.internal:5008`). |
| `ATTENDANCE_ACCESS_TOKEN` | Optional **JWT** (raw or `Bearer …`) sent as **`Authorization`** on every outbound Attendance request. This service’s own HTTP API does **not** require auth. |
| `LOCATION_BASE_URL` | **Full Location API root** ending with **`/api/v1`** — see **Location service (rooms)** below. |
| `AUTH_BASE_URL` | Auth service host (e.g. `http://localhost:5001`). Used for **`/api/auth/...`** when calling Auth from the backend. |
| `AUTH_SERVICE_ACCESS_TOKEN` | **Bearer** token with **admin** role, required for **`GET /api/auth/users-by-role/Instructor`** when `USE_MOCK_DATA=false`. |
| `HTTP_TIMEOUT_SECONDS` | HTTP client timeout for upstream calls (default `30`). |
| `CORS_ORIGINS` | Comma-separated allowed origins, or `*` (credentials disabled for `*`). |
| `DEV_USER_ID_HEADER` | Header name for instructor id (default **`X-User-Id`**). |
| `LOG_DIR` | Directory for text logs (default `logs`). |
| `LOG_FILENAME` | Active log file (default `scheduling.txt`). |
| `LOG_LEVEL` | Root log level (default `INFO`). |
| `LOG_BACKUP_COUNT` | Number of **daily** rotated log files to keep (default **`7`**); older files deleted. |

### External microservices (integration summary)

| Service | Role in Scheduling |
|---------|---------------------|
| **Attendance** | **`GET /api/admin/lessons/scheduling`** — lesson catalog for **`POST /schedules/generate`**. **`POST /api/admin/lessons/{lessonId}/sessions/generate`** — called when **`POST .../publish`** runs. |
| **Location** | **`GET {LOCATION_BASE_URL}/rooms`** — all rooms for the constraint solver (see below). |
| **Auth** | **`GET {AUTH_BASE_URL}/api/auth/users-by-role/Instructor`** with **`Authorization: Bearer`** — used to load the instructor directory and validate lesson instructor ids during schedule generation. |

Instructor and actor user ids are stored and returned as **strings** (Auth **UUID** or legacy numeric string) so they align with **`X-User-Id`**.

---

## Location service (rooms)

Scheduling does **not** embed building CRUD; it only **lists rooms** for generation.

**Request (anonymous GET is enough):**

```http
GET {LOCATION_BASE_URL}/rooms
```

**`LOCATION_BASE_URL`** must include the path through **`/api/v1`** (no trailing slash on the full value).

**Gateway example** (gateway forwards `/location/...` to Location; your base includes `/location` + `/api/v1`):

| Component | Example |
|-----------|---------|
| Base | `http://51.20.193.29:5000/location/api/v1` |
| Rooms | `http://51.20.193.29:5000/location/api/v1/rooms` |

**Direct LocationService** (no gateway): e.g. `http://localhost:5005/api/v1` → **`GET .../api/v1/rooms`**.

**Response:** JSON array of room objects (camelCase in JSON). The backend maps to `RoomDto`: `id`, `name`, `number`, `capacity`, `roomType` (numeric enum), `buildingId`, optional `buildingName`. Wrapper shapes `{ result | rooms | data | items: [...] }` are also accepted.

---

## Logging

- Output goes to **stdout** and to a **rotating file** under **`LOG_DIR`/`LOG_FILENAME`** (default **`logs/scheduling.txt`**).
- **Midnight** daily rotation; **`LOG_BACKUP_COUNT`** (default **7**) keeps that many archived daily files; older files are removed.
- **`app.http`**: logs **422** validation failures and **4xx/5xx** HTTP application errors with **`errors`**, **`detail`**, and request **body** when captured — use this to debug beyond the single-line `uvicorn.access` entry.
- Unhandled exceptions are logged with a **stack trace** under the root/`app` loggers.

---

## Authentication (current dev behaviour)

Endpoints **`GET` / `POST` / `PUT /api/v1/instructors/preferences`**, **`PATCH .../sessions/...`**, and **`POST .../publish`** require the instructor id header:

| Header | Value |
|--------|--------|
| **`X-User-Id`** | **UUID string** (Auth user id, e.g. `00000000-0000-0000-0000-000000000041`) or **legacy numeric string** for mock/older data — must match `instructor_user_id` on lessons / Auth. |

Configurable via env `DEV_USER_ID_HEADER` (default `X-User-Id`).  
If the header is missing: **`401`**. If the value is not a valid UUID and not a numeric string: **`400`**.

`POST /api/v1/schedules/generate` does **not** require `X-User-Id` today (intended for admin/trusted callers).

---

## Enums and controlled vocabularies

### `schedule_run.status` (string)

Stored and returned as one of:

| Value | Meaning |
|--------|--------|
| **`draft`** | Initial placeholder (rarely returned for completed flows). |
| **`running`** | Generation in progress. |
| **`completed`** | Generation finished successfully; sessions/unscheduled rows persisted. |
| **`failed`** | Run failed (e.g. upstream error); see `error_message`. |
| **`published`** | Published after `POST .../publish` (only from **`completed`**). |

### `schedule_change_logs.action` (string, audit)

Written by the backend when auditing:

| Value | Meaning |
|--------|--------|
| **`manual_patch`** | `PATCH` on a scheduled session. |
| **`publish`** | `POST .../publish`. |

(Not exposed as a dedicated read API yet; documented for future audit UI.)

### `timeslot_id` (string)

Must be one of the canonical ids below (Mon–Fri, four slots per day). Used in session rows and in **`PATCH`** / **`options`**.

| `timeslot_id` | `day` | `start` | `end` |
|-----------------|--------|---------|--------|
| `MON_0800` | Monday | 08:00 | 09:30 |
| `MON_1000` | Monday | 10:00 | 11:30 |
| `MON_1300` | Monday | 13:00 | 14:30 |
| `MON_1500` | Monday | 15:00 | 16:30 |
| `TUE_0800` … `TUE_1500` | Tuesday | (same pattern) | |
| `WED_0800` … `WED_1500` | Wednesday | (same pattern) | |
| `THU_0800` … `THU_1500` | Thursday | (same pattern) | |
| `FRI_0800` … `FRI_1500` | Friday | (same pattern) | |

### Instructor preferences — `preferred_days` (list of strings)

Use **capitalized English day names** (matches the scheduler):

- `Monday`, `Tuesday`, `Wednesday`, `Thursday`, `Friday`

### Instructor preferences — `preferred_time_categories` (list of strings)

Must be a subset of:

| Value | Meaning (local time window) |
|--------|------------------------------|
| **`morning`** | Slot start hour &lt; 12 |
| **`afternoon`** | Start hour ≥ 12 and &lt; 17 |
| **`evening`** | Start hour ≥ 17 |

(Aligned with `app/scheduler/engine.py` time buckets.)

### `strict` (instructor preferences, boolean)

- **`true`**: scheduler only considers slots that satisfy **both** preferred days and preferred time categories (if those lists are non-empty).
- **`false`**: preferences influence ordering only; slots outside preferences may still be assigned.

---

## Health & discovery

### `GET /health`

**Response** `200`: `{ "status": "ok" }`

### `GET /`

**Response** `307`: redirect to `/docs`.

---

## Schedules

### `POST /api/v1/schedules/generate`

Runs scheduling: loads **lessons** from Attendance (**`GET {ATTENDANCE_BASE_URL}/api/admin/lessons/scheduling`**), **rooms** from Location (**`GET {LOCATION_BASE_URL}/rooms`**), and **instructors** from Auth (**`GET {AUTH_BASE_URL}/api/auth/users-by-role/Instructor`**) when **`USE_MOCK_DATA=false`**; otherwise uses **`app/mock_data`** CSVs. Persists a new **schedule run** and returns the full result.

**Upstream alignment:** Lesson **`instructorUserId`** values should use the same string form as Auth (**UUID**) and as **`X-User-Id`** so preference rows apply during solving.

**Request body**

| Field | Type | Required | Notes |
|--------|------|----------|--------|
| `academic_year` | string | yes | 1–32 chars; used with semester for preference lookup. |
| `semester` | string | yes | 1–32 chars (e.g. `Fall`, `Spring`). |

**Response** `200` — `ScheduleGenerateResponse`

| Field | Type | Notes |
|--------|------|--------|
| `schedule_run_id` | int | Use for subsequent GET/PATCH/publish. |
| `status` | string | Usually `completed` or `failed`. |
| `academic_year` | string | Echo from request. |
| `semester` | string | Echo from request. |
| `summary` | object | See below. |
| `scheduled_sessions` | `SessionOut[]` | |
| `unscheduled_lessons` | `UnscheduledOut[]` | |

`summary`:

| Field | Type |
|--------|------|
| `total_lessons` | int |
| `scheduled_lesson_count` | int |
| `unscheduled_lesson_count` | int |
| `scheduled_session_count` | int |
| `preference_match_sessions` | int |

**Errors**

- **`422`**: Invalid JSON body (missing `academic_year` / `semester`), or **`422`** from application validation (e.g. no rooms from Location). Check the **`app.http`** log line for **`errors`** and **`body`**.
- **`500`**: Unhandled failure during generation; see server logs.

---

### `GET /api/v1/schedules/{schedule_run_id}`

**Path:** `schedule_run_id` — integer.

**Response** `200` — `ScheduleRunDetailResponse`

| Field | Type |
|--------|------|
| `id` | int |
| `academic_year` | string |
| `semester` | string |
| `status` | string — see **schedule_run.status** enum |
| `started_at` | string (ISO 8601) \| null |
| `completed_at` | string (ISO 8601) \| null |
| `error_message` | string \| null |
| `summary` | object \| null — same shape as generate `summary` when present |

**Errors:** **`404`** — run not found.

---

### `GET /api/v1/schedules/{schedule_run_id}/sessions`

**Query parameters**

| Name | Type | Required | Notes |
|------|------|----------|--------|
| `day` | string | no | Exact day name, e.g. `Monday`. |
| `instructor_user_id` | string (UUID or numeric) | no | Filter by instructor (same normalization as `X-User-Id`). |

**Response** `200` — array of **`SessionOut`**

| Field | Type | Notes |
|--------|------|--------|
| `id` | int | |
| `lesson_id` | int | |
| `instructor_user_id` | string | |
| `room_id` | int | |
| `room_name` | string | Built from Location **`buildingName`** + **`number`** (e.g. building ends with a single letter `A` and number `101` → **`A101`**). Resolved from current Location data on each GET. |
| `timeslot_id` | string | See **timeslot_id** enum |
| `day` | string |
| `start_time` | string (`HH:MM`) |
| `end_time` | string (`HH:MM`) |
| `preference_match` | bool |
| `sequence_index` | int — occurrence index for multi–times-per-week lessons |
| `course_code` | string \| null |
| `course_title` | string \| null |
| `enrollment` | int |
| `room_capacity` | int |

**Errors:** **`404`** — run not found. **`422`** — invalid `instructor_user_id` query (must be a UUID or numeric string, same rules as **`X-User-Id`**).

---

### `GET /api/v1/schedules/{schedule_run_id}/unscheduled`

**Response** `200` — array of **`UnscheduledOut`**

| Field | Type |
|--------|------|
| `id` | int |
| `lesson_id` | int |
| `instructor_user_id` | string |
| `times_per_week` | int |
| `sessions_assigned` | int |
| `sessions_needed` | int |
| `reason` | string |
| `partial_sessions` | array \| null — partial slot assignments if any |
| `course_code` | string \| null |
| `course_title` | string \| null |
| `enrollment` | int |

**Errors:** **`404`** — run not found.

---

### `PATCH /api/v1/schedules/{schedule_run_id}/sessions/{session_id}`

**Headers:** **`X-User-Id`** (required).

**Rules**

- Run must be **`completed`** or **`published`**.
- At least one of `room_id` or `timeslot_id` must be sent.
- Validates room id, timeslot id, room capacity vs enrollment, instructor double-booking, room double-booking for that run.

**Request body** — `SessionPatchRequest`

| Field | Type | Required | Notes |
|--------|------|----------|--------|
| `room_id` | int \| null | no | Omit or null to keep current room. |
| `timeslot_id` | string \| null | no | Omit or null to keep current slot; must be a valid **timeslot_id**. |

**Response** `200` — `SessionPatchResponse`

| Field | Type |
|--------|------|
| `session` | `SessionOut` |
| `message` | string — default `"Updated"` |

**Errors**

- **`404`** — run or session not found.
- **`409`** — conflict (capacity, room/instructor overlap).
- **`422`** — validation (wrong status, unknown room/slot, empty patch body).

---

### `GET /api/v1/schedules/{schedule_run_id}/sessions/{session_id}/options`

Valid `(room_id, timeslot_id)` pairs for manual editing, given the rest of the run.

Each option’s **`room_name`** uses the same **building + room number** display rule as **`SessionOut`** (e.g. **`A101`**).

**Response** `200` — `SessionOptionsResponse`

```json
{
  "options": [
    {
      "room_id": 1,
      "room_name": "A101",
      "timeslot_id": "MON_0800",
      "day": "Monday",
      "start": "08:00",
      "end": "09:30"
    }
  ]
}
```

**Errors:** **`404`**, **`422`** (same run status rules as PATCH).

---

### `POST /api/v1/schedules/{schedule_run_id}/publish`

**Headers:** **`X-User-Id`** (required).

Only allowed when run **`status`** is **`completed`**. For each distinct **`lesson_id`** in the run’s scheduled sessions, the backend calls the Attendance service:

`POST {ATTENDANCE_BASE_URL}/api/admin/lessons/{lessonId}/sessions/generate`

The Scheduling API accepts **`from_date` / `to_date`** (snake_case, ISO dates) in JSON; the client to Attendance sends **`fromDate` / `toDate`** (camelCase) plus **`weeklySlots`** (day + start/end times from this run). If all calls succeed, the run becomes **`published`** and an audit row is written (`action`: **`publish`**). Configure **`ATTENDANCE_BASE_URL`** (Compose default: **`http://13.60.31.141:5000/attendance`**).

**Request body** — `PublishRequest`

| Field | Type | Required | Notes |
|--------|------|----------|--------|
| `from_date` | string (ISO date) | yes | Inclusive start for generated class sessions |
| `to_date` | string (ISO date) | yes | Inclusive end; span must be ≤ 731 days |
| `topic` | string \| null | no | Passed to Attendance for every generated session (camelCase **`topic`** on the upstream JSON) |

**Response** `200` — `PublishResponse`

| Field | Type |
|--------|------|
| `schedule_run_id` | int |
| `status` | string — `"published"` |
| `attendance_generations` | array — per-lesson counts from Attendance (`created_count`, `skipped_duplicate_count`) |

**Errors:** **`404`**, **`422`** (validation or Attendance HTTP error surfaced as message).

---

## Instructor preferences (`/instructors/preferences`)

Profile is unique per **`(instructor_user_id, academic_year, semester)`**. The instructor is **not** in the URL; send their user id in the header below.

OpenAPI **`operation_id`** values: **`get_instructor_preferences`**, **`post_instructor_preferences`**, **`put_instructor_preferences`** (stable for codegen).

### `GET /api/v1/instructors/preferences`

**Headers:** **`X-User-Id`** (required).

**Query parameters**

| Name | Type | Required |
|------|------|----------|
| `academic_year` | string | yes |
| `semester` | string | yes |

**Response** `200` — `PreferenceProfileResponse`

| Field | Type |
|--------|------|
| `id` | int |
| `instructor_user_id` | string |
| `academic_year` | string |
| `semester` | string |
| `strict` | bool |
| `notes` | string \| null |
| `preferred_days` | string[] — see **preferred_days** |
| `preferred_time_categories` | string[] — see **preferred_time_categories** |
| `created_at` | string (ISO 8601) \| null |
| `updated_at` | string (ISO 8601) \| null |

**Errors:** **`404`** — no profile for that term.

---

### `POST /api/v1/instructors/preferences`

**Headers:** **`X-User-Id`** (required).

Same behavior as **`PUT`** below: creates or replaces the profile and its day/time rows for **`(academic_year, semester)`**. Use **`POST`** when your client convention treats preference saves as submissions rather than full replacements.

**Request body** — `PreferenceProfileUpsert` (same table as PUT)

**Response** `200` — same shape as GET (`PreferenceProfileResponse`).

---

### `PUT /api/v1/instructors/preferences`

**Headers:** **`X-User-Id`** (required).

Creates or replaces the profile and its day/time rows for that term.

**Request body** — `PreferenceProfileUpsert`

| Field | Type | Required | Notes |
|--------|------|----------|--------|
| `academic_year` | string | yes | 1–32 chars |
| `semester` | string | yes | 1–32 chars |
| `strict` | bool | no | default `false` |
| `notes` | string \| null | no | |
| `preferred_days` | string[] | no | default `[]` |
| `preferred_time_categories` | string[] | no | default `[]` |

**Response** `200` — same shape as GET (`PreferenceProfileResponse`).

---

## Attendance API (external service)

This section documents attendance endpoints used alongside this scheduling service.

**Route user ids:** For `api/students/{studentId}` and `api/instructors/{instructorId}`, ids are auth-service user GUIDs passed in the route. In current deployments, route/user auth matching checks may be disabled.

**JSON enums:** `AcademicSemester` (where it appears on nested lesson payloads) uses `JsonStringEnumConverter`; use `"Fall"`, `"Spring"`, or `"Summer"` in JSON.

**Attendance status strings** (DTO string values):

| Value | Meaning |
|--------|--------|
| `Present` | On time |
| `Late` | Late |
| `Absent` | Absent |
| `Excused` | Excused |

### Student (`/api/students/{studentId}`)

#### `GET /api/students/{studentId}/enrollments`

Lists enrolled lessons with aggregated attendance counts per lesson.

Response: `StudentLessonDto[]`

| Field | Type | Notes |
|--------|------|--------|
| `lessonId` | int | |
| `lessonName` | string | Course title |
| `lessonCode` | string | Course code |
| `totalSessions` | int | |
| `presentCount` | int | |
| `lateCount` | int | |
| `absentCount` | int | |
| `excusedCount` | int | |

#### `GET /api/students/{studentId}/lessons/{lessonId}/attendance`

Student per-session attendance rows for one lesson.

Response: `StudentAttendanceDto[]`

| Field | Type | Notes |
|--------|------|--------|
| `attendanceId` | int | |
| `sessionId` | int | |
| `sessionStartTime` | datetime | |
| `sessionEndTime` | datetime | |
| `lessonName` | string | |
| `lessonCode` | string | |
| `status` | string | `Present` / `Late` / `Absent` / `Excused` |
| `firstScanAt` | datetime? | |
| `lastScanAt` | datetime? | |
| `isManuallyAdjusted` | bool | |
| `instructorNote` | string? | |

#### `POST /api/students/{studentId}/attendance/scan`

Marks attendance by QR token for that student (same behavior as `attendance/qr/scan`). If `studentId` in body is empty, route `studentId` is used.

Body: `QrScanRequestDto`  
Response: `QrScanResponseDto`

#### `POST /api/students/{studentId}/attendance/qr/scan`

Validates QR token and records attendance for `studentId` from payload/route.

Body: `QrScanRequestDto`

| Field | Type | Notes |
|--------|------|--------|
| `studentId` | guid | Route id used if omitted in body |
| `token` | string | Signed QR payload from instructor |
| `qrContext` | object? | Optional consistency checks |
| `deviceInfo` | string? | Optional client metadata |

`qrContext`:

| Field | Type | Notes |
|--------|------|--------|
| `sessionId` | int? | Must match token session if provided |
| `roundCount` | int? | Must match token activation id if provided |
| `instructorJwt` | string? | Instructor id in JWT must match session instructor if provided |

Response: `QrScanResponseDto`

| Field | Type | Notes |
|--------|------|--------|
| `success` | bool | |
| `errorCode` | string? | Machine-readable reject code |
| `message` | string | Human-readable outcome |
| `studentId` | guid | Resolved student id |
| `sessionId` | int | |
| `activationId` | int? | |
| `validScanCount` | int | |
| `status` | string? | Attendance status on success |
| `scannedAt` | datetime? | |

Typical errors: invalid/expired token, session not found, activation inactive, outside attendance window, not enrolled, replay token.

### Instructor (`/api/instructors/{instructorId}/sessions`)

#### `POST /api/instructors/{instructorId}/sessions/{sessionId}/attendance/activate`

Opens attendance for the session (creates/activates an activation record).

Response: `AttendanceActivationResultDto`

| Field | Type |
|--------|------|
| `sessionId` | int |
| `isAttendanceActive` | bool |
| `attendanceActivatedAt` | datetime? |
| `attendanceDeactivatedAt` | datetime? |
| `message` | string |

#### `POST /api/instructors/{instructorId}/sessions/{sessionId}/attendance/deactivate`

Closes attendance for the session.

Response: `AttendanceActivationResultDto`

#### `POST /api/instructors/{instructorId}/sessions/{sessionId}/qr-token`

Issues a short-lived signed token for session QR display.

Response: `QrTokenResponseDto`

| Field | Type |
|--------|------|
| `sessionId` | int |
| `activationId` | int |
| `token` | string |
| `expiresAt` | datetime |

#### `GET /api/instructors/{instructorId}/sessions/{sessionId}/attendance`

Instructor roster for the session.

Response: `AttendanceDto[]`

#### `GET /api/instructors/{instructorId}/sessions/{sessionId}/attendance/summary`

Rollup counts only.

Response: `AttendanceSummaryDto`

| Field | Type |
|--------|------|
| `sessionId` | int |
| `totalStudents` | int |
| `presentCount` | int |
| `lateCount` | int |
| `absentCount` | int |
| `excusedCount` | int |

#### `PATCH /api/instructors/{instructorId}/sessions/{sessionId}/attendance/{studentId}`

Updates one enrolled student attendance row for that session.

Body: `UpdateAttendanceDto`

| Field | Type | Notes |
|--------|------|--------|
| `status` | string | `Present`, `Late`, `Absent`, `Excused` |
| `instructorNote` | string? | Optional |

Response: `AttendanceDto`

#### `POST /api/instructors/{instructorId}/sessions/{sessionId}/attendance/finalize`

Finalizes attendance for the session.

Body: none  
Response: usually `200` / no content.

#### `POST /api/instructors/{instructorId}/sessions/{sessionId}/attendance/bulk-absent`

Marks non-present enrolled students as absent in bulk for that session.

Body: none  
Response: service-defined.

### Admin (`/api/admin`)

#### `GET /api/admin/sessions/{sessionId}/attendance`

Admin roster view (same shape as instructor `AttendanceDto[]`, without instructor ownership check).

Response: `AttendanceDto[]`

#### `PATCH /api/admin/sessions/{sessionId}/attendance/{attendanceId}`

Corrects one attendance row by attendance id.

Body: `AdminAttendanceCorrectionDto`

| Field | Type | Notes |
|--------|------|--------|
| `status` | string | `Present`, `Late`, `Absent`, `Excused` |
| `note` | string? | Optional |

Response: `AttendanceDto`

#### `DELETE /api/admin/sessions/{sessionId}/attendance/{attendanceId}`

Deletes an attendance record.

Response: success per API wrapper conventions.

#### `GET /api/admin/lessons/scheduling`

**Used by the Scheduling microservice** when `USE_MOCK_DATA` is false: loads the lesson catalog (course metadata, instructor assignment, capacity, meetings per week, enrollment) for automated timetable generation.

Response body may be any of:

- a JSON array of lesson objects, or
- an object with a list in `result`, `lessons`, `data`, or `items`, or
- the standard wrapper `{ statusCode?, message?, result: [...] }` (empty `result` means no lessons).

Each lesson object (camelCase in JSON) maps to the Scheduling service’s `SchedulingLessonDto`:

| Field | Type | Notes |
|--------|------|--------|
| `lessonId` | int | |
| `instructorUserId` | string (UUID recommended) | Must align with Auth user id sent as `X-User-Id` |
| `enrollment` | int | Optional; default `0` |
| `maxCapacity` | int | Room sizing; optional, default `0` |
| `timesPerWeek` | int | Sessions to place per week |
| `courseCode` | string | |
| `courseTitle` | string | |
| `lessonType` | string | Optional in practice; default `Section` if omitted (scheduler ignores it). |

### Related session listing (lessons)

Additional Attendance routes (admin/instructor lesson sessions) are defined in the **Attendance** service; paths follow that API’s documentation.

### Quick reference

| Method | Path | Caller |
|--------|------|--------|
| `GET` | `/api/students/{studentId}/enrollments` | Student |
| `GET` | `/api/students/{studentId}/lessons/{lessonId}/attendance` | Student |
| `POST` | `/api/students/{studentId}/attendance/scan` | Student |
| `POST` | `/api/students/{studentId}/attendance/qr/scan` | Student |
| `POST` | `/api/instructors/{instructorId}/sessions/{sessionId}/attendance/activate` | Instructor |
| `POST` | `/api/instructors/{instructorId}/sessions/{sessionId}/attendance/deactivate` | Instructor |
| `POST` | `/api/instructors/{instructorId}/sessions/{sessionId}/qr-token` | Instructor |
| `GET` | `/api/instructors/{instructorId}/sessions/{sessionId}/attendance` | Instructor |
| `GET` | `/api/instructors/{instructorId}/sessions/{sessionId}/attendance/summary` | Instructor |
| `PATCH` | `/api/instructors/{instructorId}/sessions/{sessionId}/attendance/{studentId}` | Instructor |
| `POST` | `/api/instructors/{instructorId}/sessions/{sessionId}/attendance/finalize` | Instructor |
| `POST` | `/api/instructors/{instructorId}/sessions/{sessionId}/attendance/bulk-absent` | Instructor |
| `GET` | `/api/admin/sessions/{sessionId}/attendance` | Admin |
| `PATCH` | `/api/admin/sessions/{sessionId}/attendance/{attendanceId}` | Admin |
| `DELETE` | `/api/admin/sessions/{sessionId}/attendance/{attendanceId}` | Admin |
| `GET` | `/api/admin/lessons/scheduling` | Scheduling service (lesson catalog for generate) |

---

## TypeScript-style type aliases (optional)

```ts
type ScheduleRunStatus = "draft" | "running" | "completed" | "failed" | "published";

type TimeslotId =
  | "MON_0800" | "MON_1000" | "MON_1300" | "MON_1500"
  | "TUE_0800" | "TUE_1000" | "TUE_1300" | "TUE_1500"
  | "WED_0800" | "WED_1000" | "WED_1300" | "WED_1500"
  | "THU_0800" | "THU_1000" | "THU_1300" | "THU_1500"
  | "FRI_0800" | "FRI_1000" | "FRI_1300" | "FRI_1500";

type PreferenceDay = "Monday" | "Tuesday" | "Wednesday" | "Thursday" | "Friday";
type PreferenceTimeCategory = "morning" | "afternoon" | "evening";
```

---

## Error shape (FastAPI)

- **Request validation (`422`):** Response body is typically `{ "detail": [ ... ] }` with Pydantic-style entries (`loc`, `msg`, `type`, `input`). The **`app.http`** logger also records the same **`errors`** array plus the raw **body** (when available) at **WARNING** — use the log file or console for debugging.
- **HTTP exceptions:** `{ "detail": ... }` where `detail` may be a string or structured value depending on the handler.
- **Manual PATCH / conflicts:** **`409`** with a string **`detail`**; **`404`** when the run or session is missing.

---

*Aligned with the Scheduling microservice in this repository. **`GET /openapi.json`** is the source of truth for request/response schemas; rebuild the Docker image after pulling code so `/docs` matches the running process.*
