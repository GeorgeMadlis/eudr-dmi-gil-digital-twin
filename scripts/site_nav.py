from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class NavItem:
    label: str
    href: str


def render_header_nav(*, rel_prefix: str, active_label: str | None = None) -> str:
    """Render the shared site header + nav with a relative prefix.

    rel_prefix is the path from the current page to docs/site/.
    """

    items = [
        NavItem("Home", "index.html"),
        NavItem("Articles", "articles/index.html"),
        NavItem("Dependencies", "dependencies/index.html"),
        NavItem("Regulation", "regulation/links.html"),
        NavItem("Sources", "regulation/sources.html"),
        NavItem("Spine", "regulation/policy_to_evidence_spine.html"),
        NavItem("Views", "views/index.html"),
        NavItem("DTE Instructions v1.1", "dte_instructions.html"),
        NavItem("Conversation Starters", "dte_instructions.html#conversation-starters"),
        NavItem("AOI Reports", "aoi_reports/index.html"),
        NavItem("DAO (Stakeholders)", "dao_stakeholders/index.html"),
        NavItem("DAO (Developers)", "dao_dev/index.html"),
    ]

    nav_links = []
    for item in items:
        href = f"{rel_prefix}{item.href}"
        if active_label and item.label == active_label:
            nav_links.append(f'<a href="{href}" class="active">{item.label}</a>')
        else:
            nav_links.append(f'<a href="{href}">{item.label}</a>')

    return (
        "<header>\n"
        "  <div class=\"wrap\">\n"
        "    <nav>\n      "
        + "\n      ".join(nav_links)
        + "\n    </nav>\n    \n  </div>\n</header>"
    )
