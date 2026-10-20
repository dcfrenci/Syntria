def image_src(content: str | None) -> str | None:
    """'image:12' -> authenticated proxy URL; legacy data URIs pass through."""
    if content and content.startswith("image:") and content[6:].isdigit():
        return f"/preset-image/{content[6:]}"
    return content