TMDB_IMAGE_BASE = "https://image.tmdb.org/t/p"


def get_poster_url(path, size="w500"):
    """Build a TMDb poster image URL."""

    if not isinstance(path, str) or not path.strip():
        return None

    return f"{TMDB_IMAGE_BASE}/{size}{path}"


def get_backdrop_url(path, size="w1280"):
    """Build a TMDb backdrop image URL."""

    if not isinstance(path, str) or not path.strip():
        return None

    return f"{TMDB_IMAGE_BASE}/{size}{path}"


def format_currency(value):
    """Format financial values as readable USD amounts."""

    if value is None:
        return "N/A"

    if value >= 1_000_000_000:
        return f"${value / 1_000_000_000:.2f}B"

    if value >= 1_000_000:
        return f"${value / 1_000_000:.1f}M"

    return f"${value:,.0f}"


def format_score(value):
    """Format composite ranking scores."""

    return f"{value:.3f}" if value is not None else "N/A"
