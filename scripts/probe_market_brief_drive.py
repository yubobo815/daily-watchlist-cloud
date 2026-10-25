"""Read-only GitHub-to-Drive authorization probe. Never logs private content."""
from __future__ import annotations

import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

MAX_BYTES = 512 * 1024
FOLDER_MIME = "application/vnd.google-apps.folder"
FILE_ID = re.compile(r"^[A-Za-z0-9_-]{10,120}$")


class ProbeError(RuntimeError):
    pass


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ProbeError("Drive unexpectedly redirected a request; no credentials forwarded.")


class DriveReader:
    def __init__(self, token: str):
        if not token:
            raise ProbeError("The short-lived Google access token is missing.")
        self.token = token
        self.opener = urllib.request.build_opener(NoRedirect)

    def get(self, file_id: str, *, media: bool = False):
        if not FILE_ID.fullmatch(file_id):
            raise ProbeError("Invalid Drive file identifier.")
        params = {"alt": "media"} if media else {
            "fields": "id,mimeType,parents,size,capabilities(canEdit,canAddChildren)"
        }
        url = "https://www.googleapis.com/drive/v3/files/" + file_id + "?" + urllib.parse.urlencode(params)
        request = urllib.request.Request(url, headers={"Authorization": "Bearer " + self.token})
        try:
            with self.opener.open(request, timeout=25) as response:
                body = response.read(MAX_BYTES + 1)
        except urllib.error.HTTPError as exc:
            raise ProbeError(f"Drive read failed with HTTP {exc.code}; check API enablement and folder reader access.") from None
        except urllib.error.URLError:
            raise ProbeError("Drive network request failed; retry the authorization probe.") from None
        if not body or len(body) > MAX_BYTES:
            raise ProbeError("Drive returned empty or oversized content; nothing was published.")
        if media:
            return body
        try:
            return json.loads(body)
        except (UnicodeError, json.JSONDecodeError):
            raise ProbeError("Drive returned invalid metadata.") from None


def probe(reader, folder_id: str, source_ids: list[str]) -> dict:
    if not FILE_ID.fullmatch(folder_id) or len(source_ids) != 2 or len(set(source_ids)) != 2:
        raise ProbeError("A valid folder and two distinct published source files are required.")
    folder = reader.get(folder_id)
    capabilities = folder.get("capabilities", {})
    if folder.get("id") != folder_id or folder.get("mimeType") != FOLDER_MIME:
        raise ProbeError("The configured resource is not the expected Drive folder.")
    if capabilities.get("canEdit") is not False or capabilities.get("canAddChildren") is not False:
        raise ProbeError("Expected strictly read-only folder access; refusing broader permissions.")
    for file_id in source_ids:
        metadata = reader.get(file_id)
        if metadata.get("id") != file_id or folder_id not in metadata.get("parents", []):
            raise ProbeError("A published source is outside the authorized folder.")
        if metadata.get("capabilities", {}).get("canEdit") is not False:
            raise ProbeError("Expected a read-only source file.")
        if metadata.get("mimeType") not in {"text/markdown", "text/plain", "application/octet-stream"}:
            raise ProbeError("The published report is not a supported text file.")
        content = reader.get(file_id, media=True)
        if not isinstance(content, bytes) or not content.strip() or len(content) > MAX_BYTES:
            raise ProbeError("The source content could not be read safely.")
        # Content is deliberately neither printed nor persisted as a CI artifact.
    return {"status": "ok", "folder_read_only": True, "readable_source_files": 2, "private_content_logged": False}


def main() -> int:
    try:
        snapshot = json.loads((Path(__file__).resolve().parents[1] / "data/market-brief.json").read_text())
        source_ids = []
        for source in snapshot.get("sources", []):
            match = re.fullmatch(r"https://drive\.google\.com/file/d/([A-Za-z0-9_-]+)/view", source.get("url", ""))
            if match:
                source_ids.append(match.group(1))
        result = probe(DriveReader(os.environ.get("GOOGLE_DRIVE_ACCESS_TOKEN", "")), os.environ.get("MARKET_REPORTS_DRIVE_FOLDER_ID", ""), source_ids)
        print(json.dumps(result, sort_keys=True))
        return 0
    except (ProbeError, OSError, json.JSONDecodeError) as exc:
        print("Drive authorization probe failed: " + str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
