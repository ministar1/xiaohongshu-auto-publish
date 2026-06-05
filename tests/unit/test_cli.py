from __future__ import annotations

from typer.testing import CliRunner

from xiaohongshu_auto_publish.cli import app


def test_cli_init_and_config_check(tmp_path: object, monkeypatch: object) -> None:
    monkeypatch.chdir(tmp_path)
    runner = CliRunner()
    result = runner.invoke(app, ["init"])
    assert result.exit_code == 0
    result = runner.invoke(app, ["config-check"])
    assert "XHS_AGENT_LLM_API_KEY" in result.output
    assert "secret" not in result.output


def test_cli_topic_and_status(tmp_path: object, monkeypatch: object) -> None:
    monkeypatch.chdir(tmp_path)
    runner = CliRunner()
    runner.invoke(app, ["init"])
    result = runner.invoke(app, ["topic", "睡眠不足", "--slug", "sleep"])
    assert result.exit_code == 0
    task_id = next(line.split("：", 1)[1] for line in result.output.splitlines() if line.startswith("任务 ID"))
    status = runner.invoke(app, ["status", task_id])
    assert status.exit_code == 0
    assert "waiting_research_edit" in status.output


def test_cli_import_missing_file_returns_error(tmp_path: object, monkeypatch: object) -> None:
    monkeypatch.chdir(tmp_path)
    runner = CliRunner()
    runner.invoke(app, ["init"])
    result = runner.invoke(app, ["import", "missing.md"])
    assert result.exit_code != 0
    assert "文章文件不存在" in result.stderr
