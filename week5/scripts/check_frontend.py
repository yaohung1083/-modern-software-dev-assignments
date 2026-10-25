"""Execute the mocked React integration harness without starting a server."""

import mimetypes
import os
from pathlib import Path
from urllib.parse import urlparse

from playwright.sync_api import sync_playwright

FRONTEND = Path(__file__).resolve().parents[1] / "frontend"


def main() -> None:
    with sync_playwright() as playwright:
        options = {"headless": True}
        if executable := os.getenv("WEEK5_CHROMIUM_EXECUTABLE"):
            options["executable_path"] = executable
        browser = playwright.chromium.launch(**options)
        try:
            page = browser.new_page()

            def serve(route):
                target = (FRONTEND / urlparse(route.request.url).path.lstrip("/")).resolve()
                if not target.is_relative_to(FRONTEND) or not target.is_file():
                    route.fulfill(status=404, body="Not found")
                    return
                route.fulfill(
                    path=str(target),
                    content_type=mimetypes.guess_type(target.name)[0] or "text/plain",
                )

            page.route("http://week5.test/**", serve)
            page.goto("http://week5.test/tests.html")
            page.wait_for_function(
                "['passed','failed'].includes(document.getElementById('test-results').dataset.status)",
                timeout=60000,
            )
            output = page.locator("#test-results")
            print(output.inner_text())
            if output.get_attribute("data-status") != "passed":
                raise RuntimeError("Frontend integration tests failed")
        finally:
            browser.close()


if __name__ == "__main__":
    main()
