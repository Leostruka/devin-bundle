"""C15 — second physical pair: inventory, identity, lease lifecycle.

Devices are identified by serial/topology/interface — never by
persisted eventN or bare VID/PID wildcard. Pair A (human) is declared
protected; leasing it, or a composite receiver containing it, is
refused. Lease is a state machine with a single consumer; disconnect
pauses, replug requires re-identification — never adopts other
hardware. No attach is performed by this layer.
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cu_load import load  # noqa: E402

cu_devices = load("cu_devices")


KBD_A = {"device_id": "usb-1.2.1-kbd", "vid": "046d", "pid": "c31c",
         "serial": "A1234", "topology": "1.2.1",
         "interfaces": ["kbd"], "kind": "keyboard"}
KBD_B = {"device_id": "usb-1.4.1-kbd", "vid": "046d", "pid": "c31c",
         "serial": "B5678", "topology": "1.4.1",
         "interfaces": ["kbd"], "kind": "keyboard"}
COMPOSITE = {"device_id": "usb-1.3-receiver",
             "vid": "046d", "pid": "c52b", "serial": "RCVR9",
             "topology": "1.3",
             "members": ["usb-1.3.1-kbd-A1234", "usb-1.3.2-mouse-B"],
             "interfaces": ["kbd", "mouse"], "kind": "receiver"}

POLICY = {"protected": ["usb-1.2.1-kbd"],
          "protected_serials": ["A1234"]}
INVENTORY = [KBD_A, KBD_B, COMPOSITE]


def _req(**over):
    r = {"device_id": "usb-1.4.1-kbd", "env_id": "devin-linux",
         "confirmed_by_human": True}
    r.update(over)
    return r


def test_protected_device_cannot_be_leased():
    errors = cu_devices.validate_lease(
        _req(device_id="usb-1.2.1-kbd"), POLICY, INVENTORY)
    assert "protected_host_device" in errors


def test_protected_device_refused_even_off_inventory():
    """Spec case: protection binds to the declared id regardless of
    inventory presence."""
    errors = cu_devices.validate_lease(
        {"device_id": "human-keyboard", "env_id": "vm-a",
         "confirmed_by_human": True},
        {"protected": ["human-keyboard"]}, [])
    assert "protected_host_device" in errors


def test_protected_by_serial():
    """Same protected device reached by serial — protection is on
    identity, not the id string."""
    errors = cu_devices.validate_lease(
        _req(device_id="usb-1.2.1-kbd"),
        {"protected": [], "protected_serials": ["A1234"]}, INVENTORY)
    assert "protected_host_device" in errors


def test_composite_receiver_with_protected_member_refused():
    pol = {"protected": [], "protected_serials": ["A1234"]}
    errors = cu_devices.validate_lease(
        _req(device_id="usb-1.3-receiver"), pol, INVENTORY)
    assert "protected_member_in_composite" in errors


def test_unknown_device_rejected():
    errors = cu_devices.validate_lease(
        _req(device_id="usb-9.9.9"), POLICY, INVENTORY)
    assert "device_not_in_inventory" in errors


def test_no_identifiers_rejected():
    dev = {"device_id": "x", "vid": "1", "pid": "2",
           "serial": None, "topology": None}
    errors = cu_devices.validate_lease(
        _req(device_id="x"), POLICY, [dev])
    assert "device_not_uniquely_identified" in errors


def test_wildcard_vidpid_not_an_identity():
    """VID/PID alone can match many devices — not a lease identity."""
    dev = dict(KBD_B)
    dev["serial"] = None
    dev["topology"] = None
    errors = cu_devices.validate_lease(
        _req(device_id="usb-1.4.1-kbd"), POLICY, [dev])
    assert "device_not_uniquely_identified" in errors


def test_unconfirmed_by_human_rejected():
    errors = cu_devices.validate_lease(
        _req(confirmed_by_human=False), POLICY, INVENTORY)
    assert "human_confirmation_required" in errors


def test_valid_lease_request_ok():
    assert cu_devices.validate_lease(_req(), POLICY, INVENTORY) == []


# --- lease state machine ---------------------------------------------------

def test_lease_lifecycle_single_consumer():
    lease = cu_devices.Lease("usb-1.4.1-kbd", "devin-linux")
    assert lease.state == "reserved"
    lease.attach()
    assert lease.state == "attached"
    lease.release()
    assert lease.state == "available"


def test_disconnect_pauses_to_lost_not_available():
    lease = cu_devices.Lease("usb-1.4.1-kbd", "devin-linux")
    lease.attach()
    lease.disconnect()
    assert lease.state == "lost"      # agent paused; not free hardware


def test_replug_requires_reidentification():
    lease = cu_devices.Lease("usb-1.4.1-kbd", "devin-linux",
                             identity={"serial": "B5678",
                                       "topology": "1.4.1"})
    lease.attach()
    lease.disconnect()
    with pytest.raises(RuntimeError, match="reidentification"):
        lease.attach()                # no blind re-adopt
    lease.reidentify(KBD_B)           # same identity observed again
    lease.attach()
    assert lease.state == "attached"


def test_reidentify_rejects_different_hardware():
    lease = cu_devices.Lease("usb-1.4.1-kbd", "devin-linux",
                             identity={"serial": "B5678",
                                       "topology": "1.4.1"})
    lease.attach()
    lease.disconnect()
    with pytest.raises(ValueError):
        lease.reidentify(KBD_A)       # different serial — not ours


def test_single_consumer():
    lease = cu_devices.Lease("usb-1.4.1-kbd", "devin-linux")
    other = cu_devices.Lease("usb-1.4.1-kbd", "other-env")
    lease.attach()
    with pytest.raises(RuntimeError, match="leased_elsewhere"):
        other.attach(leases=[lease])
