"""Reddit API ツール。

Reddit (r/wallstreetbets, r/stocks 等) から投稿を取得し、
個人投資家のセンチメントを分析する。
無料枠: 100 req/min (OAuth 認証時)
"""

import praw

from ..config.settings import REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USER_AGENT


def _get_reddit_client() -> praw.Reddit:
    """Reddit API クライアントを生成する。"""
    return praw.Reddit(
        client_id=REDDIT_CLIENT_ID,
        client_secret=REDDIT_CLIENT_SECRET,
        user_agent=REDDIT_USER_AGENT,
    )


def get_reddit_hot_posts(
    subreddits: str = "wallstreetbets,stocks,investing",
    limit: int = 20,
) -> dict:
    """Reddit の人気投稿を取得する。

    指定したサブレディットの HOT 投稿を取得し、
    個人投資家の注目トピックを把握する。

    Args:
        subreddits: カンマ区切りのサブレディット名
            (例: "wallstreetbets,stocks,investing")
        limit: サブレディットごとの取得件数 (デフォルト: 20)

    Returns:
        各サブレディットの人気投稿リスト (タイトル, スコア, コメント数等)
    """
    reddit = _get_reddit_client()
    subreddit_list = [s.strip() for s in subreddits.split(",")]

    all_posts = []
    for sub_name in subreddit_list:
        subreddit = reddit.subreddit(sub_name)
        for post in subreddit.hot(limit=limit):
            if post.stickied:
                continue
            all_posts.append({
                "subreddit": sub_name,
                "title": post.title,
                "score": post.score,
                "upvote_ratio": post.upvote_ratio,
                "num_comments": post.num_comments,
                "created_utc": post.created_utc,
                "selftext": post.selftext[:500] if post.selftext else "",
                "url": f"https://reddit.com{post.permalink}",
            })

    all_posts.sort(key=lambda x: x["score"], reverse=True)

    return {
        "subreddits": subreddit_list,
        "total_posts": len(all_posts),
        "posts": all_posts,
    }


def search_reddit_posts(
    query: str,
    subreddits: str = "wallstreetbets,stocks,investing",
    sort: str = "relevance",
    limit: int = 20,
) -> dict:
    """Reddit でキーワード検索を行う。

    特定の銘柄やトピックに関する投稿を検索し、
    個人投資家の議論内容と感情を把握する。

    Args:
        query: 検索キーワード (例: "AAPL earnings", "Tesla")
        subreddits: カンマ区切りのサブレディット名
            (例: "wallstreetbets,stocks")
        sort: ソート順 ("relevance", "hot", "top", "new", "comments")
        limit: サブレディットごとの取得件数

    Returns:
        検索結果の投稿リスト
    """
    reddit = _get_reddit_client()
    subreddit_list = [s.strip() for s in subreddits.split(",")]

    all_posts = []
    for sub_name in subreddit_list:
        subreddit = reddit.subreddit(sub_name)
        for post in subreddit.search(query, sort=sort, limit=limit):
            all_posts.append({
                "subreddit": sub_name,
                "title": post.title,
                "score": post.score,
                "upvote_ratio": post.upvote_ratio,
                "num_comments": post.num_comments,
                "created_utc": post.created_utc,
                "selftext": post.selftext[:500] if post.selftext else "",
                "url": f"https://reddit.com{post.permalink}",
            })

    all_posts.sort(key=lambda x: x["score"], reverse=True)

    return {
        "query": query,
        "subreddits": subreddit_list,
        "total_posts": len(all_posts),
        "posts": all_posts,
    }
