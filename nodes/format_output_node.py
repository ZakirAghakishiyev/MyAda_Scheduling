from typing import Any, Dict, List

from vellum.workflows import BaseNode

from .constraint_solver_node import ConstraintSolverNode

DAY_ORDER = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]


class FormatOutputNode(BaseNode):
    scheduled: List[Dict[str, Any]] = ConstraintSolverNode.Outputs.scheduled
    unscheduled: List[Dict[str, Any]] = ConstraintSolverNode.Outputs.unscheduled

    class Outputs(BaseNode.Outputs):
        schedule_json: dict[str, Any]
        schedule_text: str

    class Display(BaseNode.Display):
        x = 936
        z_index = 4
        icon = "vellum:icon:table"
        color = "blue"

    def run(self) -> BaseNode.Outputs:
        schedule_json = {
            "scheduled": self.scheduled,
            "unscheduled": self.unscheduled,
            "summary": {
                "total_lessons": len(self.scheduled) + len(self.unscheduled),
                "scheduled_count": len(self.scheduled),
                "unscheduled_count": len(self.unscheduled),
            },
        }
        lines = []
        lines.append("=" * 70)
        lines.append("           LESSON SCHEDULE")
        lines.append("=" * 70)
        day_sessions: Dict[str, list] = {d: [] for d in DAY_ORDER}
        for lesson in self.scheduled:
            for session in lesson["sessions"]:
                day_sessions[session["day"]].append(
                    {
                        "start": session["start"],
                        "end": session["end"],
                        "room": session["room"],
                        "crn": lesson["crn"],
                        "instructor": lesson["instructor"],
                        "enrollment": lesson["enrollment"],
                        "capacity": session["room_capacity"],
                    }
                )
        for day in DAY_ORDER:
            sessions = sorted(day_sessions[day], key=lambda s: s["start"])
            if not sessions:
                continue
            lines.append(f"\n  {day.upper()}")
            lines.append("  " + "-" * 66)
            lines.append(
                f"  {'Time':<14} {'Room':<12} {'CRN':<10} {'Instructor':<22} {'Enroll/Cap'}"
            )
            lines.append("  " + "-" * 66)
            for s in sessions:
                time_str = f"{s['start']}-{s['end']}"
                enroll_cap = (
                    f"{s['enrollment']}/{s['capacity']}"
                    if s["enrollment"] > 0
                    else f"-/{s['capacity']}"
                )
                pref_flag = " ✓" if s.get("preference_match") else ""
                lines.append(
                    f"  {time_str:<14} {s['room']:<12} {s['crn']:<10} {s['instructor']:<22} {enroll_cap}{pref_flag}"
                )
        lines.append("\n" + "=" * 70)
        lines.append(
            f"  SUMMARY: {len(self.scheduled)} scheduled, {len(self.unscheduled)} unscheduled"
        )
        lines.append("=" * 70)
        if self.unscheduled:
            lines.append("\n  UNSCHEDULED LESSONS:")
            lines.append("  " + "-" * 66)
            for u in self.unscheduled:
                lines.append(
                    f"  CRN: {u['crn']} | Instructor: {u['instructor']} | Needed: {u['sessions_needed']} | Assigned: {u['sessions_assigned']}"
                )
                lines.append(f"    Reason: {u['reason']}")
        schedule_text = "\n".join(lines)
        return self.Outputs(schedule_json=schedule_json, schedule_text=schedule_text)
