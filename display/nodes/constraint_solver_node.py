from uuid import UUID

from vellum_ee.workflows.display.nodes import BaseNodeDisplay
from vellum_ee.workflows.display.nodes.types import NodeOutputDisplay, PortDisplayOverrides

from ...nodes.constraint_solver_node import ConstraintSolverNode


class ConstraintSolverNodeDisplay(BaseNodeDisplay[ConstraintSolverNode]):
    node_id = UUID("2eff45b3-4946-4fab-8602-c922dab77f49")
    attribute_ids_by_name = {
        "lessons": UUID("8f773b66-d5d9-4ee2-85af-1772703c1498"),
        "instructor_preferences": UUID("53bb36fb-e642-4bde-b370-247c08b74295"),
    }
    output_display = {
        ConstraintSolverNode.Outputs.scheduled: NodeOutputDisplay(
            id=UUID("017ba0b2-bd6b-4cd6-9c3a-a7a4474795bb"), name="scheduled"
        ),
        ConstraintSolverNode.Outputs.unscheduled: NodeOutputDisplay(
            id=UUID("84de1a2c-41ef-4e3c-809e-73dae5ad29d4"), name="unscheduled"
        ),
    }
    port_displays = {
        ConstraintSolverNode.Ports.default: PortDisplayOverrides(id=UUID("16a0afb7-672a-4f14-8f03-2e6887ed2a08"))
    }
