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
import pandas as pd

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
    result = agent.markdown_to_csv(markdown_string)

    print(result)

    # Check that the number of tables is correct
    assert len(result) == 3

    assert result[0][0] == "Table 1. Registered population of the three gnome villages of Hollowmere Valley, as counted at the midsummer census each year from 2010 to 2024."
    assert result[1][0] == "Table 2. Monthly rainfall and wild mushroom harvest in the Whispering Wood for the year 2023, with the average market price fetched at the Mossbury Saturday market."
    assert result[2][0] == "Table 3. Vital statistics of the dragons resident in the Hollowmere caves, taken from the Spring 2024 Draconic Register, including each dragon's age, wingspan, measured top speed, and declared favourite snack."


async def test_test1():
    agent = _make_agent()

    result = await agent.test1("Taeseung")
    assert result == "Hello, Taeseung!"

#async def test_get_table_from_deeplynx(context):
#    agent = _make_agent()
#
#    test_artifact_id = "2784d45d-5cc8-4fe5-8de2-2f4c107fafa3"
#
#    df = await agent.get_table_from_deeplynx_for_testing(
#        artifact_id=test_artifact_id,
#        context=context,
#        artifacts=None
#    )
#
#    assert isinstance(df, pd.DataFrame), "Result should be a pandas DataFrame"
#    assert len(df) > 0, "DataFrame should not be empty"
#    assert len(df.columns) > 0, "DataFrame should have at least one column"
#
#    print(f"\n✅ Successfully fetched table from DeepLynx!")
#    print(f"   Artifact ID: {test_artifact_id}")
#    print(f"   Shape: {df.shape[0]} rows × {df.shape[1]} columns")
#    print(f"   Columns: {df.columns.tolist()}")
#    print(f"\n   First 5 rows:")
#    print(df.head())
#    print(f"\n   Data types:")
#    print(df.dtypes)
    
