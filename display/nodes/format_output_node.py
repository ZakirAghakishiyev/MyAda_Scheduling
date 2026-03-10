from uuid import UUID

from vellum_ee.workflows.display.nodes import BaseNodeDisplay
from vellum_ee.workflows.display.nodes.types import NodeOutputDisplay, PortDisplayOverrides

from ...nodes.format_output_node import FormatOutputNode


class FormatOutputNodeDisplay(BaseNodeDisplay[FormatOutputNode]):
    node_id = UUID("7712226d-9e6e-4bd1-94df-624c03792a01")
    attribute_ids_by_name = {
        "scheduled": UUID("b5f4db85-adcb-4226-af85-4508a270c101"),
        "unscheduled": UUID("24f4f73b-b939-4857-be87-a4e0975d1c72"),
    }
    output_display = {
        FormatOutputNode.Outputs.schedule_json: NodeOutputDisplay(
            id=UUID("f84e4914-7248-477e-8a62-7d2b2abd5199"), name="schedule_json"
        ),
        FormatOutputNode.Outputs.schedule_text: NodeOutputDisplay(
            id=UUID("aec8edec-6611-469e-a53b-2b4905d963a6"), name="schedule_text"
        ),
    }
    port_displays = {
        FormatOutputNode.Ports.default: PortDisplayOverrides(id=UUID("d20e734e-879d-48fb-8e11-9cfe18512acc"))
    }
