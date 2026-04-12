# Scheduling microservice — frontend API reference

Base URL (local Docker default): `http://localhost:5009`  
API prefix: **`/api/v1`**  
OpenAPI: **`GET /openapi.json`**, Swagger UI: **`GET /docs`**, ReDoc: **`GET /redoc`**

Unless noted, requests and responses use **JSON** with **`Content-Type: application/json`**. Field names are **snake_case** (e.g. `academic_year`, `schedule_run_id`).

---

## Authentication (current dev behaviour)

Endpoints under **`/api/v1/instructors/me/*`**, **`PATCH .../sessions/...`**, and **`POST .../publish`** require the authenticated user id:

| Header | Value |
|--------|--------|
| **`X-User-Id`** | Integer — must match the instructor’s `instructor_user_id` from Auth (or mock data). |

Configurable via env `DEV_USER_ID_HEADER` (default `X-User-Id`).  
If the header is missing or not an integer: **`401`** or **`400`**.

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

Runs scheduling (loads lessons/rooms from external services or mock), persists a new **schedule run**, returns full result.

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

- **`422`**: validation or upstream-style message (e.g. empty rooms from Location).

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
| `instructor_user_id` | int | no | Filter by instructor. |

**Response** `200` — array of **`SessionOut`**

| Field | Type |
|--------|------|
| `id` | int |
| `lesson_id` | int |
| `instructor_user_id` | int |
| `room_id` | int |
| `room_name` | string |
| `timeslot_id` | string — see **timeslot_id** enum |
| `day` | string |
| `start_time` | string (`HH:MM`) |
| `end_time` | string (`HH:MM`) |
| `preference_match` | bool |
| `sequence_index` | int — occurrence index for multi–times-per-week lessons |
| `course_code` | string \| null |
| `course_title` | string \| null |
| `enrollment` | int |
| `room_capacity` | int |

**Errors:** **`404`** — run not found.

---

### `GET /api/v1/schedules/{schedule_run_id}/unscheduled`

**Response** `200` — array of **`UnscheduledOut`**

| Field | Type |
|--------|------|
| `id` | int |
| `lesson_id` | int |
| `instructor_user_id` | int |
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

**Response** `200` — `SessionOptionsResponse`

```json
{
  "options": [
    {
      "room_id": 1,
      "room_name": "B101",
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

Only allowed when run **`status`** is **`completed`**. Sets status to **`published`** and writes an audit row (`action`: **`publish`**).

**Response** `200` — `PublishResponse`

| Field | Type |
|--------|------|
| `schedule_run_id` | int |
| `status` | string — `"published"` |

**Errors:** **`404`**, **`422`** (e.g. not `completed`).

---

## Instructor preferences (`/instructors/me`)

Profile is unique per **`(instructor_user_id, academic_year, semester)`**.

### `GET /api/v1/instructors/me/preferences`

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
| `instructor_user_id` | int |
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

### `PUT /api/v1/instructors/me/preferences`

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

Validation errors often return **`422`** with a body containing `detail` (array of `{ loc, msg, type }` for request validation).

Application errors for conflicts/not found may use a simple **`detail`**: string message.

---

*Generated from the Scheduling microservice codebase. When in doubt, use **`GET /openapi.json`** as the source of truth for schemas.*
