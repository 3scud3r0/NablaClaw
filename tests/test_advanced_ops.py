from nablaclaw.channels import ChannelHub, DeliveryResult, InMemoryChannelAdapter
from nablaclaw.core import PermissionPolicy


def test_permission_inheritance() -> None:
    policy = PermissionPolicy()
    policy.grant("base", "skill:*")
    policy.grant_role("child", "base")
    assert policy.allowed("child", "skill:read_file")


def test_channel_hub_broadcast_returns_delivery_results() -> None:
    hub = ChannelHub()
    hub.register(InMemoryChannelAdapter("telegram"))
    hub.register(InMemoryChannelAdapter("discord"))
    results = hub.broadcast(user_id="u1", text="ping")
    assert len(results) == 2
    assert all(isinstance(item, DeliveryResult) for item in results)
    assert all(item.ok for item in results)
