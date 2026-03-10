from uuid import UUID

from vellum_ee.workflows.display.base import (
    EdgeDisplay,
    EntrypointDisplay,
    WorkflowDisplayData,
    WorkflowDisplayDataViewport,
    WorkflowInputsDisplay,
    WorkflowMetaDisplay,
    WorkflowOutputDisplay,
)
from vellum_ee.workflows.display.editor import NodeDisplayData, NodeDisplayPosition
from vellum_ee.workflows.display.workflows import BaseWorkflowDisplay

from ..inputs import Inputs
from ..nodes.constraint_solver_node import ConstraintSolverNode
from ..nodes.format_output_node import FormatOutputNode
from ..workflow import Workflow


class WorkflowDisplay(BaseWorkflowDisplay[Workflow]):
    workflow_display = WorkflowMetaDisplay(
        entrypoint_node_id=UUID("63884a7b-c01c-4cbc-b8d4-abe0a8796f6b"),
        entrypoint_node_source_handle_id=UUID("eba8fd73-57ab-4d7b-8f75-b54dbe5fc8ba"),
        entrypoint_node_display=NodeDisplayData(
            position=NodeDisplayPosition(x=-30, y=0), z_index=2, width=306, height=88
        ),
        display_data=WorkflowDisplayData(
            viewport=WorkflowDisplayDataViewport(x=75.48802395209583, y=359.4850299401198, zoom=0.7829341317365269)
        ),
    )
    inputs_display = {
        Inputs.instructor_preferences: WorkflowInputsDisplay(
            id=UUID("e7550716-bf71-4e17-b6c9-4a88b65922e1"), name="instructor_preferences"
        ),
        Inputs.lessons: WorkflowInputsDisplay(id=UUID("aa78dc79-88ab-457f-acbc-eacaaecd7af0"), name="lessons"),
    }
    entrypoint_displays = {
        ConstraintSolverNode: EntrypointDisplay(
            id=UUID("63884a7b-c01c-4cbc-b8d4-abe0a8796f6b"),
            edge_display=EdgeDisplay(id=UUID("24c3428a-57d6-435f-a417-f1148890d3ee")),
        )
    }
    edge_displays = {
        (ConstraintSolverNode.Ports.default, FormatOutputNode): EdgeDisplay(
            id=UUID("e1290a81-0ec8-43a5-956b-fa0644343f9a"), z_index=1
        )
    }
    output_displays = {
        Workflow.Outputs.schedule_json: WorkflowOutputDisplay(
            id=UUID("3e2f0b89-21a4-415e-8004-e92785810068"), name="schedule_json"
        ),
        Workflow.Outputs.schedule_text: WorkflowOutputDisplay(
            id=UUID("a0738712-1a44-4469-bba7-479f7edde590"), name="schedule_text"
        ),
        Workflow.Outputs.unscheduled_lessons: WorkflowOutputDisplay(
            id=UUID("f07dea46-f0ca-4753-9bb4-18e17649e93e"), name="unscheduled_lessons"
        ),
    }
