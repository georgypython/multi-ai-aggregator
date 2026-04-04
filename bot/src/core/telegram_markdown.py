import re

_MDV2_RESERVED = set("_[]()~`>#+-=|{}.!")


def _normalize_markdown_bold(text: str) -> str:
    # Convert common markdown bold to Telegram MarkdownV2 bold.
    return re.sub(r"\*\*(.+?)\*\*", r"*\1*", text)


def _escape_markdown_v2(text: str) -> str:
    result: list[str] = []
    for ch in text:
        if ch in _MDV2_RESERVED:
            result.append("\\")
        result.append(ch)
    return "".join(result)


def to_markdown_v2_safe(text: str) -> str:
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    out: list[str] = []

    in_code_block = False
    for raw_line in lines:
        stripped = raw_line.strip()

        if stripped.startswith("```"):
            in_code_block = not in_code_block
            out.append("```")
            continue

        if in_code_block:
            # In code blocks keep content as close to original as possible.
            out.append(raw_line.replace("`", "\\`").replace("\\", "\\\\"))
            continue

        heading_match = re.match(r"^#{1,6}\s+(.+)$", stripped)
        if heading_match:
            out.append(
                f"*{_escape_markdown_v2(_normalize_markdown_bold(heading_match.group(1)))}*"
            )
            continue

        bullet_match = re.match(r"^[-*]\s+(.+)$", stripped)
        if bullet_match:
            out.append(
                f"• {_escape_markdown_v2(_normalize_markdown_bold(bullet_match.group(1)))}"
            )
            continue

        numbered_match = re.match(r"^\d+\.\s+(.+)$", stripped)
        if numbered_match:
            out.append(
                f"• {_escape_markdown_v2(_normalize_markdown_bold(numbered_match.group(1)))}"
            )
            continue

        out.append(_escape_markdown_v2(_normalize_markdown_bold(raw_line)))

    if in_code_block:
        out.append("```")

    return "\n".join(out)


def split_markdown_v2_safe(text: str, *, limit: int = 3500) -> list[str]:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    if not normalized:
        return [""]

    chunks: list[str] = []
    current: list[str] = []

    def flush_current() -> None:
        if not current:
            return
        raw = "\n".join(current)
        chunks.append(to_markdown_v2_safe(raw))
        current.clear()

    for line in normalized.split("\n"):
        if not current:
            candidate_raw = line
        else:
            candidate_raw = "\n".join(current + [line])

        if len(to_markdown_v2_safe(candidate_raw)) <= limit:
            current.append(line)
            continue

        flush_current()

        # Very long line fallback: split by characters.
        part = ""
        for ch in line:
            next_part = part + ch
            if len(to_markdown_v2_safe(next_part)) > limit and part:
                chunks.append(to_markdown_v2_safe(part))
                part = ch
            else:
                part = next_part

        current.append(part)

    flush_current()
    return chunks
