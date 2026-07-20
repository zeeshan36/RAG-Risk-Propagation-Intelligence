"""Jinja2 prompt template loader."""
from pathlib import Path
from typing import Any, Dict

from jinja2 import Environment, FileSystemLoader, select_autoescape

_TEMPLATES_DIR = Path(__file__).parent / "templates"

_env = Environment(
    loader=FileSystemLoader(str(_TEMPLATES_DIR)),
    autoescape=select_autoescape(["html", "xml"]),
    trim_blocks=True,
    lstrip_blocks=True,
)


def render_template(name: str, **context: Any) -> str:
    """Render a Jinja2 template by name."""
    template = _env.get_template(name)
    return template.render(**context)


def render_impact_analysis(context: Dict[str, Any]) -> str:
    return render_template("impact_analysis.j2", **context)


def render_mitigation_plan(context: Dict[str, Any]) -> str:
    return render_template("mitigation_plan.j2", **context)


def render_vulnerability_review(context: Dict[str, Any]) -> str:
    return render_template("vulnerability_review.j2", **context)
