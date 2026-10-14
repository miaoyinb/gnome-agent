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

import re
import io
import pandas as pd

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

    async def _execute(
        self,
        params: dict[str, Any],
        context: RequestContext,
        event_queue: EventQueue,
    ) -> dict[str, Any]:
        """Process one request.

        Args:
            params: Parameters from the caller's JSON payload, plus ``skill_id``
                from the message metadata (the skill the orchestrator selected).
            context: The A2A request context.  Use ``context.context_id`` as a
                stable key for per-conversation state.
            event_queue: Pass to the ``send_*`` helpers to emit progress updates
                and artifacts.

        Returns:
            A plain ``dict``.  The base class wraps it as the final ``completed``
            task status automatically — do not enqueue that event yourself.
        """
        # ------------------------------------------------------------------
        # 1. Read inputs from params.  These keys must match the properties
        #    declared in agent_card.json's inputSchema.
        # ------------------------------------------------------------------
        input_data = params.get("input_data")

        if not input_data:
            return {"status": "error", "error": "input_data is required"}

        # ------------------------------------------------------------------
        # 2. Send optional progress updates so the UI stays responsive.
        #    The base class sends the initial "working" update automatically;
        #    call this only when you want intermediate messages.
        # ------------------------------------------------------------------
        await self.send_status_update(
            context=context,
            event_queue=event_queue,
            message="Processing your request…",
        )

        # ------------------------------------------------------------------
        # 3. Do your actual work here.  Replace this with real logic.
        # ------------------------------------------------------------------
        if input_data['skill_id'] == 'markdown_to_csv':
            markdown_text = await read_in_markdown(path_or_markdown=params.get('path_or_markdown'))
            dict_of_tables = markdown_to_csv(markdown_text=markdown_text)
            return await send_to_deeplynx(
                context=context,
                event_queue=event_queue,
                message="Reading in markdown to create csv",
                dict_of_csv=dict_of_tables,
            )
        if input_data["skill_id"] == "plot_table":
            return await plot_table(
                context=context, event_queue=event_queue, message="Plotting a table"
            )
        return {"status": "Error", "error": "unknown skill"}

        # ------------------------------------------------------------------
        # 4. Return a plain dict.  Keep keys consistent with the
        #    "output_format" you described in agent_card.json.
        # ------------------------------------------------------------------
        return result

    def read_in_markdown(self, path_or_markdown=None):
        """
        Read in the markdown file

        Args: 
            path_or_markdown (str) : string containing either the path to the markdown file or the markdown file itself

        Returns:
            markdown_text (str) : Return either the read in version of the path or the markdown file presented
        """
        if os.path.isfile(path_or_markdown):
            with open(path_or_markdown, "r") as f:
                return f.read()
        return path_or_markdown

    def markdown_to_csv(self, markdown_text):
        """
        Find every markdown table in the text and pair each with its nearest "Table N." caption.

        Args:
            markdown_text (str) : markdown text as a

        Returns:
            a list of deeplynx ids (str), one per table
        """
        lines = markdown_text.splitlines()
        # Find the instances where we start a markdown table
        separator_re = re.compile(r"^\|?\s*:?-+:?\s*(\|\s*:?-+:?\s*)*\|?$")

        # Find the instance where Table is mentioned as the first word
        caption_re = re.compile(r"^\s*(Table\s+\d+\.?.*)$", re.IGNORECASE)

        # 1. Locate contiguous blocks of lines that form tables
        table_blocks = []  # list of (start_idx, end_idx_exclusive)
        i = 0
        while i < len(lines):
            if lines[i].strip().startswith("|"):
                start = i
                while i < len(lines) and lines[i].strip().startswith("|"):
                    i += 1
                table_blocks.append((start, i))
            else:
                i += 1

        # 2. For each table block, find caption + parse into a DataFrame
        dict_of_tables = {}
        tab_num = 1
        for start, end in table_blocks:
            # Caption = nearest line above the table starting with "Table N."
            caption = ""
            for j in range(start - 1, -1, -1):
                line = lines[j].strip()
                if line.startswith("|"):
                    break  # hit another table before finding a caption
                match = caption_re.match(line)
                if match:
                    caption = match.group(1).strip()
                    break

            # Drop the markdown separator row (e.g. |---|---|), then strip leading/trailing pipes
            table_lines = [
                line.strip().strip("|")
                for line in lines[start:end]
                if not separator_re.match(line.strip())
            ]
            if not table_lines:
                continue

            table_text = "\n".join(table_lines)
            df = pd.read_table(
                io.StringIO(table_text), sep=r"\s*\|\s*", engine="python"
            )
            df.columns = [c.strip() for c in df.columns]
            dict_of_tables.update({"caption": caption, "dataframe": df})
        return dict_of_tables

    def send_to_deeplynx(self, context, event_queue, message, dict_of_tables):
        """
        Take the dictionary of captions and csvs and send this to DeepLynx
        Args:
            dict_of csv (dict): which takes the form
            {
                caption (str)                : string containing the table captions
                dataframe (pandas.DataFrame) : pandas data frame containing the table associated with the caption
            }
        Returns:
            results (list) : list of table_id's created in deeplynx for each caption-df pair
        """
        tab_num = 0
        results = []
        for caption, df in dict_of_tables.items():
            rows = df.values.tolist()

            # Create a DeepLynx artifact which contains the
            table_id = await self.send_json_artifact(
                context,
                event_queue,
                {"caption": caption, "columns": df.columns, "rows": rows},
                name=f"table {tab_num}",
                catalog_artifact=True,
            )
            results.append(table_id)
            tab_num += 1
        return results

    def plot_table(context, event_queue, message, text_path):
        """
        Get the artefact and plot it as another artefact.  This is a placeholder for your actual plotting logic.
        """
        path = await self.get_artifact_file_path(
            params["table_artifact_id"],
            context=context,
            artifacts=params.get("artifacts"),
        )

        table_id = await self.send_json_artifact(
            context, event_queue, payload, name="table", catalog_artifact=True
        )

        ref = await self.send_deeplynx_artifact(
            context=context,
            event_queue=event_queue,
            file_path=png,
            name="plot.png",
            description="…",
            storage_config=ConnectionConfig.from_env(),
            mime_type="image/png",
        )
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
