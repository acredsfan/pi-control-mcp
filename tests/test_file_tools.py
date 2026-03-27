from __future__ import annotations

import base64

from pi_remote_mcp.tools.file_tools import file_download, file_search, file_upload


def test_file_search_and_binary_round_trip(tmp_path) -> None:
    sample = tmp_path / "sample.txt"
    sample.write_text("hello", encoding="utf-8")

    search = file_search("*.txt", str(tmp_path))
    assert any(match["path"].endswith("sample.txt") for match in search["matches"])

    upload_target = tmp_path / "blob.bin"
    payload = base64.b64encode(b"abc123").decode("ascii")
    upload = file_upload(str(upload_target), payload)
    assert upload["written"] == 6

    download = file_download(str(upload_target))
    assert base64.b64decode(download["data_base64"].encode("ascii")) == b"abc123"
