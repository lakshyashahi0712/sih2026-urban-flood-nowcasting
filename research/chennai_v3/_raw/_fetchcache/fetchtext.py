"""Fetch a URL and print readable text (HTML stripped). Usage: python fetchtext.py URL [outfile]"""
import sys, re, urllib.request, gzip

url = sys.argv[1]
outfile = sys.argv[2] if len(sys.argv) > 2 else None

REQ_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Encoding": "gzip",
}

try:
    with urllib.request.urlopen(urllib.request.Request(url, headers=REQ_HEADERS), timeout=45) as r:
        raw = r.read()
        if raw[:2] == b"\x1f\x8b":
            raw = gzip.decompress(raw)
        ctype = r.headers.get("Content-Type", "")
        status = r.status
        final_url = r.geturl()
except Exception as e:
    print("FETCH-ERROR: %s: %s" % (type(e).__name__, e))
    sys.exit(0)

try:
    text = raw.decode("utf-8", errors="replace")
except Exception:
    text = raw.decode("latin-1", errors="replace")

if "html" in ctype or text.lstrip().lower().startswith(("<!doctype", "<html")):
    text = re.sub(r"(?is)<(script|style|noscript|svg|head)[^>]*>.*?</\1>", " ", text)
    text = re.sub(r"(?is)<br\s*/?>", "\n", text)
    text = re.sub(r"(?is)</(p|div|li|tr|h[1-6]|td|th|section|article)>", "\n", text)
    text = re.sub(r"(?s)<!--.*?-->", " ", text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = text.replace("&nbsp;", " ")
    text = text.replace("&#39;", "'")
    text = text.replace("&#x27;", "'")
    text = text.replace(chr(38) + "quot;", chr(34))
    text = text.replace(chr(38) + "#34;", chr(34))
    text = text.replace(chr(38) + "amp;", chr(38))
    text = text.replace(chr(8217), chr(39))
    text = text.replace(chr(8216), chr(39))
    text = text.replace(chr(8220), chr(34))
    text = text.replace(chr(8221), chr(34))
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n", text)

header = "STATUS: %s\nFINAL-URL: %s\nCONTENT-TYPE: %s\n%s\n" % (status, final_url, ctype, "=" * 60)
if outfile:
    with open(outfile, "w", encoding="utf-8") as f:
        f.write(header + text)
    print("WROTE %d chars to %s" % (len(text), outfile))
else:
    print(header + text)
