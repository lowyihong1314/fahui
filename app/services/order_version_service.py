ACTIVE_ORDER_VERSION = "2025_YLP"


class OrderVersionService:
    @staticmethod
    def normalize(version) -> str | None:
        if version is None:
            return None

        text = str(version).strip()
        if not text:
            return None

        if text.isdigit():
            return f"{text}_YLP"

        return text

    @staticmethod
    def to_year(version) -> int | None:
        normalized = OrderVersionService.normalize(version)
        if not normalized:
            return None

        prefix = normalized.split("_", 1)[0]
        return int(prefix) if prefix.isdigit() else None
