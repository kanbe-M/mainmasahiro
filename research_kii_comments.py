"""
「心の話 -きい-」チャンネルのコメントリサーチ
"""
import requests
import csv
import time
import json
import sys
from datetime import datetime

# ローカルPC実行用（pip install requests が必要）
# 実行方法: python3 research_kii_comments.py

API_KEY = "YOUR_API_KEY_HERE"  # ← ここにAPIキーを入れてください
BASE_URL = "https://www.googleapis.com/youtube/v3"

def search_channel(query):
    """チャンネルを検索してIDを取得"""
    url = f"{BASE_URL}/search"
    params = {
        "key": API_KEY,
        "q": query,
        "type": "channel",
        "part": "snippet",
        "maxResults": 5,
    }
    r = requests.get(url, params=params)
    r.raise_for_status()
    items = r.json().get("items", [])
    for item in items:
        print(f"  チャンネル名: {item['snippet']['channelTitle']}")
        print(f"  チャンネルID: {item['snippet']['channelId']}")
        print()
    return items

def get_videos(channel_id, max_videos=50):
    """チャンネルの動画一覧を取得"""
    videos = []
    url = f"{BASE_URL}/search"
    params = {
        "key": API_KEY,
        "channelId": channel_id,
        "type": "video",
        "part": "snippet",
        "maxResults": 50,
        "order": "viewCount",  # 再生数順
    }

    while len(videos) < max_videos:
        r = requests.get(url, params=params)
        r.raise_for_status()
        data = r.json()

        for item in data.get("items", []):
            videos.append({
                "video_id": item["id"]["videoId"],
                "title": item["snippet"]["title"],
                "published_at": item["snippet"]["publishedAt"],
            })

        next_page = data.get("nextPageToken")
        if not next_page or len(videos) >= max_videos:
            break
        params["pageToken"] = next_page
        time.sleep(0.5)

    return videos[:max_videos]

def get_video_stats(video_ids):
    """動画の統計情報を取得"""
    stats = {}
    # 50件ずつAPIを叩く
    for i in range(0, len(video_ids), 50):
        chunk = video_ids[i:i+50]
        url = f"{BASE_URL}/videos"
        params = {
            "key": API_KEY,
            "id": ",".join(chunk),
            "part": "statistics",
        }
        r = requests.get(url, params=params)
        r.raise_for_status()
        for item in r.json().get("items", []):
            s = item.get("statistics", {})
            stats[item["id"]] = {
                "view_count": int(s.get("viewCount", 0)),
                "like_count": int(s.get("likeCount", 0)),
                "comment_count": int(s.get("commentCount", 0)),
            }
    return stats

def get_comments(video_id, max_comments=100):
    """動画のコメントを取得"""
    comments = []
    url = f"{BASE_URL}/commentThreads"
    params = {
        "key": API_KEY,
        "videoId": video_id,
        "part": "snippet",
        "maxResults": 100,
        "order": "relevance",  # 関連度順（いいね数の多いものが上）
    }

    while len(comments) < max_comments:
        try:
            r = requests.get(url, params=params)
            if r.status_code == 403:
                # コメント無効の動画
                break
            r.raise_for_status()
            data = r.json()

            for item in data.get("items", []):
                c = item["snippet"]["topLevelComment"]["snippet"]
                comments.append({
                    "text": c["textDisplay"],
                    "like_count": c.get("likeCount", 0),
                    "published_at": c["publishedAt"],
                    "author": c["authorDisplayName"],
                })

            next_page = data.get("nextPageToken")
            if not next_page or len(comments) >= max_comments:
                break
            params["pageToken"] = next_page
            time.sleep(0.3)
        except Exception as e:
            print(f"    コメント取得エラー: {e}")
            break

    return comments

def main():
    print("=== 「心の話 -きい-」コメントリサーチ ===\n")

    # Step 1: チャンネルを検索
    print("【チャンネル検索中...】")
    items = search_channel("心の話 きい")

    if not items:
        print("チャンネルが見つかりませんでした")
        return

    # 手動確認用にチャンネルIDを表示（上の検索結果から選択）
    channel_id = input("使用するチャンネルID を入力してください: ").strip()

    # Step 2: 動画一覧取得
    print(f"\n【動画一覧取得中...】（再生数TOP50）")
    videos = get_videos(channel_id, max_videos=50)
    print(f"  {len(videos)}本取得")

    # Step 3: 統計情報取得
    print("\n【統計情報取得中...】")
    video_ids = [v["video_id"] for v in videos]
    stats = get_video_stats(video_ids)

    for v in videos:
        v.update(stats.get(v["video_id"], {}))

    # 再生数でソート
    videos.sort(key=lambda x: x.get("view_count", 0), reverse=True)

    # Step 4: コメント取得（TOP20動画）
    print("\n【コメント取得中...】（TOP20動画）")
    all_comments = []

    for i, v in enumerate(videos[:20]):
        print(f"  [{i+1}/20] {v['title'][:40]}... (再生:{v.get('view_count',0):,})")
        comments = get_comments(v["video_id"], max_comments=100)
        for c in comments:
            c["video_id"] = v["video_id"]
            c["video_title"] = v["title"]
            c["video_views"] = v.get("view_count", 0)
        all_comments.extend(comments)
        time.sleep(0.5)

    # Step 5: CSV保存
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")

    # 動画リスト
    videos_file = f"kii_videos_{timestamp}.csv"
    with open(f"/home/user/mainmasahiro/{videos_file}", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=["video_id","title","published_at","view_count","like_count","comment_count"])
        w.writeheader()
        w.writerows(videos)

    # コメント一覧
    comments_file = f"kii_comments_{timestamp}.csv"
    with open(f"/home/user/mainmasahiro/{comments_file}", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=["video_title","video_views","like_count","text","author","published_at","video_id"])
        w.writeheader()
        # いいね数でソート
        all_comments.sort(key=lambda x: x.get("like_count", 0), reverse=True)
        w.writerows(all_comments)

    print(f"\n=== 完了 ===")
    print(f"動画リスト: {videos_file}（{len(videos)}本）")
    print(f"コメント: {comments_file}（{len(all_comments)}件）")

if __name__ == "__main__":
    main()
