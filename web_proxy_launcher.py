from flask import Flask, request, redirect, render_template_string

app = Flask(__name__)

HTML_FORM = '''
<!DOCTYPE html>
<html>
<head>
  <title>Proxy URL Entry</title>
  <style>
    body { background: #e6f0ff; }
    h2 { color: #003366; }
    form { margin-top: 2em; }
    input[type="text"] { width: 400px; font-size: 1.2em; padding: 8px; }
    button { font-size: 1.2em; padding: 8px 16px; background: #0074d9; color: white; border: none; border-radius: 4px; cursor: pointer; }
    button:hover { background: #005fa3; }
  </style>
</head>
<body>
  <h2>Web Proxy Launcher</h2>
  <form method="post">
    <label for="url">Enter a URL:</label>
    <input type="text" id="url" name="url" placeholder="http://example.com" required>
    <button type="submit">Go</button>
  </form>
  {% if error %}
    <p style="color: red;">{{ error }}</p>
  {% endif %}
</body>
</html>
'''

@app.route("/", methods=["GET", "POST"])
def index():
    error = ""
    if request.method == "POST":
        url = request.form.get("url")
        if not url:
            error = "Please enter a URL."
        elif not (url.startswith("http://") or url.startswith("https://")):
            error = "URL must start with http:// or https://"
        else:
            return redirect(url)
    return render_template_string(HTML_FORM, error=error)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)