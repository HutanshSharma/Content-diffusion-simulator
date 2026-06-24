from datetime import datetime, timezone

def _safe_div(a: float, b: float) -> float:
    return a / b if b else 0.0


def _clamp(value: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, value))


def _score_youtube(data: dict) -> dict:
    subscribers   = data.get("subscribers", 0)
    total_views   = data.get("total_views", 0)
    video_count   = data.get("video_count", 1)
    recent_videos = data.get("recent_videos", [])

    avg_views_per_video = _safe_div(total_views, video_count)

    # Engagement rate: (likes + comments) / views per video
    engagement_rates = []
    for v in recent_videos:
        views = v.get("views", 0)
        if views > 0:
            rate = _safe_div(v.get("likes", 0) + v.get("comments", 0), views)
            engagement_rates.append(rate)

    avg_engagement = (sum(engagement_rates) / len(engagement_rates)) if engagement_rates else 0

    # Posting frequency: posts per month from recent videos
    posting_freq = _calc_posting_frequency(
        [v.get("published_at", "") for v in recent_videos]
    )

    # Views consistency (low variance = more stable = higher quality)
    view_counts = [v.get("views", 0) for v in recent_videos]
    consistency = _calc_consistency(view_counts)

    return {
        "subscribers":          subscribers,
        "avg_views_per_video":  avg_views_per_video,
        "avg_engagement_rate":  round(avg_engagement, 4),
        "posting_freq_monthly": round(posting_freq, 2),
        "view_consistency":     round(consistency, 4),
    }


def _score_instagram(data: dict) -> dict:
    followers    = data.get("followers", 0)
    following    = data.get("following", 1)
    recent_posts = data.get("recent_posts", [])
    monthly_reach = data.get("monthly_reach", 0)

    engagement_rate_per_post = []
    for p in recent_posts:
        likes    = p.get("like_count", 0)
        comments = p.get("comments_count", 0)
        if followers > 0:
            rate = _safe_div(likes + comments, followers)
            engagement_rate_per_post.append(rate)

    avg_engagement = (sum(engagement_rate_per_post) / len(engagement_rate_per_post)) if engagement_rate_per_post else 0

    posting_freq = _calc_posting_frequency(
        [p.get("timestamp", "") for p in recent_posts]
    )

    follower_following_ratio = _safe_div(followers, following)

    return {
        "followers":              followers,
        "monthly_reach":          monthly_reach,
        "avg_engagement_rate":    round(avg_engagement, 4),
        "posting_freq_monthly":   round(posting_freq, 2),
        "follower_following_ratio": round(follower_following_ratio, 2),
    }


def _calc_posting_frequency(timestamps: list[str]) -> float:
    """Returns estimated posts per month from a list of ISO timestamps (to find span days)."""
    dates = []
    for ts in timestamps:
        if not ts:
            continue
        try:
            dates.append(datetime.fromisoformat(ts.replace("Z", "+00:00")))
        except ValueError:
            continue

    if len(dates) < 2:
        return 0.0

    dates.sort()
    span_days = (dates[-1] - dates[0]).days or 1
    return _safe_div(len(dates), span_days) * 30


def _calc_consistency(values: list[float]) -> float:
    """Returns 0-1 consistency score. Higher = more consistent performance."""
    if len(values) < 2:
        return 1.0
    mean = sum(values) / len(values)
    if mean == 0:
        return 0.0
    variance = sum((v - mean) ** 2 for v in values) / len(values)
    cv = (variance ** 0.5) / mean  # coefficient of variation ( standard variation / mean )
    return _clamp(1 - cv, 0.0, 1.0)


def compute_scores(youtube_data: dict | None, instagram_data: dict | None) -> dict:
    yt = _score_youtube(youtube_data) if youtube_data else {}
    ig = _score_instagram(instagram_data) if instagram_data else {}

    # ── 1. Creator Trust Score ────────────────────────────────────────
    # Based on audience size + engagement quality
    yt_trust = 0.0
    ig_trust = 0.0

    if yt:
        sub_score   = _clamp(_safe_div(yt["subscribers"], 1_000_000) * 50, 0, 50)
        eng_score   = _clamp(yt["avg_engagement_rate"] * 1000, 0, 50)
        yt_trust    = sub_score + eng_score

    if ig:
        follower_score = _clamp(_safe_div(ig["followers"], 500_000) * 50, 0, 50)
        eng_score      = _clamp(ig["avg_engagement_rate"] * 500, 0, 50)
        ig_trust       = follower_score + eng_score

    trust_score = _clamp(
        (yt_trust + ig_trust) / (2 if yt and ig else 1)
    )

    # ── 2. Creator Momentum Score ─────────────────────────────────────
    # Based on posting frequency + recent engagement trend
    momentum = 0.0

    if yt:
        freq_score = _clamp(yt["posting_freq_monthly"] * 5, 0, 50)
        cons_score = yt["view_consistency"] * 50
        momentum  += freq_score + cons_score

    if ig:
        freq_score = _clamp(ig["posting_freq_monthly"] * 3, 0, 50)
        momentum  += freq_score

    momentum = _clamp(momentum / (2 if yt and ig else 1))

    # ── 3. Niche Authority Score ──────────────────────────────────────
    # Proxy: views-per-subscriber ratio on YouTube + reach-to-followers on IG
    niche = 0.0

    if yt and yt["subscribers"] > 0:
        vps   = _safe_div(yt["avg_views_per_video"], yt["subscribers"])
        niche += _clamp(vps * 100, 0, 100)

    if ig and ig["followers"] > 0:
        rtr   = _safe_div(ig["monthly_reach"], ig["followers"])
        niche += _clamp(rtr * 50, 0, 100)

    niche = _clamp(niche / (2 if yt and ig else 1))

    # ── 4. Audience Quality Score ─────────────────────────────────────
    # High followers but low engagement = ghost followers
    quality = 0.0

    if yt:
        quality += _clamp(yt["avg_engagement_rate"] * 2000, 0, 100)

    if ig:
        ratio_score = _clamp(ig["follower_following_ratio"] * 10, 0, 50)
        eng_score   = _clamp(ig["avg_engagement_rate"] * 1000, 0, 50)
        quality    += ratio_score + eng_score

    quality = _clamp(quality / (2 if yt and ig else 1))

    # ── 5. Creator Volatility Score ───────────────────────────────────
    # Low volatility = consistent. High = unpredictable.
    # Inverted consistency score.
    volatility = 0.0

    if yt:
        volatility += _clamp((1 - yt["view_consistency"]) * 100, 0, 100)

    volatility = _clamp(volatility)

    # ── Momentum label ────────────────────────────────────────────────
    if momentum >= 70:
        momentum_label = "High"
    elif momentum >= 40:
        momentum_label = "Medium"
    else:
        momentum_label = "Low"

    return {
        "creator_trust_score":     round(trust_score, 1),
        "creator_momentum_score":  round(momentum, 1),
        "creator_momentum_label":  momentum_label,
        "niche_authority_score":   round(niche, 1),
        "audience_quality_score":  round(quality, 1),
        "creator_volatility_score": round(volatility, 1),
        "raw": {
            "youtube":   yt,
            "instagram": ig,
        },
    }