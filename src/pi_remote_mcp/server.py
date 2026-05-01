from __future__ import annotations

from fastmcp import FastMCP

from pi_remote_mcp.config import AppConfig
from pi_remote_mcp.security.policy import PolicyInput, resolve_policy
from pi_remote_mcp.tools.desktop_tools import (
    app,
    annotated_snapshot,
    click,
    focus_window,
    get_backend_info,
    get_clipboard,
    list_windows,
    lock_screen,
    minimize_all,
    move,
    notification,
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
from pi_remote_mcp.tools.memory_tools import memory_errors, memory_files, memory_health, memory_note_add, memory_recent, memory_schema_check, memory_search, memory_show
from pi_remote_mcp.tools.mower_tools import git_project_state, hardware_probe, journal_search, mower_runtime_snapshot, network_failover_status, service_health_report
from pi_remote_mcp.tools.registry_tools import reg_read, reg_write
from pi_remote_mcp.tools.session_tools import (
    detect_dialog,
    get_active_window,
    get_session_state,
    list_monitors,
    list_workspaces,
    probe_capabilities,
    reconnect_session,
    switch_workspace,
    watch_clipboard,
    watch_window,
    window_properties,
)
from pi_remote_mcp.tools.system_tools import (
    cancel_task,
    event_log,
    get_running_tasks,
    get_task_status,
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
from pi_remote_mcp.tools import ui_tools


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
        mcp.tool(name="ObserveScreen")(ui_tools.observe_screen_tool)
    if "AnnotatedSnapshot" in policy.enabled_tools:
        mcp.tool(name="AnnotatedSnapshot")(annotated_snapshot)
    if "OCR" in policy.enabled_tools:
        mcp.tool(name="OCR")(ui_tools.ocr)
    if "ScreenRecord" in policy.enabled_tools:
        mcp.tool(name="ScreenRecord")(ui_tools.screen_record)
    if "UIMap" in policy.enabled_tools:
        mcp.tool(name="UIMap")(ui_tools.ui_map)
    if "UIMapJson" in policy.enabled_tools:
        mcp.tool(name="UIMapJson")(ui_tools.ui_map_json)
    if "UIFind" in policy.enabled_tools:
        mcp.tool(name="UIFind")(ui_tools.ui_find)
    if "UIClick" in policy.enabled_tools:
        mcp.tool(name="UIClick")(ui_tools.ui_click)
    if "UIAct" in policy.enabled_tools:
        mcp.tool(name="UIAct")(ui_tools.ui_act)
    if "UISequence" in policy.enabled_tools:
        mcp.tool(name="UISequence")(ui_tools.ui_sequence)
    if "UIWatch" in policy.enabled_tools:
        mcp.tool(name="UIWatch")(ui_tools.ui_watch)
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
    if "GetActiveWindow" in policy.enabled_tools:
        mcp.tool(name="GetActiveWindow")(get_active_window)
    if "WindowProperties" in policy.enabled_tools:
        mcp.tool(name="WindowProperties")(window_properties)
    if "ListWorkspaces" in policy.enabled_tools:
        mcp.tool(name="ListWorkspaces")(list_workspaces)
    if "SwitchWorkspace" in policy.enabled_tools:
        mcp.tool(name="SwitchWorkspace")(switch_workspace)
    if "ListMonitors" in policy.enabled_tools:
        mcp.tool(name="ListMonitors")(list_monitors)
    if "GetBackendInfo" in policy.enabled_tools:
        mcp.tool(name="GetBackendInfo")(get_backend_info)
    if "ProbeCapabilities" in policy.enabled_tools:
        mcp.tool(name="ProbeCapabilities")(probe_capabilities)
    if "DetectDialog" in policy.enabled_tools:
        mcp.tool(name="DetectDialog")(detect_dialog)
    if "WatchClipboard" in policy.enabled_tools:
        mcp.tool(name="WatchClipboard")(watch_clipboard)
    if "WatchWindow" in policy.enabled_tools:
        mcp.tool(name="WatchWindow")(watch_window)
    if "GetSessionState" in policy.enabled_tools:
        mcp.tool(name="GetSessionState")(get_session_state)
    if "ReconnectSession" in policy.enabled_tools:
        mcp.tool(name="ReconnectSession")(reconnect_session)

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
    if "GetTaskStatus" in policy.enabled_tools:
        mcp.tool(name="GetTaskStatus")(get_task_status)
    if "GetRunningTasks" in policy.enabled_tools:
        mcp.tool(name="GetRunningTasks")(get_running_tasks)
    if "CancelTask" in policy.enabled_tools:
        mcp.tool(name="CancelTask")(cancel_task)
    if "EventLog" in policy.enabled_tools:
        mcp.tool(name="EventLog")(event_log)
    if "RegRead" in policy.enabled_tools:
        mcp.tool(name="RegRead")(reg_read)
    if "RegWrite" in policy.enabled_tools:
        mcp.tool(name="RegWrite")(reg_write)
    if "Ping" in policy.enabled_tools:
        mcp.tool(name="Ping")(ping)
    if "PortCheck" in policy.enabled_tools:
        mcp.tool(name="PortCheck")(port_check)
    if "NetConnections" in policy.enabled_tools:
        mcp.tool(name="NetConnections")(net_connections)
    if "Scrape" in policy.enabled_tools:
        mcp.tool(name="Scrape")(scrape)

    if "MemoryRecent" in policy.enabled_tools:
        mcp.tool(name="MemoryRecent")(memory_recent)
    if "MemorySearch" in policy.enabled_tools:
        mcp.tool(name="MemorySearch")(memory_search)
    if "MemoryShow" in policy.enabled_tools:
        mcp.tool(name="MemoryShow")(memory_show)
    if "MemoryFiles" in policy.enabled_tools:
        mcp.tool(name="MemoryFiles")(memory_files)
    if "MemoryErrors" in policy.enabled_tools:
        mcp.tool(name="MemoryErrors")(memory_errors)
    if "MemoryNoteAdd" in policy.enabled_tools:
        mcp.tool(name="MemoryNoteAdd")(memory_note_add)
    if "MemoryHealth" in policy.enabled_tools:
        mcp.tool(name="MemoryHealth")(memory_health)
    if "MemorySchemaCheck" in policy.enabled_tools:
        mcp.tool(name="MemorySchemaCheck")(memory_schema_check)

    if "ServiceHealthReport" in policy.enabled_tools:
        mcp.tool(name="ServiceHealthReport")(service_health_report)
    if "JournalSearch" in policy.enabled_tools:
        mcp.tool(name="JournalSearch")(journal_search)
    if "MowerRuntimeSnapshot" in policy.enabled_tools:
        mcp.tool(name="MowerRuntimeSnapshot")(mower_runtime_snapshot)
    if "HardwareProbe" in policy.enabled_tools:
        mcp.tool(name="HardwareProbe")(hardware_probe)
    if "NetworkFailoverStatus" in policy.enabled_tools:
        mcp.tool(name="NetworkFailoverStatus")(network_failover_status)
    if "GitProjectState" in policy.enabled_tools:
        mcp.tool(name="GitProjectState")(git_project_state)

    return mcp, policy.enabled_tools
