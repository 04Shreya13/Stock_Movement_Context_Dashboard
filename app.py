"""Serve the local Stock Context website: python app.py [--port 8501]."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit
import argparse
import gzip
import webbrowser


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8501)
    parser.add_argument('--no-browser', action='store_true')
    args = parser.parse_args()
    root = Path(__file__).resolve().parent / 'web'
    types = {'index.html': 'text/html', 'style.css': 'text/css',
             'app.js': 'text/javascript', 'data.js': 'text/javascript',
             'summaries.js': 'text/javascript'}
    assets = {}
    for name, content_type in types.items():
        path = root / name
        if not path.is_file():
            parser.exit(1, f'Missing website asset: {path}\n')
        raw = path.read_bytes()
        assets['/' + name] = (raw, gzip.compress(raw), content_type)
    assets['/'] = assets['/index.html']

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.respond(True)

        def do_HEAD(self):
            self.respond(False)

        def respond(self, send_body):
            asset = assets.get(urlsplit(self.path).path)
            if asset is None:
                self.send_error(404)
                return
            raw, compressed, content_type = asset
            encodings = self.headers.get('Accept-Encoding', '').split(',')
            use_gzip = any(e.strip().lower() == 'gzip' for e in encodings)
            body = compressed if use_gzip else raw
            self.send_response(200)
            self.send_header('Content-Type', content_type + '; charset=utf-8')
            self.send_header('Content-Length', str(len(body)))
            self.send_header('Cache-Control', 'no-cache')
            self.send_header('Vary', 'Accept-Encoding')
            if use_gzip:
                self.send_header('Content-Encoding', 'gzip')
            self.end_headers()
            if send_body:
                self.wfile.write(body)

    try:
        server = ThreadingHTTPServer(('127.0.0.1', args.port), Handler)
    except OSError:
        parser.exit(1, 'Port unavailable. Try: python app.py --port 8502\n')
    url = f'http://127.0.0.1:{server.server_port}/'
    print(f'Stock Context is running at {url}', flush=True)
    print('Press Ctrl+C to stop.', flush=True)
    if not args.no_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == '__main__':
    main()
