from mitmproxy import http

def request(flow: http.HTTPFlow) -> None:
    print(f"Request: {flow.request.method} {flow.request.pretty_url}")
    flow.request.headers["X-Proxy-Intercepted"] = "true"

def response(flow: http.HTTPFlow) -> None:
    print(f"Response: {flow.request.pretty_url} -> {flow.response.status_code}")
    if flow.response.headers.get("content-type", "").startswith("text/html"):
        flow.response.text = flow.response.text.replace(
            "</body>",
            '<div style="background:yellow;padding:10px;text-align:center;">Served via mitmproxy!</div></body>'
        )