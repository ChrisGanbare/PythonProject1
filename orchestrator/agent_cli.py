"""CLI for Agent workflow: catalog / compile / validate / run-from-json."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def _registry():
    sys.path.insert(0, str(REPO_ROOT))
    sys.path.insert(0, str(REPO_ROOT / "projects"))
    from orchestrator.registry import ProjectRegistry

    r = ProjectRegistry(REPO_ROOT)
    r.discover()
    return r


def cmd_catalog(_args: argparse.Namespace) -> int:
    from shared.agent import build_agent_catalog

    cat = build_agent_catalog(_registry())
    print(json.dumps(cat, ensure_ascii=False, indent=2))
    return 0


def cmd_schema(_args: argparse.Namespace) -> int:
    from shared.agent.schemas import StandardVideoJobRequest

    print(json.dumps(StandardVideoJobRequest.model_json_schema(), ensure_ascii=False, indent=2))
    return 0


def cmd_compile(args: argparse.Namespace) -> int:
    from shared.agent import compile_natural_language
    from shared.agent.schemas import StandardVideoJobRequest

    prev = None
    if args.previous:
        text = Path(args.previous).read_text(encoding="utf-8")
        prev = StandardVideoJobRequest.model_validate_json(text)

    result = compile_natural_language(" ".join(args.prompt), _registry(), previous=prev)
    out = result.model_dump()
    print(json.dumps(out, ensure_ascii=False, indent=2))
    if args.output and result.success and result.standard_request:
        Path(args.output).write_text(
            result.standard_request.model_dump_json(indent=2),
            encoding="utf-8",
        )
    return 0 if result.success else 1


def cmd_validate(args: argparse.Namespace) -> int:
    from shared.agent import validate_standard_request
    from shared.agent.schemas import StandardVideoJobRequest

    text = Path(args.file).read_text(encoding="utf-8")
    req = StandardVideoJobRequest.model_validate_json(text)
    v = validate_standard_request(req, _registry())
    print(json.dumps(v.model_dump(), ensure_ascii=False, indent=2))
    return 0 if v.valid else 1


def cmd_run(args: argparse.Namespace) -> int:
    from orchestrator.runner import run_project_task
    from shared.agent.schemas import StandardVideoJobRequest

    text = Path(args.file).read_text(encoding="utf-8")
    req = StandardVideoJobRequest.model_validate_json(text)
    registry = _registry()
    from shared.agent import validate_standard_request

    v = validate_standard_request(req, registry)
    if not v.valid:
        print(json.dumps({"errors": v.errors}, ensure_ascii=False), file=sys.stderr)
        return 1
    project = registry.get_project(req.project)
    assert project is not None
    print(f"Running {req.project}:{req.task} ...", file=sys.stderr)
    run_project_task(project, req.task, req.kwargs)
    print("Done.", file=sys.stderr)
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Agent 工作流：目录 / 编译 / 校验 / 执行标准模板")
    sub = p.add_subparsers(dest="command", required=True)

    sub.add_parser("catalog", help="输出当前子项目与任务目录 JSON")

    sub.add_parser("schema", help="输出 StandardVideoJobRequest 的 JSON Schema")

    c = sub.add_parser("compile", help="自然语言编译为标准模板（需配置 OpenAI 兼容 API）")
    c.add_argument("prompt", nargs="+", help="需求描述（可多个词，请不用引号也可：video-agent compile 做 一个 抖音 视频）")
    c.add_argument("--previous", help="上一版标准模板 JSON 文件路径（迭代修改）")
    c.add_argument("-o", "--output", help="成功时将 standard_request 写入该文件")

    v = sub.add_parser("validate", help="校验标准模板 JSON 文件")
    v.add_argument("file", help="StandardVideoJobRequest JSON 路径")

    r = sub.add_parser("run", help="同步执行标准模板（前台渲染，等同 scheduler run）")
    r.add_argument("file", help="StandardVideoJobRequest JSON 路径")

    return p


def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "catalog":
        return cmd_catalog(args)
    if args.command == "schema":
        return cmd_schema(args)
    if args.command == "compile":
        return cmd_compile(args)
    if args.command == "validate":
        return cmd_validate(args)
    if args.command == "run":
        return cmd_run(args)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
