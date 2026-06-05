from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from xiaohongshu_auto_publish.app import build_account_service, build_orchestrator
from xiaohongshu_auto_publish.config.loader import check_required_secrets, init_project, load_config
from xiaohongshu_auto_publish.errors import XHSError
from xiaohongshu_auto_publish.input.normalizer import ArticleInputRequest, TopicInputRequest
from xiaohongshu_auto_publish.interaction.cli_adapter import format_result
from xiaohongshu_auto_publish.maintenance.archive import archive_task
from xiaohongshu_auto_publish.maintenance.cleanup import cleanup_workspace
from xiaohongshu_auto_publish.models import WritingStyle
from xiaohongshu_auto_publish.state.store import StateStore

app = typer.Typer(no_args_is_help=True)
accounts_app = typer.Typer(no_args_is_help=True)
app.add_typer(accounts_app, name="accounts")

ConfigOption = Annotated[Path, typer.Option("--config", help="配置文件路径")]
SetOption = Annotated[list[str] | None, typer.Option("--set", help="覆盖配置：section.field=value")]


def main() -> None:
    app()


def _config(config: Path, set_values: list[str] | None) -> object:
    return load_config(config, set_values)


def _style(value: str) -> WritingStyle:
    try:
        return WritingStyle(value)
    except ValueError as exc:
        raise typer.BadParameter("style 必须是 popular、professional 或 balanced") from exc


def _handle_error(exc: XHSError) -> None:
    typer.echo(f"错误：{exc.summary}", err=True)
    if exc.detail:
        typer.echo(f"原因：{exc.detail}", err=True)
    if exc.next_action:
        typer.echo(f"建议：{exc.next_action}", err=True)
    if exc.related_artifacts:
        typer.echo("相关文件：", err=True)
        for path in exc.related_artifacts:
            typer.echo(f"- {path}", err=True)
    raise typer.Exit(1)


@app.command()
def init(
    config: ConfigOption = Path("config.toml"),
    set_values: SetOption = None,
    overwrite: Annotated[bool, typer.Option("--overwrite")] = False,
) -> None:
    del config, set_values
    created = init_project(Path.cwd(), overwrite=overwrite)
    for path in created:
        typer.echo(path)


@app.command()
def topic(
    topic_text: str,
    config: ConfigOption = Path("config.toml"),
    set_values: SetOption = None,
    account: Annotated[str, typer.Option("--account")] = "default",
    style: Annotated[str, typer.Option("--style")] = "popular",
    audience: Annotated[str | None, typer.Option("--audience")] = None,
    series: Annotated[bool, typer.Option("--series")] = False,
    length: Annotated[str, typer.Option("--length")] = "medium",
    slug: Annotated[str | None, typer.Option("--slug")] = None,
) -> None:
    try:
        cfg = load_config(config, set_values)
        orchestrator = build_orchestrator(cfg)
        result = orchestrator.create_from_topic(
            TopicInputRequest(
                topic=topic_text,
                account_id=account,
                style=_style(style),
                audience=audience,
                length=length,
                series=series,
                slug=slug,
            )
        )
    except XHSError as exc:
        _handle_error(exc)
    typer.echo(format_result(result))


@app.command(name="import")
def import_article(
    article_path: Path,
    config: ConfigOption = Path("config.toml"),
    set_values: SetOption = None,
    topic: Annotated[str | None, typer.Option("--topic")] = None,
    account: Annotated[str, typer.Option("--account")] = "default",
    style: Annotated[str, typer.Option("--style")] = "popular",
    slug: Annotated[str | None, typer.Option("--slug")] = None,
) -> None:
    try:
        cfg = load_config(config, set_values)
        result = build_orchestrator(cfg).create_from_article(
            ArticleInputRequest(
                article_path=article_path,
                topic=topic,
                account_id=account,
                style=_style(style),
                slug=slug,
            )
        )
    except XHSError as exc:
        _handle_error(exc)
    typer.echo(format_result(result))


@app.command(name="continue")
def continue_command(
    task_id: str,
    config: ConfigOption = Path("config.toml"),
    set_values: SetOption = None,
    yes: Annotated[bool, typer.Option("--yes")] = False,
    force_parse: Annotated[bool, typer.Option("--force-parse")] = False,
    prompt_policy: Annotated[str, typer.Option("--prompt-policy")] = "locked",
    manual_review_note: Annotated[str | None, typer.Option("--manual-review-note")] = None,
) -> None:
    try:
        cfg = load_config(config, set_values)
        result = build_orchestrator(cfg).continue_task(
            task_id,
            yes=yes,
            force_parse=force_parse,
            prompt_policy=prompt_policy,
            manual_review_note=manual_review_note,
        )
    except XHSError as exc:
        _handle_error(exc)
    typer.echo(format_result(result))


@app.command()
def retry(
    task_id: str,
    config: ConfigOption = Path("config.toml"),
    set_values: SetOption = None,
    prompt_policy: Annotated[str, typer.Option("--prompt-policy")] = "locked",
) -> None:
    try:
        cfg = load_config(config, set_values)
        result = build_orchestrator(cfg).retry_task(task_id, prompt_policy)
    except XHSError as exc:
        _handle_error(exc)
    typer.echo(format_result(result))


@app.command()
def status(task_id: str, config: ConfigOption = Path("config.toml"), set_values: SetOption = None) -> None:
    try:
        cfg = load_config(config, set_values)
        result = build_orchestrator(cfg).get_status(task_id)
    except XHSError as exc:
        _handle_error(exc)
    typer.echo(format_result(result))


@app.command(name="list")
def list_tasks(config: ConfigOption = Path("config.toml"), set_values: SetOption = None) -> None:
    try:
        cfg = load_config(config, set_values)
        tasks = build_orchestrator(cfg).list_tasks()
    except XHSError as exc:
        _handle_error(exc)
    for task in tasks:
        typer.echo(f"{task.task_id}\t{task.status.value}\t{task.topic}")


@app.command("review-content")
def review_content(task_id: str, config: ConfigOption = Path("config.toml"), set_values: SetOption = None) -> None:
    try:
        cfg = load_config(config, set_values)
        result = build_orchestrator(cfg).review_content(task_id)
    except XHSError as exc:
        _handle_error(exc)
    typer.echo(format_result(result))


@app.command("review-writing")
def review_writing(task_id: str, config: ConfigOption = Path("config.toml"), set_values: SetOption = None) -> None:
    try:
        cfg = load_config(config, set_values)
        result = build_orchestrator(cfg).review_writing(task_id)
    except XHSError as exc:
        _handle_error(exc)
    typer.echo(format_result(result))


@app.command("review-format")
def review_format(task_id: str, config: ConfigOption = Path("config.toml"), set_values: SetOption = None) -> None:
    try:
        cfg = load_config(config, set_values)
        result = build_orchestrator(cfg).review_format(task_id)
    except XHSError as exc:
        _handle_error(exc)
    typer.echo(format_result(result))


@app.command("package")
def package_command(
    task_id: str,
    config: ConfigOption = Path("config.toml"),
    set_values: SetOption = None,
    yes: Annotated[bool, typer.Option("--yes")] = False,
) -> None:
    try:
        cfg = load_config(config, set_values)
        result = build_orchestrator(cfg).build_package(task_id, user_confirmed=yes)
    except XHSError as exc:
        _handle_error(exc)
    typer.echo(format_result(result))


@app.command()
def rollback(
    task_id: str,
    to_phase: Annotated[str, typer.Option("--to-phase")],
    config: ConfigOption = Path("config.toml"),
    set_values: SetOption = None,
) -> None:
    try:
        cfg = load_config(config, set_values)
        result = build_orchestrator(cfg).rollback_task(task_id, to_phase)
    except XHSError as exc:
        _handle_error(exc)
    typer.echo(format_result(result))


@app.command()
def publish(
    task_id: str,
    config: ConfigOption = Path("config.toml"),
    set_values: SetOption = None,
    confirmed: Annotated[bool, typer.Option("--confirmed")] = False,
) -> None:
    try:
        cfg = load_config(config, set_values)
        result = build_orchestrator(cfg).publish(task_id, confirmed=confirmed)
    except XHSError as exc:
        _handle_error(exc)
    typer.echo(format_result(result))


@app.command()
def cleanup(
    config: ConfigOption = Path("config.toml"),
    set_values: SetOption = None,
    dry_run: Annotated[bool, typer.Option("--dry-run")] = False,
    apply: Annotated[bool, typer.Option("--apply")] = False,
) -> None:
    try:
        cfg = load_config(config, set_values)
        candidates = cleanup_workspace(cfg, apply=apply and not dry_run)
    except XHSError as exc:
        _handle_error(exc)
    for item in candidates:
        typer.echo(f"{item.path}\t{item.reason}\t{item.bytes_to_free}")


@app.command()
def archive(task_id: str, config: ConfigOption = Path("config.toml"), set_values: SetOption = None) -> None:
    try:
        cfg = load_config(config, set_values)
        target = archive_task(cfg, StateStore(cfg), task_id)
    except XHSError as exc:
        _handle_error(exc)
    typer.echo(target)


@accounts_app.command("list")
def accounts_list(config: ConfigOption = Path("config.toml"), set_values: SetOption = None) -> None:
    try:
        cfg = load_config(config, set_values)
        summaries = build_account_service(cfg).list_profiles()
    except XHSError as exc:
        _handle_error(exc)
    for profile in summaries:
        marker = "default" if profile.is_default else ""
        typer.echo(f"{profile.account_id}\t{marker}\t{profile.path}")


@accounts_app.command("show")
def accounts_show(
    account_id: str,
    config: ConfigOption = Path("config.toml"),
    set_values: SetOption = None,
) -> None:
    try:
        cfg = load_config(config, set_values)
        profile = build_account_service(cfg).show_profile(account_id)
    except XHSError as exc:
        _handle_error(exc)
    typer.echo(f"账号：{profile.account_id}")
    typer.echo(f"定位：{profile.positioning}")
    typer.echo(f"受众：{profile.audience}")
    typer.echo(f"语气：{profile.tone}")
    typer.echo(f"配置文件：{profile.path}")


@app.command("config-check")
def config_check(config: ConfigOption = Path("config.toml"), set_values: SetOption = None) -> None:
    try:
        cfg = load_config(config, set_values)
        missing = check_required_secrets(cfg)
    except XHSError as exc:
        _handle_error(exc)
    if not missing:
        typer.echo("配置检查通过")
        return
    typer.echo("缺少环境变量：")
    for name in missing:
        typer.echo(f"- {name}")
