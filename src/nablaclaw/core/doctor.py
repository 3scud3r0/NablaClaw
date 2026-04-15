from __future__ import annotations

import os
import socket
import sys
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class CheckResult:
    name: str
    ok: bool
    details: str


@dataclass
class DoctorReport:
    checks: list[CheckResult] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return all(item.ok for item in self.checks)

    def as_dict(self) -> dict[str, object]:
        return {
            "ok": self.ok,
            "checks": [item.__dict__ for item in self.checks],
        }


class Doctor:
    def run(self) -> DoctorReport:
        report = DoctorReport()
        report.checks.append(self._check_python())
        report.checks.append(self._check_home_writable())
        report.checks.append(self._check_network_dns())
        report.checks.append(self._check_screen_capture_lib())
        return report

    def _check_python(self) -> CheckResult:
        ok = sys.version_info >= (3, 11)
        return CheckResult("python_version", ok, f"{sys.version.split()[0]}")

    def _check_home_writable(self) -> CheckResult:
        home = Path.home()
        ok = os.access(home, os.W_OK)
        return CheckResult("home_writable", ok, str(home))

    def _check_network_dns(self) -> CheckResult:
        try:
            socket.gethostbyname("openrouter.ai")
            return CheckResult("dns_resolution", True, "openrouter.ai resolvido")
        except Exception as err:
            return CheckResult("dns_resolution", False, str(err))

    def _check_screen_capture_lib(self) -> CheckResult:
        try:
            import mss  # noqa: F401
            return CheckResult("screen_capture_lib", True, "mss instalado")
        except Exception:
            return CheckResult("screen_capture_lib", False, "instale: pip install mss")
