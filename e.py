import flask
import requests
import re
from urllib.parse import urljoin

app = flask.Flask(__name__)

HTML_FORM = '''
<!DOCTYPE html>
<html>
<head>
  <title>Google</title>
  <style>
    body {{ background: #00004d; }}
    form {{ margin-top: 2em; }}
    input[type="text"] {{ color: #000000; background: #cccccc; width: 400px; font-size: 1.2em; padding: 8px; display: block; margin: 0 auto;}}
    .error {{ color: red; }}
  </style>
</head>
<body>
  <form method="post" action="/">
    <input type="text" id="url" name="url" placeholder="Enter URL" required>
  </form>
  {error}
</body>
</html>
'''

def rewrite_html_assets(html, page_url):
    # Rewrite asset URLs to go through the proxy
    def rewrite(pattern, repl):
        return re.sub(pattern, repl, html, flags=re.IGNORECASE)

    html = rewrite(r'<link([^>]*)href=["\']([^"\']+)["\']([^>]*)>', lambda m: f'<link{m.group(1)}href="/asset?url={urljoin(page_url, m.group(2))}"{m.group(3)}>')
    html = rewrite(r'<script([^>]*)src=["\']([^"\']+)["\']([^>]*)>', lambda m: f'<script{m.group(1)}src="/asset?url={urljoin(page_url, m.group(2))}"{m.group(3)}>')
    html = rewrite(r'<img([^>]*)src=["\']([^"\']+)["\']([^>]*)>', lambda m: f'<img{m.group(1)}src="/asset?url={urljoin(page_url, m.group(2))}"{m.group(3)}>')
    html = rewrite(r'<video([^>]*)src=["\']([^"\']+)["\']([^>]*)>', lambda m: f'<video{m.group(1)}src="/asset?url={urljoin(page_url, m.group(2))}"{m.group(3)}>')
    html = rewrite(r'<audio([^>]*)src=["\']([^"\']+)["\']([^>]*)>', lambda m: f'<audio{m.group(1)}src="/asset?url={urljoin(page_url, m.group(2))}"{m.group(3)}>')
    html = rewrite(r'<source([^>]*)src=["\']([^"\']+)["\']([^>]*)>', lambda m: f'<source{m.group(1)}src="/asset?url={urljoin(page_url, m.group(2))}"{m.group(3)}>')
    html = rewrite(r'<embed([^>]*)src=["\']([^"\']+)["\']([^>]*)>', lambda m: f'<embed{m.group(1)}src="/asset?url={urljoin(page_url, m.group(2))}"{m.group(3)}>')
    html = rewrite(r'<iframe([^>]*)src=["\']([^"\']+)["\']([^>]*)>', lambda m: f'<iframe{m.group(1)}src="/asset?url={urljoin(page_url, m.group(2))}"{m.group(3)}>')

    # Navigation
    def repl_a(match):
        before, href, after = match.group(1), match.group(2), match.group(3)
        if href.startswith('#') or href.startswith('mailto:') or href.startswith('javascript:'):
            return f'<a{before}href="{href}"{after}>'
        abs_url = urljoin(page_url, href)
        return f'<a{before}href="/?url={abs_url}"{after}>'
    html = re.sub(r'<a([^>]*)href=["\']([^"\']+)["\']([^>]*)>', repl_a, html, flags=re.IGNORECASE)

    return html

def rewrite_css_urls(css, css_url):
    def url_repl(m):
        asset = m.group(1).strip('\'"')
        return f"url(/asset?url={urljoin(css_url, asset)})"
    css = re.sub(r'url\(([^)]+)\)', url_repl, css)
    def import_repl(m):
        asset = m.group(1).strip('\'"')
        return f'@import "/asset?url={urljoin(css_url, asset)}"'
    css = re.sub(r'@import\s+["\']([^"\']+)["\']', import_repl, css)
    return css

@app.route("/", methods=["GET", "POST"])
def home():
    error = ""
    url = ""
    if flask.request.method == "POST":
        url = flask.request.form.get("url")
    elif flask.request.method == "GET":
        url = flask.request.args.get("url")
    if url:
        try:
            resp = requests.get(url, allow_redirects=True)
            final_url = resp.url
            content_type = resp.headers.get('Content-Type', '')
            if 'text/html' in content_type:
                html = resp.content.decode(resp.encoding or 'utf-8', errors='replace')
                html = rewrite_html_assets(html, final_url)
                return html
            else:
                return "<pre>" + resp.content.decode('utf-8', errors='replace') + "</pre>"
        except Exception as e:
            error = f'<p class="error">Error: {e}</p>'
            return HTML_FORM.format(error=error)
    return HTML_FORM.format(error=error)

@app.route("/asset")
def asset():
    url = flask.request.args.get("url")
    if not url:
        return "No asset URL provided", 400
    try:
        r = requests.get(url, stream=True)
        content_type = r.headers.get('Content-Type', 'application/octet-stream')
        content = r.content
        if 'text/css' in content_type:
            css = content.decode(r.encoding or 'utf-8', errors='replace')
            css = rewrite_css_urls(css, url)
            resp = flask.Response(css)
            resp.headers['Content-Type'] = content_type
            return resp
        else:
            resp = flask.Response(content)
            resp.headers['Content-Type'] = content_type
            return resp
    except Exception as e:
        return f"Error loading asset: {e}", 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8081)