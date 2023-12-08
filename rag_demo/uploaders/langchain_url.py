def extract_urls(text:str)->list[str]:
    x = text.split()
    res = []
    for i in x:
        if i.startswith("https:") or i.startswith("http:"):
            res.append(i)
    return res

# def webpage_description(url) -> str:
