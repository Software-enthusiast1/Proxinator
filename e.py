import flask
import requests
import re
from urllib.parse import urljoin

app = flask.Flask(__name__)

FORM_HTML = '''
<!DOCTYPE html>
<html>
<head>
  <title>Google</title>
</head>
<body>
  <form method="post" action="/">
    <input type="text" id="url" name="url" placeholder="Enter URL here" size="40" required>
  </form>
  {error}
</body>
</html>
'''

def rewrite_html_assets(html, page_url):
    # Rewrite <link href="..."> for CSS
    def repl_link(match):
        before = match.group(1)
        href = match.group(2)
        after = match.group(3)
        abs_url = urljoin(page_url, href)
        return f'<link{before}href="/asset?url={abs_url}"{after}>'
    html = re.sub(r'<link([^>]*)href=["\']([^"\']+)["\']([^>]*)>', repl_link, html, flags=re.IGNORECASE)

    # Rewrite <script src="..."> for JS
    def repl_script(match):
        before = match.group(1)
        src = match.group(2)
        after = match.group(3)
        abs_url = urljoin(page_url, src)
        return f'<script{before}src="/asset?url={abs_url}"{after}>'
    html = re.sub(r'<script([^>]*)src=["\']([^"\']+)["\']([^>]*)>', repl_script, html, flags=re.IGNORECASE)

    # Rewrite <img src="..."> for images
    def repl_img(match):
        before = match.group(1)
        src = match.group(2)
        after = match.group(3)
        abs_url = urljoin(page_url, src)
        return f'<img{before}src="/asset?url={abs_url}"{after}>'
    html = re.sub(r'<img([^>]*)src=["\']([^"\']+)["\']([^>]*)>', repl_img, html, flags=re.IGNORECASE)

    # Rewrite <a href="..."> for navigation
    def repl_a(match):
        before = match.group(1)
        href = match.group(2)
        after = match.group(3)
        abs_url = urljoin(page_url, href)
        # Don't rewrite anchor, mailto, javascript links
        if href.startswith('#') or href.startswith('mailto:') or href.startswith('javascript:'):
            return f'<a{before}href="{href}"{after}>'
        else:
            return f'<a{before}href="/?url={abs_url}"{after}>'
    html = re.sub(r'<a([^>]*)href=["\']([^"\']+)["\']([^>]*)>', repl_a, html, flags=re.IGNORECASE)

    return html

def rewrite_css_urls(css, css_url):
    def repl_url(match):
        orig_url = match.group(1).strip('\'"')
        abs_url = urljoin(css_url, orig_url)
        return f'url(/asset?url={abs_url})'
    css = re.sub(r'url\(([^)]+)\)', repl_url, css)

    def repl_import(match):
        import_url = match.group(1).strip('\'"')
        abs_url = urljoin(css_url, import_url)
        return f'@import "/asset?url={abs_url}"'
    css = re.sub(r'@import\s+["\']([^"\']+)["\']', repl_import, css)
    return css

@app.route("/", methods=["GET", "POST"])
def home():
    error = ""
    url = ""
    show_form = True
    if flask.request.method == "POST":
        url = flask.request.form.get("url")
        show_form = False
    elif flask.request.method == "GET":
        url = flask.request.args.get("url")
        if url:
            show_form = False
    if url:
        try:
            resp = requests.get(url, allow_redirects=True)
            final_url = resp.url
            content_type = resp.headers.get('Content-Type', '')
            if 'text/html' in content_type:
                html = resp.content.decode(resp.encoding or 'utf-8', errors='replace')
                html = rewrite_html_assets(html, final_url)
                # Only show the form if show_form is True
                if show_form:
                    return FORM_HTML.format(error=error) + "<hr>" + html
                else:
                    return html
            else:
                if show_form:
                    return FORM_HTML.format(error=error) + "<hr><pre>" + resp.content.decode('utf-8', errors='replace') + "</pre>"
                else:
                    return "<pre>" + resp.content.decode('utf-8', errors='replace') + "</pre>"
        except Exception as e:
            error = f"<p style='color:red;'>Error: {e}</p>"
            return FORM_HTML.format(error=error)
    return FORM_HTML.format(error=error)

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