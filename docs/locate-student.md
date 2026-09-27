# Locating a student: `locateStudent(student_id, timestamp) => hive_room_id`

How to answer "which physical room is student X in at time T" from Hive data,
what the existing System-B90 code already does, and where the gaps are.

## TL;DR

A Hive room is a `Class` with `type == "Room"`, so `hive_room_id` is a
`Class.id`. Check these three sources in order of precedence:

1. **Scheduled event** (the answer for any time the student has a class
   scheduled): a Hive `Event` with `start <= T < end` whose `attendees`
   include one of the student's classes and whose `room` is set gives
   `event.room`.
2. **Home room** (fallback for any other time): the `Room`-type class the
   student is seated in, `Seating(hanich=student, classroom.type == Room)`.
3. **Status overlay** (optional): if the student's status at T is
   `Toilet`, `Home`, `Medical` or another "away" status, they are not in any
   room. Return `None` or flag the result.

No existing service does this. The pieces are already in `pyhive`
(`get_schedule_events`, event attendees, classes, seating, users), so this
needs one function, not a new package (see [Recommendation](#recommendation)).

## Hive data model (source: `Hive/core/core`)

| Concept | Model | Notes |
|---|---|---|
| Room | `management.Class` with `type=ClassType.Room` | Same table as student groups (`type="Student Group"`). Names are unique. |
| Student ↔ class membership | `management.Seating` (through table for `Class.users`) | A student has seats in their Room class (x/y, optional `hostname` of the workstation) and in each Student Group. There is no history, only the current membership. |
| Scheduled event | `schedule.Event` | `start`, `end`, `room` (FK to a Room class, nullable), `attendees` (M2M to `Class` via `EventAttendee`), `hidden_from_students`. |
| Event source | `schedule/ics.py` `load_events` (Celery `update_schedule`, when `HIVE_SCHEDULE_MODE=EXTERNAL`) | ICS `LOCATION` maps to a Room class **by name** (it is auto-created if missing). Attendee emails map to a Class **by `Class.email`**. |
| Student status | `CourseUser.status` + `status_date` | `Present, Raised Hand, Toilet Request, Toilet, Personal Talk, Work Talk, Medical, Prayer, Room, Home`. |
| Status history | `management.UserHistory` (`user`, `time`, `status`, …) | Written on assignment recalculation and auto-toilet release, **not on every status change**, so it is only a partial time series. |
| Workstation | `CourseUser.hostname`, `Seating.hostname` | `Program.auto_room` ("move students to rooms based on hostname") exists as a flag but **has no implementation** anywhere in Hive. `ClassViewSet.auto_seat` matches seats to users by hostname only when someone calls it. |

## Algorithm

Implemented twice, once per language, with the same rules and the same test
cases:

| | Python (pyhive) | TypeScript (hive-core) |
|---|---|---|
| Pure resolver | `pyhive.locate.resolve_location(class_ids, room_ids, events, at)` | `resolveLocation(classIds, roomIds, events, at)` |
| Client wrapper | `pyhive.locate.locate_student(client, student_id, at)` | `locateStudent(client, studentId, at)` |
| Tests | `tests/test_locate.py` | `tests/unit/locate.test.ts` |

The resolver is a pure function over data both clients already fetch
(student class ids, Room class ids, and events in a ±1 day window, since the
API filters by containment, not overlap). It picks a roomed event covering
`at` whose attendees include one of the student's classes. A Student Group
match beats a Room-class match, and after that the later start wins. With no
such event, it falls back to the lowest-id Room class the student sits in.
**If you change a rule, change both files and both test suites.**

The status overlay (step 3) is deliberately left to callers. For "now", use
`student.status`. For a past T, use the latest `UserHistory` row with
`time <= T`, and treat the answer as best-effort, because that history is
sparse.

## Caveats and gotchas

- **Room ids are only Hive ids for Hive rooms.** bluz also has *custom*
  rooms (`RoomSource.Custom`, stored in Mongo) with no Hive `Class`. An event
  placed in one of them has no `hive_room_id`.
- **The Hive `Event` table is only as good as the ICS feed.** Events arrive
  via `load_events` (ICS). bluz does **not** push its events into Hive
  `Event`; it pushes Lessons, LessonRules and `classes/{id}/lesson/`
  activations. If the ICS feed is not bluz's calendar, bluz-only events are
  invisible to this algorithm (see the bluz option below).
- **Attendee resolution goes through `Class.email`.** A group without an
  email in Hive never gets attendees from ICS, so its events match nobody.
- **Membership is current-state only.** Seating has no history, so for a past
  T the answer assumes the student was in the same groups and home room then.
- **Permissions.** Event `start`/`end`/`lesson__id` filters exist only for
  Segel clearance (`EventSegel` in `schedule/filtersets.py`). Use a staff or
  service account.
- **Timezones.** Compare in UTC. Hive stores tz-aware datetimes, and
  `start_local_date` is the local (`hive_local_date`) date if you want a
  day-scoped query.
- **Overlaps are real.** Two events can cover one group at the same time,
  which is why the tie-break exists. Log when it has to choose.

## What already exists in System-B90

| Repo | What it does | Reusable? |
|---|---|---|
| **madash** `src/components/students-provider.tsx` | `student.room` = name of the Room-type class the student belongs to (home room; `'Unknown'` if none). Static, ignores time. | Step 2 only. |
| **bluz** `ui/src/api-server/student-view.ts` | Projects one day of *bluz* events (Mongo) with `rooms` and `courses` for the student view. Doesn't resolve a single student. | Data source for option B below. |
| **bluz** `ui/src/api-server/hive/lesson-sync.ts` | Maps bluz course (shuffle) to a Hive Student Group **by name** (`classIdByName`). | This is the join key for option B. |
| **Samkasotron** `app/hive_service.py` | Resolves mentees → Student Group names via a class cache. Its schedule comes from `luzapp` (a git schedule repo), not from Hive events. It has no room logic. | Student → groups pattern only. |
| **pyhive** `client/schedule.py`, `client/seating.py` | Typed clients for events, event-attendees, classes, seating, users. | Everything step 1 and step 2 need. |

## Two possible schedule sources

- **A. Hive `Event` (recommended default).** This is fully in Hive, the ids
  are already `hive_room_id`, and it is simple. It depends on the ICS feed
  being complete.
- **B. bluz events.** These are richer and are the planning source of truth.
  Join event `courses` → course name → Hive Student Group by name, and event
  `rooms` (`source == Hive`) → Class id. Custom rooms have no Hive id. This
  needs bluz's Mongo/API per iteration.

Start with A. Add B as a second resolver behind the same interface only if
events turn out to be missing from Hive.

## Recommendation

This is **not complex enough for a new package.** It lives in pyhive and
hive-core, next to the clients it uses. A natural next step is a batch
variant (`locate_students`) that fetches events and classes once for many
students. Consider a
dedicated "hive-resolvers" package only if more derived queries pile up
(e.g. "who is in room R at T", instructor location, historical occupancy)
and need shared caching. Even then, it should sit on top of pyhive rather
than duplicate it.
