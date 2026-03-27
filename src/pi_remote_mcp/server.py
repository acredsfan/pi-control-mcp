from __future__ import annotations

from fastmcp import FastMCP

from pi_remote_mcp.config import AppConfig
from pi_remote_mcp.security.policy import PolicyInput, resolve_policy
from pi_remote_mcp.tools.desktop_tools import (
    app,
    click,
    focus_window,
    get_backend_info,
    get_clipboard,
    list_windows,
    lock_screen,
    minimize_all,
    move,
    notification,
    observe_screen,
    scroll,
    set_clipboard,
    shortcut,
    snapshot,
    type_text,
    wait,
)
from pi_remote_mcp.tools.file_tools import (
    file_download,
    file_list,
    file_read,
    file_search,
    file_upload,
    file_write,
)
from pi_remote_mcp.tools.network_tools import net_connections, ping, port_check, scrape
from pi_remote_mcp.tools.system_tools import (
    event_log,
    get_system_info,
    kill_process,
    list_processes,
    service_list,
    service_start,
    service_stop,
    shell,
    task_create,
    task_delete,
    task_list,
)


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
    if "Scroll" in policy.enabled_tools:
        mcp.tool(name="Scroll")(scroll)
    if "Move" in policy.enabled_tools:
        mcp.tool(name="Move")(move)
    if "Shortcut" in policy.enabled_tools:
        mcp.tool(name="Shortcut")(shortcut)
    if "Wait" in policy.enabled_tools:
        mcp.tool(name="Wait")(wait)
    if "FocusWindow" in policy.enabled_tools:
        mcp.tool(name="FocusWindow")(focus_window)
    if "MinimizeAll" in policy.enabled_tools:
        mcp.tool(name="MinimizeAll")(minimize_all)
    if "App" in policy.enabled_tools:
        mcp.tool(name="App")(app)
    if "GetClipboard" in policy.enabled_tools:
        mcp.tool(name="GetClipboard")(get_clipboard)
    if "SetClipboard" in policy.enabled_tools:
        mcp.tool(name="SetClipboard")(set_clipboard)
    if "Notification" in policy.enabled_tools:
        mcp.tool(name="Notification")(notification)
    if "LockScreen" in policy.enabled_tools:
        mcp.tool(name="LockScreen")(lock_screen)
    if "ListWindows" in policy.enabled_tools:
        mcp.tool(name="ListWindows")(list_windows)
    if "GetBackendInfo" in policy.enabled_tools:
        mcp.tool(name="GetBackendInfo")(get_backend_info)

    if "FileList" in policy.enabled_tools:
        mcp.tool(name="FileList")(file_list)
    if "FileRead" in policy.enabled_tools:
        mcp.tool(name="FileRead")(file_read)
    if "FileWrite" in policy.enabled_tools:
        mcp.tool(name="FileWrite")(file_write)
    if "FileSearch" in policy.enabled_tools:
        mcp.tool(name="FileSearch")(file_search)
    if "FileDownload" in policy.enabled_tools:
        mcp.tool(name="FileDownload")(file_download)
    if "FileUpload" in policy.enabled_tools:
        mcp.tool(name="FileUpload")(file_upload)

    if "GetSystemInfo" in policy.enabled_tools:
        mcp.tool(name="GetSystemInfo")(get_system_info)
    if "ListProcesses" in policy.enabled_tools:
        mcp.tool(name="ListProcesses")(list_processes)
    if "Shell" in policy.enabled_tools:
        mcp.tool(name="Shell")(shell)
    if "KillProcess" in policy.enabled_tools:
        mcp.tool(name="KillProcess")(kill_process)
    if "ServiceList" in policy.enabled_tools:
        mcp.tool(name="ServiceList")(service_list)
    if "ServiceStart" in policy.enabled_tools:
        mcp.tool(name="ServiceStart")(service_start)
    if "ServiceStop" in policy.enabled_tools:
        mcp.tool(name="ServiceStop")(service_stop)
    if "TaskList" in policy.enabled_tools:
        mcp.tool(name="TaskList")(task_list)
    if "TaskCreate" in policy.enabled_tools:
        mcp.tool(name="TaskCreate")(task_create)
    if "TaskDelete" in policy.enabled_tools:
        mcp.tool(name="TaskDelete")(task_delete)
    if "EventLog" in policy.enabled_tools:
        mcp.tool(name="EventLog")(event_log)
    if "Ping" in policy.enabled_tools:
        mcp.tool(name="Ping")(ping)
    if "PortCheck" in policy.enabled_tools:
        mcp.tool(name="PortCheck")(port_check)
    if "NetConnections" in policy.enabled_tools:
        mcp.tool(name="NetConnections")(net_connections)
    if "Scrape" in policy.enabled_tools:
        mcp.tool(name="Scrape")(scrape)

    return mcp, policy.enabled_tools
