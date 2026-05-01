from __future__ import annotations

from dataclasses import dataclass


TIER_1_TOOLS = {
    "Snapshot",
    "ObserveScreen",
    "AnnotatedSnapshot",
    "UIMap",
    "UIMapJson",
    "UIFind",
    "UIWatch",
    "OCR",
    "ScreenRecord",
    "GetClipboard",
    "GetSystemInfo",
    "ListProcesses",
    "FileList",
    "FileSearch",
    "RegRead",
    "ServiceList",
    "TaskList",
    "EventLog",
    "Notification",
    "Ping",
    "PortCheck",
    "NetConnections",
    "Wait",
    "ListWindows",
    "GetActiveWindow",
    "WindowProperties",
    "ListWorkspaces",
    "ListMonitors",
    "GetBackendInfo",
    "ProbeCapabilities",
    "DetectDialog",
    "WatchClipboard",
    "WatchWindow",
    "GetSessionState",
    "GetTaskStatus",
    "GetRunningTasks",
    "MemoryRecent",
    "MemorySearch",
    "MemoryShow",
    "MemoryFiles",
    "MemoryErrors",
    "MemoryHealth",
    "MemorySchemaCheck",
    "ServiceHealthReport",
    "JournalSearch",
    "MowerRuntimeSnapshot",
    "HardwareProbe",
    "NetworkFailoverStatus",
    "GitProjectState",
}

TIER_2_TOOLS = {
    "Click",
    "Type",
    "Move",
    "Scroll",
    "Shortcut",
    "FocusWindow",
    "MinimizeAll",
    "App",
    "UIClick",
    "UIAct",
    "UISequence",
    "Scrape",
    "SwitchWorkspace",
    "ReconnectSession",
    "CancelTask",
    "MemoryNoteAdd",
}

TIER_3_TOOLS = {
    "Shell",
    "FileRead",
    "FileWrite",
    "FileUpload",
    "FileDownload",
    "KillProcess",
    "ServiceStart",
    "ServiceStop",
    "TaskCreate",
    "TaskDelete",
    "SetClipboard",
    "LockScreen",
    "RegWrite",
}

ALL_KNOWN_TOOLS = TIER_1_TOOLS | TIER_2_TOOLS | TIER_3_TOOLS


@dataclass(slots=True)
class PolicyInput:
    enable_tier3: bool
    disable_tier2: bool
    explicit_tools: list[str]
    exclude_tools: list[str]


@dataclass(slots=True)
class ResolvedPolicy:
    enabled_tools: set[str]
    enabled_tiers: tuple[int, ...]


def resolve_policy(policy: PolicyInput) -> ResolvedPolicy:
    if policy.explicit_tools:
        selected = set(policy.explicit_tools)
    else:
        selected = set(TIER_1_TOOLS)
        if not policy.disable_tier2:
            selected |= TIER_2_TOOLS
        if policy.enable_tier3:
            selected |= TIER_3_TOOLS

    selected -= set(policy.exclude_tools)
    selected &= ALL_KNOWN_TOOLS

    tiers = [1]
    if selected & TIER_2_TOOLS:
        tiers.append(2)
    if selected & TIER_3_TOOLS:
        tiers.append(3)

    return ResolvedPolicy(enabled_tools=selected, enabled_tiers=tuple(tiers))
