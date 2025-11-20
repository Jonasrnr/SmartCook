import instaloader

def getInstaDesc(url: str) -> str:
    """
    Extrahiert die Beschreibung eines öffentlichen Instagram-Reels über instaloader.
    Funktioniert zuverlässig bei öffentlichen Reels.
    """
    shortcode = url.rstrip("/").split("/")[-1]
    loader = instaloader.Instaloader(
        download_pictures=False,
        download_videos=False,
        download_comments=False,
        save_metadata=False,
        quiet=True
    )

    try:
        post = instaloader.Post.from_shortcode(loader.context, shortcode)
        print(post)
        print(post.url)
        return (post.caption, post.url) or None
    except Exception as e:
        print(f"Fehler: {e}")
        return None