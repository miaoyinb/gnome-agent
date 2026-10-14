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

"""Tests for the Gnome Agent agent's `_execute` logic.

Extend these as you implement your agent: every input-validation branch and
every distinct result shape deserves a test. Run with `uv run pytest`.
"""

from agent import GnomeAgentAgent


def _make_agent() -> GnomeAgentAgent:
    # agent_card.json is loaded lazily by run()/build_app(), not by the
    # constructor, so unit tests can instantiate the agent directly.
    return GnomeAgentAgent(agent_name="Gnome Agent Agent")

'''
# This input is no longer valid, need to fix
async def test_execute_returns_success_for_valid_input(context, event_queue):
    agent = _make_agent()

    result = await agent._execute({"input_data": "hello"}, context, event_queue)

    assert result["status"] == "success"
    assert result["input_received"] == "hello"
    # The progress update was emitted through the event queue.
    assert event_queue.enqueue_event.await_count >= 1
'''

async def test_execute_rejects_missing_input(context, event_queue):
    agent = _make_agent()

    result = await agent._execute({}, context, event_queue)

    assert result["status"] == "error"
    assert "input_data" in result["error"]

async def test_markdown_to_csv(context, event_queue):
    # Load the test document
    # Specify the path to your markdown file
    file_path = "tests/data/hollowmere_almanac.md"

    # Open the file and read its contents into a string
    with open(file_path, "r", encoding="utf-8") as file:
        markdown_string = file.read()

    agent = _make_agent()
    result = await agent.markdown_to_csv(context, event_queue)

    assert len(result) == 3

    
