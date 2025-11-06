def getTikTokDesc(url: str) -> str:
    import requests

    api_url = f"https://www.tiktok.com/oembed?url={url}"

    r = requests.get(api_url)

    data = r.json()
    print(data)
    recipe_text = data.get("title", "")
    thumbnail = data.get("thumbnail_url", "")

    return (recipe_text, thumbnail)
