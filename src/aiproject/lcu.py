from __future__ import annotations

from dataclasses import dataclass
import base64
import json
import re
import ssl
import subprocess
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


@dataclass(frozen=True)
class LcuCredentials:
    port: str
    token: str


@dataclass(frozen=True)
class CurrentChampion:
    champion_id: int
    alias: str
    name: str
    source: str
    phase: str


def _league_client_command_lines() -> list[str]:
    commands = [
        [
            "powershell",
            "-NoProfile",
            "-Command",
            "Get-CimInstance Win32_Process -Filter \"name='LeagueClientUx.exe'\" | "
            "ForEach-Object { $_.CommandLine }",
        ],
        ["wmic", "process", "where", "name='LeagueClientUx.exe'", "get", "commandline"],
    ]
    for command in commands:
        try:
            creationflags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
            output = subprocess.check_output(
                command,
                stderr=subprocess.DEVNULL,
                timeout=5,
                creationflags=creationflags,
            )
        except Exception:
            continue
        text = output.decode("utf-8", errors="ignore").strip()
        lines = [line.strip() for line in text.splitlines() if "--app-port=" in line]
        if lines:
            return lines
    return []


def find_lcu_credentials() -> LcuCredentials | None:
    for command_line in _league_client_command_lines():
        port = re.search(r"--app-port=(\d+)", command_line)
        token = re.search(r"--remoting-auth-token=([^\s\"]+)", command_line)
        if port and token:
            return LcuCredentials(port=port.group(1), token=token.group(1))
    return None


def lcu_get(path: str, credentials: LcuCredentials | None = None) -> dict | list | str:
    credentials = credentials or find_lcu_credentials()
    if credentials is None:
        raise RuntimeError("未检测到 League Client。请先打开英雄联盟客户端。")

    auth = base64.b64encode(f"riot:{credentials.token}".encode("utf-8")).decode("ascii")
    request = Request(
        f"https://127.0.0.1:{credentials.port}{path}",
        headers={
            "Authorization": f"Basic {auth}",
            "Accept": "application/json",
        },
    )
    context = ssl._create_unverified_context()
    try:
        with urlopen(request, timeout=4, context=context) as response:
            raw = response.read().decode("utf-8", errors="replace")
    except HTTPError as exc:
        if exc.code == 404:
            raise RuntimeError("当前不在英雄选择阶段。") from exc
        raise RuntimeError(f"LCU 请求失败：HTTP {exc.code}") from exc
    except URLError as exc:
        raise RuntimeError(f"LCU 连接失败：{exc.reason}") from exc

    return json.loads(raw) if raw else {}


def get_gameflow_phase() -> str | None:
    credentials = find_lcu_credentials()
    if credentials is None:
        return None

    try:
        phase = lcu_get("/lol-gameflow/v1/gameflow-phase", credentials)
    except RuntimeError:
        return None
    return phase if isinstance(phase, str) else None


def _champion_lookup(credentials: LcuCredentials) -> dict[int, tuple[str, str]]:
    champions = lcu_get("/lol-game-data/assets/v1/champion-summary.json", credentials)
    lookup: dict[int, tuple[str, str]] = {}
    for champion in champions:
        champion_id = int(champion.get("id", 0) or 0)
        if champion_id <= 0:
            continue
        lookup[champion_id] = (
            str(champion.get("alias", "")).strip(),
            str(champion.get("name", "")).strip(),
        )
    return lookup


def get_current_champion() -> CurrentChampion | None:
    credentials = find_lcu_credentials()
    if credentials is None:
        return None

    try:
        session = lcu_get("/lol-champ-select/v1/session", credentials)
    except RuntimeError as exc:
        if "英雄选择阶段" in str(exc):
            return None
        raise
    if not isinstance(session, dict):
        return None

    cell_id = session.get("localPlayerCellId")
    local_player = None
    for player in session.get("myTeam", []):
        if player.get("cellId") == cell_id:
            local_player = player
            break

    if local_player is None:
        summoner = lcu_get("/lol-summoner/v1/current-summoner", credentials)
        summoner_id = summoner.get("summonerId") if isinstance(summoner, dict) else None
        for player in session.get("myTeam", []):
            if player.get("summonerId") == summoner_id:
                local_player = player
                break

    if local_player is None:
        return None

    champion_id = int(local_player.get("championId") or local_player.get("championPickIntent") or 0)
    source = "championId" if int(local_player.get("championId") or 0) > 0 else "championPickIntent"
    if champion_id <= 0:
        return None

    alias, name = _champion_lookup(credentials).get(champion_id, ("", ""))
    return CurrentChampion(
        champion_id=champion_id,
        alias=alias,
        name=name or alias,
        source=source,
        phase=str(session.get("timer", {}).get("phase", "")),
    )
