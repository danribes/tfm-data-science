import os
from typing import Optional

TEMPLATES = {
    "retiree": (
        "By {year}, your pension's real purchasing power is projected at {real_index:.1f} "
        "(base=100 today), and health funding sits at {adequacy} of its current level."
    ),
    "mortgage_banker": (
        "By {year}, the projected mortgage rate is {rate:.2f}%, monthly payment "
        "{payment:.0f}, default-risk proxy {risk:.2f}."
    ),
}


def render_template_narrative(persona: str, **kwargs) -> str:
    template = TEMPLATES.get(persona)
    if template is None:
        return "No narrative template available for this persona."
    return template.format(**kwargs)


def llm_available() -> bool:
    return bool(os.environ.get("ANTHROPIC_API_KEY"))


def render_llm_narrative(persona: str, scenario_summary: str) -> Optional[str]:
    if not llm_available():
        return None
    import anthropic
    client = anthropic.Anthropic()
    message = client.messages.create(
        model="claude-sonnet-5",
        max_tokens=300,
        messages=[{
            "role": "user",
            "content": (
                f"Write a short (3-4 sentence), plain-English narrative for a {persona} persona "
                f"reading a sovereign fiscal scenario dashboard. Never issue advice or a "
                f"buy/sell/vote recommendation -- describe conditional projections only. "
                f"Scenario summary:\n{scenario_summary}"
            ),
        }],
    )
    return message.content[0].text


def render_narrative(persona: str, scenario_summary: str, **template_kwargs) -> str:
    if llm_available():
        llm_text = render_llm_narrative(persona, scenario_summary)
        if llm_text:
            return llm_text
    return render_template_narrative(persona, **template_kwargs)
