from vellum.workflows import BaseWorkflow
from vellum.workflows.state import BaseState

from .inputs import Inputs
from .nodes.constraint_solver_node import ConstraintSolverNode
from .nodes.format_output_node import FormatOutputNode


class Workflow(BaseWorkflow[Inputs, BaseState]):
    graph = ConstraintSolverNode >> FormatOutputNode

    class Outputs(BaseWorkflow.Outputs):
        schedule_json = FormatOutputNode.Outputs.schedule_json
        schedule_text = FormatOutputNode.Outputs.schedule_text
        unscheduled_lessons = ConstraintSolverNode.Outputs.unscheduled
