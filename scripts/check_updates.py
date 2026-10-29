#!/usr/bin/env python3
"""Check this project's binary releases without downloading or compiling sources."""
import json
import urllib.error
import urllib.request

CURRENT = "0.2.2"
URL = "https://api.github.com/repos/seba970423/JamesDSP-Native-Arch-Remake/releases/latest"


def main():
    request = urllib.request.Request(URL, headers={"User-Agent": "JamesDSP-Native-Arch-Remake/" + CURRENT})
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            release = json.load(response)
        tag = release.get("tag_name", "")
        if tag.lstrip("v") == CURRENT:
            print("The bundled prebuilt release is current:", CURRENT)
        else:
            print("Published prebuilt release:", tag)
            print("Download its complete bundle to update:", release.get("html_url", URL))
            print("Continuing with this bundle's verified engines:", CURRENT)
    except urllib.error.HTTPError as error:
        if error.code == 404:
            print("No binary release is published yet. Using the bundled verified engines:", CURRENT)
        else:
            print("Release check unavailable. Using the bundled verified engines:", CURRENT)
    except (OSError, ValueError):
        print("Release check unavailable. Using the bundled verified engines:", CURRENT)


if __name__ == "__main__":
    main()
