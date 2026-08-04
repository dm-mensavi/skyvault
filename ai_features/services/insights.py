import logging
from datetime import datetime, timedelta, timezone
from django.db.models import Sum
from vault.models import File
from ai_features.models import FileAnalysis, StorageInsight
from ai_features.services.claude import generate_text

logger = logging.getLogger(__name__)

INSIGHT_SYSTEM_PROMPT = (
    "You are SkyVault AI, a smart personal file vault assistant.\n"
    "Given a user's file storage statistics, write a concise, friendly, and actionable storage insight "
    "(2–3 sentences max). Include specific numbers. Mention the dominant file type, any storage "
    "optimisation opportunities (e.g. large files, untouched files, overflowing trash), and one concrete "
    "recommendation. Be specific and direct — this is a portfolio product."
)


def gather_storage_stats(user) -> dict:
    """
    Aggregates vault-level storage statistics for a user.
    Returns a structured dict suitable for Claude prompt injection and dashboard display.
    """
    files = File.objects.filter(user=user, trashed=False)
    trashed = File.objects.filter(user=user, trashed=True)

    total_files = files.count()
    total_bytes = files.aggregate(total=Sum("size"))["total"] or 0
    total_mb = round(total_bytes / (1024 * 1024), 2)

    # By file type
    by_type: dict[str, int] = {}
    for f in files.values("name"):
        ext = f["name"].rsplit(".", 1)[-1].lower() if "." in f["name"] else "unknown"
        by_type[ext] = by_type.get(ext, 0) + 1

    # By tag (from FileAnalysis)
    by_tag: dict[str, int] = {}
    for analysis in FileAnalysis.objects.filter(file__user=user, file__trashed=False, status="done"):
        for tag in analysis.tags:
            by_tag[tag] = by_tag.get(tag, 0) + 1

    # Files not touched in 6+ months
    six_months_ago = datetime.now(tz=timezone.utc) - timedelta(days=180)
    untouched_6mo = files.filter(created_at__lt=six_months_ago).count()

    # Top 5 largest files
    largest = [
        {"name": f.name, "mb": round(f.size / (1024 * 1024), 2)}
        for f in files.order_by("-size")[:5]
    ]

    return {
        "total_files": total_files,
        "total_mb": total_mb,
        "by_type": dict(sorted(by_type.items(), key=lambda x: x[1], reverse=True)),
        "by_tag": dict(sorted(by_tag.items(), key=lambda x: x[1], reverse=True)[:10]),
        "untouched_6mo": untouched_6mo,
        "largest_files": largest,
        "trashed_count": trashed.count(),
    }


def generate_storage_insight(user, force_refresh: bool = False) -> dict:
    """
    Fetches or regenerates the Claude-generated storage insight for the user.
    Caches result in StorageInsight model. Refreshes if force_refresh=True or no cached insight.
    """
    # Check cached insight (valid for 24 hours unless force_refresh)
    cached = StorageInsight.objects.filter(user=user).first()
    if cached and not force_refresh:
        age_hours = (datetime.now(tz=timezone.utc) - cached.generated_at).total_seconds() / 3600
        if age_hours < 24:
            return {
                "insight": cached.insight,
                "generated_at": cached.generated_at.strftime("%Y-%m-%d %H:%M"),
                "stats": cached.stats_snapshot,
                "from_cache": True,
            }

    stats = gather_storage_stats(user)

    if stats["total_files"] == 0:
        insight_text = (
            "Your SkyVault is empty — upload your first document to unlock AI-powered "
            "summaries, smart tags, and semantic search!"
        )
    else:
        # Build compact stats prompt
        top_types = ", ".join(f"{k}: {v}" for k, v in list(stats["by_type"].items())[:5])
        top_tags = ", ".join(f"{k}: {v}" for k, v in list(stats["by_tag"].items())[:5]) or "none yet"
        largest = ", ".join(f"{f['name']} ({f['mb']} MB)" for f in stats["largest_files"][:3]) or "none"

        user_prompt = (
            f"Storage stats for this SkyVault user:\n"
            f"- Total files: {stats['total_files']} ({stats['total_mb']} MB used)\n"
            f"- File types: {top_types}\n"
            f"- AI-detected tags: {top_tags}\n"
            f"- Files untouched 6+ months: {stats['untouched_6mo']}\n"
            f"- Largest files: {largest}\n"
            f"- Items in trash: {stats['trashed_count']}\n"
            "\nWrite a 2–3 sentence storage insight with one concrete action recommendation."
        )

        try:
            insight_text = generate_text(INSIGHT_SYSTEM_PROMPT, user_prompt, max_tokens=200).strip()
            if not insight_text:
                insight_text = (
                    f"Your vault contains {stats['total_files']} files ({stats['total_mb']} MB). "
                    "Configure an AI API key to unlock natural-language AI insights."
                )
        except Exception as e:
            logger.error(f"Error generating storage insight for user {user.id}: {e}", exc_info=True)
            insight_text = (
                f"Your vault holds {stats['total_files']} files ({stats['total_mb']} MB). "
                "AI insight generation is temporarily unavailable."
            )

    # Upsert cached insight
    StorageInsight.objects.update_or_create(
        user=user,
        defaults={"insight": insight_text, "stats_snapshot": stats},
    )

    return {
        "insight": insight_text,
        "generated_at": datetime.now(tz=timezone.utc).strftime("%Y-%m-%d %H:%M"),
        "stats": stats,
        "from_cache": False,
    }
