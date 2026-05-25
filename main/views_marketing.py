import json
import requests
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required

FACEBOOK_PAGE_ID = "107868541732644"
INSTAGRAM_ACCOUNT_ID = "17841452161435255"
META_GRAPH_BASE = "https://graph.facebook.com/v19.0"


@login_required
def marketing_dashboard(request):
    return render(request, "main/marketing.html")


@login_required
def api_meta_insights(request):
    """Proxy endpoint: fetches Facebook + Instagram insights using user-supplied token."""
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)

    try:
        body = json.loads(request.body)
        token = body.get("token", "").strip()
    except (json.JSONDecodeError, AttributeError):
        return JsonResponse({"error": "Invalid JSON body"}, status=400)

    if not token:
        return JsonResponse({"error": "Access token is required"}, status=400)

    data = {}

    # Facebook Page Insights
    fb_metrics = "page_impressions,page_reach,page_engaged_users,page_fans,page_views_total"
    fb_insights_url = (
        f"{META_GRAPH_BASE}/{FACEBOOK_PAGE_ID}/insights"
        f"?metric={fb_metrics}&period=day&access_token={token}"
    )
    fb_posts_url = (
        f"{META_GRAPH_BASE}/{FACEBOOK_PAGE_ID}/posts"
        f"?fields=message,created_time,full_picture,likes.summary(true),comments.summary(true),shares"
        f"&limit=10&access_token={token}"
    )

    try:
        fb_insights_resp = requests.get(fb_insights_url, timeout=10)
        data["facebook_insights"] = fb_insights_resp.json()
    except requests.RequestException as e:
        data["facebook_insights"] = {"error": str(e)}

    try:
        fb_posts_resp = requests.get(fb_posts_url, timeout=10)
        data["facebook_posts"] = fb_posts_resp.json()
    except requests.RequestException as e:
        data["facebook_posts"] = {"error": str(e)}

    # Instagram Insights
    ig_metrics = "impressions,reach,profile_views,follower_count"
    ig_insights_url = (
        f"{META_GRAPH_BASE}/{INSTAGRAM_ACCOUNT_ID}/insights"
        f"?metric={ig_metrics}&period=day&access_token={token}"
    )
    ig_media_url = (
        f"{META_GRAPH_BASE}/{INSTAGRAM_ACCOUNT_ID}/media"
        f"?fields=id,caption,media_type,timestamp,like_count,comments_count,thumbnail_url,media_url"
        f"&limit=10&access_token={token}"
    )

    try:
        ig_insights_resp = requests.get(ig_insights_url, timeout=10)
        data["instagram_insights"] = ig_insights_resp.json()
    except requests.RequestException as e:
        data["instagram_insights"] = {"error": str(e)}

    try:
        ig_media_resp = requests.get(ig_media_url, timeout=10)
        data["instagram_media"] = ig_media_resp.json()
    except requests.RequestException as e:
        data["instagram_media"] = {"error": str(e)}

    return JsonResponse(data)


@login_required
def api_tiktok_insights(request):
    """Proxy endpoint: fetches TikTok Business insights using user-supplied token."""
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)

    try:
        body = json.loads(request.body)
        token = body.get("token", "").strip()
        business_id = body.get("business_id", "").strip()
    except (json.JSONDecodeError, AttributeError):
        return JsonResponse({"error": "Invalid JSON body"}, status=400)

    if not token or not business_id:
        return JsonResponse({"error": "TikTok access token and business_id are required"}, status=400)

    headers = {"Access-Token": token, "Content-Type": "application/json"}
    url = f"https://business-api.tiktok.com/open_api/v1.3/business/get/?business_id={business_id}"

    try:
        resp = requests.get(url, headers=headers, timeout=10)
        return JsonResponse(resp.json())
    except requests.RequestException as e:
        return JsonResponse({"error": str(e)}, status=502)
