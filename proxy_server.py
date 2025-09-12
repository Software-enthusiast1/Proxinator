import flask
import requests

app = flask.Flask(__name__)

@app.route('/', defaults={'path': ''}, methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH'])
@app.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH'])
def proxy(path):
    url = flask.request.args.get('url')
    if not url:
        url = f"http://{path}"
    method = flask.request.method

    headers = {key: value for key, value in flask.request.headers if key != 'Host'}
    data = flask.request.get_data()

    try:
        resp = requests.request(
            method,
            url,
            headers=headers,
            data=data,
            allow_redirects=False,
        )
        excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
        response_headers = [(name, value) for (name, value) in resp.raw.headers.items() if name.lower() not in excluded_headers]
        return (resp.content, resp.status_code, response_headers)
    except Exception as e:
        return f"Error: {e}", 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
