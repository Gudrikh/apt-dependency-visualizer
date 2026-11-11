"""Проверки полей Packages, альтернатив и получения по HTTP."""

import gzip
import lzma
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from src.apt import load_apt_repository, parse_packages


INDEX = """Package: test-app
Pre-Depends: startup
Depends: liba (>= 2), libb:any |
 libc, liba
Description: описание пакета
 Depends: эту строку нельзя принять за поле

Package: liba
Version: 2

Package: liba
Version: 1
Depends: old-lib
"""
EXPECTED = {"test-app": ("liba", "libb", "libc", "startup"), "liba": ()}


class IndexHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        data = INDEX.encode("utf-8")
        responses = {
            "/Packages": data,
            "/Packages.gz": gzip.compress(data),
            "/Packages.xz": lzma.compress(data),
            "/invalid.gz": b"\x1f\x8b",
        }
        if self.path not in responses:
            self.send_error(404)
            return
        self.send_response(200)
        self.end_headers()
        self.wfile.write(responses[self.path])

    def log_message(self, *_):
        pass


class AptTests(unittest.TestCase):
    def test_control_parser(self):
        self.assertEqual(parse_packages(INDEX), EXPECTED)

    def test_non_index(self):
        with self.assertRaisesRegex(ValueError, "Package"):
            parse_packages("<html>Error</html>")

    def test_http_formats(self):
        with ThreadingHTTPServer(("127.0.0.1", 0), IndexHandler) as server:
            thread = threading.Thread(target=server.serve_forever)
            thread.start()
            url = f"http://127.0.0.1:{server.server_port}/"
            try:
                for name in ("", "Packages", "Packages.gz", "Packages.xz"):
                    with self.subTest(name=name):
                        self.assertEqual(load_apt_repository(url + name),
                                         EXPECTED)
                with self.assertRaisesRegex(ValueError, "404"):
                    load_apt_repository(url + "absent")
                with self.assertRaisesRegex(ValueError, "неверный индекс"):
                    load_apt_repository(url + "invalid.gz")
            finally:
                server.shutdown()
                thread.join()
