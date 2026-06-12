"""أخطاء Pipeline الموحّدة."""


class PipelineError(Exception):
    """خطأ قابل للمعالجة في الواجهة وCLI."""

    def __init__(self, code: str, message: str):
        self.code = code
        super().__init__(message)


UNITS_MISSING = "UNITS_MISSING"
CATALOG_INVALID = "CATALOG_INVALID"
SCRAPE_FAILED = "SCRAPE_FAILED"
STATE_CORRUPT = "STATE_CORRUPT"
CATEGORY_EXISTS = "CATEGORY_EXISTS"
