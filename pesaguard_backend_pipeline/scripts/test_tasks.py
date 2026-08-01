def write_marker(path: str, content: str = "ok"):
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(content)
