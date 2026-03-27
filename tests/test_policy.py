from pi_remote_mcp.security.policy import PolicyInput, resolve_policy


def test_default_policy_enables_tier1_and_tier2_only() -> None:
    resolved = resolve_policy(
        PolicyInput(enable_tier3=False, disable_tier2=False, explicit_tools=[], exclude_tools=[])
    )
    assert 1 in resolved.enabled_tiers
    assert 2 in resolved.enabled_tiers
    assert 3 not in resolved.enabled_tiers
    assert "Shell" not in resolved.enabled_tools


def test_enable_tier3_adds_shell() -> None:
    resolved = resolve_policy(
        PolicyInput(enable_tier3=True, disable_tier2=False, explicit_tools=[], exclude_tools=[])
    )
    assert "Shell" in resolved.enabled_tools
    assert 3 in resolved.enabled_tiers


def test_explicit_tools_override_tiers() -> None:
    resolved = resolve_policy(
        PolicyInput(
            enable_tier3=False,
            disable_tier2=True,
            explicit_tools=["Snapshot", "Shell"],
            exclude_tools=[],
        )
    )
    assert resolved.enabled_tools == {"Snapshot", "Shell"}


def test_policy_includes_new_clipboard_and_network_tools_by_default() -> None:
    resolved = resolve_policy(
        PolicyInput(enable_tier3=False, disable_tier2=False, explicit_tools=[], exclude_tools=[])
    )
    assert "GetClipboard" in resolved.enabled_tools
    assert "Ping" in resolved.enabled_tools
    assert "SetClipboard" not in resolved.enabled_tools
