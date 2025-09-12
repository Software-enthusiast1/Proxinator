import flask
import requests

app = flask.Flask(__name__)

FORM_HTML = '''
<!DOCTYPE html>
<html>
<head>
  <title>Proxinator</title>
</head>
<body>
  <form method="post">
    <label for="url">Enter a URL:</label>
    <input type="text" id="url" name="url" placeholder="http://example.com" size="40" required>
  </form>
  {error}
</body>
</html>
'''

@app.route("/", methods=["GET", "POST"])
def home():
    error = ""
    if flask.request.method == "POST":
        url = flask.request.form.get("url")
        if not url:
            error = "<p style='color:red;'>Please enter a URL!</p>"
            return FORM_HTML.format(error=error)
        try:
            resp = requests.get(url)
            content = resp.content
            content_type = resp.headers.get('Content-Type', '')
            if 'text/html' in content_type:
                html = content.decode(resp.encoding or 'utf-8', errors='replace')
                # Display raw HTML as returned by the site (preserves CSS links and styles)
                return FORM_HTML.format(error=error) + "<hr>" + html
            else:
                # Non-html content
                return FORM_HTML.format(error=error) + "<hr><pre>" + content.decode('utf-8', errors='replace') + "</pre>"
        except Exception as e:
            error = f"<p style='color:red;'>Error: {e}</p>"
            return FORM_HTML.format(error=error)
    return FORM_HTML.format(error=error)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)