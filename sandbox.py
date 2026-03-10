from vellum.workflows.inputs import DatasetRow
from vellum.workflows.sandbox import WorkflowSandboxRunner

from .inputs import Inputs
from .workflow import Workflow

dataset = [
    DatasetRow(
        label="Basic Mix (5 lessons)",
        inputs=Inputs(
            instructor_preferences=[],
            lessons=[
                {
                    "crn": "CS101",
                    "enrollment": 28,
                    "instructor": "Dr. Smith",
                    "times_per_week": 3,
                },
                {
                    "crn": "MATH201",
                    "enrollment": 22,
                    "instructor": "Prof. Johnson",
                    "times_per_week": 2,
                },
                {
                    "crn": "ENG301",
                    "enrollment": 15,
                    "instructor": "Dr. Smith",
                    "times_per_week": 2,
                },
                {
                    "crn": "PHY101",
                    "enrollment": 38,
                    "instructor": "Dr. Lee",
                    "times_per_week": 3,
                },
                {
                    "crn": "CHEM101",
                    "enrollment": 20,
                    "instructor": "Prof. Patel",
                    "times_per_week": 1,
                },
            ],
        ),
    ),
    DatasetRow(
        label="Heavy Load (10 lessons)",
        inputs=Inputs(
            instructor_preferences=[],
            lessons=[
                {
                    "crn": "CS101",
                    "enrollment": 28,
                    "instructor": "Dr. Smith",
                    "times_per_week": 3,
                },
                {
                    "crn": "CS201",
                    "enrollment": 24,
                    "instructor": "Dr. Smith",
                    "times_per_week": 2,
                },
                {
                    "crn": "MATH101",
                    "enrollment": 30,
                    "instructor": "Prof. Johnson",
                    "times_per_week": 3,
                },
                {
                    "crn": "MATH201",
                    "enrollment": 22,
                    "instructor": "Prof. Johnson",
                    "times_per_week": 2,
                },
                {
                    "crn": "ENG101",
                    "enrollment": 18,
                    "instructor": "Dr. Williams",
                    "times_per_week": 2,
                },
                {
                    "crn": "ENG301",
                    "enrollment": 15,
                    "instructor": "Dr. Williams",
                    "times_per_week": 2,
                },
                {
                    "crn": "PHY101",
                    "enrollment": 38,
                    "instructor": "Dr. Lee",
                    "times_per_week": 3,
                },
                {
                    "crn": "PHY201",
                    "enrollment": 20,
                    "instructor": "Dr. Lee",
                    "times_per_week": 2,
                },
                {
                    "crn": "CHEM101",
                    "enrollment": 25,
                    "instructor": "Prof. Patel",
                    "times_per_week": 2,
                },
                {
                    "crn": "BIO101",
                    "enrollment": 33,
                    "instructor": "Dr. Garcia",
                    "times_per_week": 3,
                },
            ],
        ),
    ),
    DatasetRow(
        label="Overflow Test (forces unscheduled)",
        inputs=Inputs(
            instructor_preferences=[],
            lessons=[
                {
                    "crn": "A001",
                    "enrollment": 10,
                    "instructor": "Dr. Alpha",
                    "times_per_week": 5,
                },
                {
                    "crn": "A002",
                    "enrollment": 10,
                    "instructor": "Dr. Alpha",
                    "times_per_week": 5,
                },
                {
                    "crn": "A003",
                    "enrollment": 10,
                    "instructor": "Dr. Alpha",
                    "times_per_week": 5,
                },
                {
                    "crn": "A004",
                    "enrollment": 10,
                    "instructor": "Dr. Alpha",
                    "times_per_week": 5,
                },
                {
                    "crn": "A005",
                    "enrollment": 10,
                    "instructor": "Dr. Alpha",
                    "times_per_week": 5,
                },
                {
                    "crn": "B001",
                    "enrollment": 42,
                    "instructor": "Dr. Beta",
                    "times_per_week": 4,
                },
            ],
        ),
    ),
    DatasetRow(
        label="Instructor Preferences",
        inputs=Inputs(
            instructor_preferences=[
                {
                    "instructor": "Dr. Smith",
                    "preferred_days": [
                        "Monday",
                        "Wednesday",
                    ],
                    "preferred_times": [
                        "morning",
                    ],
                    "strict": False,
                },
                {
                    "instructor": "Prof. Johnson",
                    "preferred_days": [
                        "Tuesday",
                        "Thursday",
                    ],
                    "preferred_times": [
                        "afternoon",
                    ],
                    "strict": True,
                },
                {
                    "instructor": "Dr. Lee",
                    "preferred_days": [],
                    "preferred_times": [
                        "afternoon",
                    ],
                    "strict": False,
                },
            ],
            lessons=[
                {
                    "crn": "CS101",
                    "enrollment": 28,
                    "instructor": "Dr. Smith",
                    "times_per_week": 3,
                },
                {
                    "crn": "MATH201",
                    "enrollment": 22,
                    "instructor": "Prof. Johnson",
                    "times_per_week": 2,
                },
                {
                    "crn": "ENG301",
                    "enrollment": 15,
                    "instructor": "Dr. Lee",
                    "times_per_week": 2,
                },
                {
                    "crn": "PHY101",
                    "enrollment": 18,
                    "instructor": "Dr. Lee",
                    "times_per_week": 3,
                },
            ],
        ),
    ),
]

runner = WorkflowSandboxRunner(workflow=Workflow(), dataset=dataset)

if __name__ == "__main__":
    runner.run()
