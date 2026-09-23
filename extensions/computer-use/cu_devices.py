#!/usr/bin/env python3
"""Physical device leases (C15) — identity, validation, lifecycle.

A second physical keyboard/pointer pair can be leased to a guest env.
Devices are identified by serial + topology + interface set — never
by a persisted eventN node or a bare VID/PID wildcard (both match
unrelated hardware). The human's pair is declared protected; a
composite receiver containing a protected member is refused wholesale.

This layer performs NO attach: usbipd/QEMU passthrough wiring happens
only after a human-approved plan, on qualified platforms. A support
failure leaves the virtual delivery intact and records the capability
as unqualified — it is never declared done.
"""


def enumerate_devices():
    """Platform device inventory. Requires a qualified backend
    (usbipd-win listing on Windows, sysfs/udev on Linux); without one
    the honest answer is an empty list — never fabricated hardware."""
    return []


def _identity_ok(dev):
    """Uniquely identifiable = serial AND topology present. VID/PID
    alone is a product class, not an identity."""
    return bool(dev.get("serial")) and bool(dev.get("topology"))


def _protected_ids(policy):
    return set((policy or {}).get("protected") or [])


def _protected_serials(policy):
    return set((policy or {}).get("protected_serials") or [])


def validate_lease(request, policy, inventory):
    """List of error strings; [] = lease may proceed to the human-
    confirmed attach plan (which is a separate approval)."""
    errors = []
    if not isinstance(request, dict):
        return ["lease_request_not_a_mapping"]
    dev_id = request.get("device_id")
    if not request.get("env_id"):
        errors.append("env_id_required")
    if dev_id in _protected_ids(policy):
        errors.append("protected_host_device")
    inv = {d.get("device_id"): d for d in (inventory or [])
           if isinstance(d, dict)}
    dev = inv.get(dev_id)
    if dev is None:
        errors.append("device_not_in_inventory")
        dev = {}
    if dev:
        if not _identity_ok(dev):
            errors.append("device_not_uniquely_identified")
        if dev.get("serial") in _protected_serials(policy):
            errors.append("protected_host_device")
        members = dev.get("members") or []
        serials = _protected_serials(policy)
        pids = _protected_ids(policy)
        if any(m in pids for m in members) or \
                any(str(m).endswith(str(s)) or str(s) in str(m)
                    for m in members for s in serials):
            errors.append("protected_member_in_composite")
    if request.get("confirmed_by_human") is not True:
        errors.append("human_confirmation_required")
    return errors


class Lease:
    """Single-consumer lease state machine:
    available -> reserved -> attached -> releasing -> available.
    Disconnect while attached -> lost (agent pauses). Replug requires
    re-identification against the recorded identity — never adopts
    whatever hardware appeared."""

    STATES = frozenset({"available", "reserved", "attached",
                        "releasing", "lost"})

    def __init__(self, device_id, env_id, identity=None):
        self.device_id = device_id
        self.env_id = env_id
        self.identity = identity or {}
        self.state = "reserved"

    def _require(self, state):
        if self.state != state:
            raise RuntimeError(
                f"lease_state:{self.state}:expected_{state}")

    def attach(self, leases=None):
        if self.state == "lost":
            raise RuntimeError(
                "reidentification_required:replug_is_not_identity")
        self._require("reserved")
        for other in leases or []:
            if other is not self and other.device_id == \
                    self.device_id and other.state == "attached":
                raise RuntimeError("leased_elsewhere")
        self.state = "attached"

    def disconnect(self):
        if self.state == "attached":
            self.state = "lost"

    def reidentify(self, device):
        """Replug observed: must match the recorded identity (serial +
        topology). Different hardware is rejected, not adopted."""
        if self.state != "lost":
            raise RuntimeError(f"lease_state:{self.state}")
        if self.identity:
            for k in ("serial", "topology"):
                if self.identity.get(k) and \
                        device.get(k) != self.identity[k]:
                    raise ValueError(f"identity_mismatch:{k}")
        elif device.get("serial") is None:
            raise ValueError("identity_mismatch:no_baseline")
        self.identity = {"serial": device.get("serial"),
                         "topology": device.get("topology")}
        self.state = "reserved"

    def release(self):
        self._require("attached")
        self.state = "releasing"
        self.state = "available"
