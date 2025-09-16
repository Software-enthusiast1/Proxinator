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
  <style>
    html, body {{ height: 100%; margin: 0; padding: 0; }}
    #particles-js {{
      position: fixed;
      width: 100vw;
      height: 100vh;
      top: 0;
      left: 0;
      z-index: 0;
      background: #222;
    }}
    body {{
      min-height: 100vh;
      position: relative;
      z-index: 1;
      overflow: hidden;
    }}
    .center-content {{
      position: absolute;
      top: 50%;
      left: 50%;
      transform: translate(-50%, -50%);
      z-index: 1;
      background: rgba(102, 102, 102,0.75);
      padding: 2em;
      border-radius: 10px;
      box-shadow: 0 4px 24px rgba(0,0,0,0.2);
      text-align: center;
    }}
    h2 {{ color: #0a6fc2; margin-bottom: 1em; }}
    form {{ margin-top: 1em; }}
    input[type="text"] {{ width: 400px; font-size: 1.2em; padding: 8px; }}
    .error {{ color: red; }}
  </style>
  <!-- Import particles.js from CDN -->
  <script src="https://cdn.jsdelivr.net/npm/particles.js@2.0.0/particles.min.js"></script>
</head>
<body>
  <div id="particles-js"></div>
  <div class="center-content">
    <h2>Proxinator</h2>
    <form method="post" action="/">
      <input type="text" id="url" name="url" placeholder="Enter a URL" required>
    </form>
    {error}
  </div>
  <!-- Initialize particles.js -->
  <script>
    particlesJS("particles-js", {{
      "particles": {{
        "number": {{
          "value": 120,
          "density": {{
            "enable": true,
            "value_area": 800
          }}
        }},
        "color": {{
          "value": "#2196F3"
        }},
        "shape": {{
          "type": "circle",
          "stroke": {{
            "width": 0,
            "color": "#000000"
          }},
          "polygon": {{
            "nb_sides": 5
          }}
        }},
        "opacity": {{
          "value": 0.5,
          "random": false,
          "anim": {{
            "enable": false,
            "speed": 1,
            "opacity_min": 0.1,
            "sync": false
          }}
        }},
        "size": {{
          "value": 3,
          "random": true,
          "anim": {{
            "enable": false,
            "speed": 40,
            "size_min": 0.1,
            "sync": false
          }}
        }},
        "line_linked": {{
          "enable": true,
          "distance": 150,
          "color": "#2196F3",
          "opacity": 0.4,
          "width": 1
        }},
        "move": {{
          "enable": true,
          "speed": 6,
          "direction": "none",
          "random": false,
          "straight": false,
          "out_mode": "out",
          "bounce": false,
          "attract": {{
            "enable": false,
            "rotateX": 600,
            "rotateY": 1200
          }}
        }}
      }},
      "interactivity": {{
        "detect_on": "canvas",
        "events": {{
          "onhover": {{
            "enable": true,
            "mode": "repulse"
          }},
          "onclick": {{
            "enable": true,
            "mode": "push"
          }},
          "resize": true
        }},
        "modes": {{
          "grab": {{
            "distance": 400,
            "line_linked": {{
              "opacity": 1
            }}
          }},
          "bubble": {{
            "distance": 400,
            "size": 40,
            "duration": 2,
            "opacity": 8,
            "speed": 3
          }},
          "repulse": {{
            "distance": 200,
            "duration": 0.4
          }},
          "push": {{
            "particles_nb": 4
          }},
          "remove": {{
            "particles_nb": 2
          }}
        }}
      }},
      "retina_detect": true
    }});
  </script>
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