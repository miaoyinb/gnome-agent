# This file is part of Prometheus
# https://inl.gov/super-intelligence/prometheus/
#
# Copyright 2026 Battelle Energy Alliance, LLC
# All rights reserved, see NOTICE.txt for full restrictions
# https://github.com/idaholab/prometheus_core/blob/main/NOTICE.txt
#
# Licensed under the MIT License, please see LICENSE for details
# https://github.com/idaholab/prometheus_core/blob/main/LICENSE
#
# SPDX-License-Identifier: MIT

"""
Gnome Agent Agent.

Fix this later

This is a Prometheus specialist agent.  Subclass PrometheusAgent and implement
`_execute` — the base class handles the HTTP server, authentication, agent-card
serving, and registry registration for you.
"""

import logging
from typing import Any

from prometheus_api import load_prompt  # noqa: F401 - used by the LLM pattern below
from prometheus_api.agent import EventQueue, PrometheusAgent, RequestContext

# Read secrets and configuration from environment variables.
# Never hard-code API keys or URLs here.
# Example (add `import os` to the imports above):
#   MY_API_KEY = os.getenv("MY_API_KEY")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class GnomeAgentAgent(PrometheusAgent):
    """Gnome Agent Agent."""

    # Optional: register agent-owned HTTP endpoints in __init__.
    #
    # def __init__(self, *args: Any, **kwargs: Any) -> None:
    #     super().__init__(*args, **kwargs)
    #     self.add_http_endpoint(
    #         "/api/preview/{artifact_id}",
    #         self.preview_artifact,
    #         methods=["GET"],
    #         endpoint_id="artifact_preview",
    #         purpose="artifact",
    #         description="Return preview metadata for one artifact.",
    #         content_types=["application/json"],
    #     )
    #     self.add_static_endpoint(
    #         "/viewer",
    #         "viewer-assets",
    #         endpoint_id="viewer_assets",
    #         purpose="viewer_plugin",
    #         description="Serve viewer plugin JavaScript and CSS.",
    #         content_types=["text/javascript", "text/css"],
    #     )
    #
    # async def preview_artifact(self, request):
    #     from starlette.responses import JSONResponse
    #
    #     return JSONResponse({"artifact_id": request.path_params["artifact_id"]})

    async def _execute(self, params, context, event_queue):
        if params["skill_id"] == "plot_table":
            return await self.plot(params, context, event_queue)
        return {"status": "error", "error": "unknown skill"}

    def plot(params, context, event_queue):
        path = await self.get_artifact_file_path(params["table_artifact_id"], context=context,artifacts=params.get("artifacts"))

        table_id = await self.send_json_artifact(context, event_queue, payload, name="table",catalog_artifact=True)

        ref = await self.send_deeplynx_artifact(
            context=context, event_queue=event_queue,
            file_path=png, name="plot.png", description="…",
            storage_config=ConnectionConfig.from_env(),
            mime_type="image/png")
        return {"status": "success", "artifact_id": ref.artifact_id}

    # ----------------------------------------------------------------------
    # PATTERNS — uncomment and adapt as needed.
    # ----------------------------------------------------------------------
    #
    # Calling an LLM through the platform's LiteLLM gateway:
    #
    #     system_prompt = load_prompt("system_prompt.txt").format(input_data=input_data)
    #     async with self.llm_client(context) as llm:
    #         response = await llm.medium(system_prompt)
    #     return {"status": "success", "summary": response.text}
    #
    # Dispatching when agent_card.json declares more than one skill:
    #
    #     handler = {
    #         "skill_a": self._handle_a,
    #         "skill_b": self._handle_b,
    #     }.get(params.get("skill_id"))
    #     if handler is None:
    #         return {"status": "error", "error": f"Unknown skill: {params.get('skill_id')}"}
    #     return await handler(params, context, event_queue)
    #
    # Persisting per-conversation state across turns (Redis-backed, with an
    # in-memory fallback for local development):
    #
    #     state = self.load_context_state(str(context.context_id))
    #     state["count"] = state.get("count", 0) + 1
    #     self.save_context_state(str(context.context_id), state)
    #
    # See TUTORIAL.md ("Advanced topics") for emitting artifacts, asking the
    # user for missing inputs (INPUT_REQUIRED), and DeepLynx file storage.


if __name__ == "__main__":
    agent = GnomeAgentAgent(agent_name="Gnome Agent Agent")
    agent.run()
