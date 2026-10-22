import os
from dataclasses import dataclass
from typing import Literal

SandboxProvider = Literal["cloud", "e2b", "modal", "daytona", "docker"]

@dataclass
class CuaConfig:
    """Configuration for Cua remote sandboxes and isolation."""
    # Where sandboxes run: NEVER on local host monitor
    provider: SandboxProvider = "cloud"
    default_image: str = "ghcr.io/trycua/linux:24.04-slim"
    
    # Hard invariant: NEVER allow windows to spawn on the user's physical desktop
    allow_host_gui: bool = False
    
    # Cloud authentication
    api_key: str = os.getenv("CUA_API_KEY", "")
    e2b_api_key: str = os.getenv("E2B_API_KEY", "")
    modal_token: str = os.getenv("MODAL_TOKEN", "")

    # Lease and persistence
    default_lease_minutes: int = 15
    db_path: str = ""

    @classmethod
    def load(cls) -> "CuaConfig":
        provider = os.getenv("CUA_PROVIDER", "cloud").lower()
        if provider not in ("cloud", "e2b", "modal", "daytona", "docker"):
            provider = "cloud"
        return cls(
            provider=provider,
            allow_host_gui=False
        )
