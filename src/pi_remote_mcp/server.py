from __future__ import annotations

from fastmcp import FastMCP

from pi_remote_mcp.config import AppConfig
from pi_remote_mcp.security.policy import PolicyInput, resolve_policy
from pi_remote_mcp.tools.desktop_tools import click, observe_screen, snapshot, type_text
from pi_remote_mcp.tools.file_tools import file_list, file_read, file_write
from pi_remote_mcp.tools.system_tools import get_system_info, list_processes, shell


def create_server(config: AppConfig) -> tuple[FastMCP, set[str]]:
    mcp = FastMCP("Pi Control MCP")

    policy = resolve_policy(
        PolicyInput(
            enable_tier3=config.security.enable_tier3,
            disable_tier2=config.security.disable_tier2,
            explicit_tools=config.tools.enable,
            exclude_tools=config.tools.exclude,
        )
    )

    if "Snapshot" in policy.enabled_tools:
        mcp.tool(name="Snapshot")(snapshot)
    if "ObserveScreen" in policy.enabled_tools:
        mcp.tool(name="ObserveScreen")(observe_screen)
    if "Click" in policy.enabled_tools:
        mcp.tool(name="Click")(click)
    if "Type" in policy.enabled_tools:
        mcp.tool(name="Type")(type_text)

    if "FileList" in policy.enabled_tools:
        mcp.tool(name="FileList")(file_list)
    if "FileRead" in policy.enabled_tools:
        mcp.tool(name="FileRead")(file_read)
    if "FileWrite" in policy.enabled_tools:
        mcp.tool(name="FileWrite")(file_write)

    if "GetSystemInfo" in policy.enabled_tools:
        mcp.tool(name="GetSystemInfo")(get_system_info)
    if "ListProcesses" in policy.enabled_tools:
        mcp.tool(name="ListProcesses")(list_processes)
    if "Shell" in policy.enabled_tools:
        mcp.tool(name="Shell")(shell)

    return mcp, policy.enabled_tools
