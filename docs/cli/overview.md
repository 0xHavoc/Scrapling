# Command Line Interface

Since v0.3, Scrapling includes a powerful command-line interface that provides three main capabilities:

1. **Interactive Shell**: An interactive Web Scraping shell based on IPython that provides many shortcuts and useful tools
2. **Extract Commands**: Scrape websites from the terminal without any programming
3. **Utility Commands**: Installation and management tools
4. **Web UI**: Run a local browser interface for quick scraping

```bash
# Launch interactive shell
scrapling shell

# Convert the content of a page to markdown and save it to a file
scrapling extract get "https://example.com" content.md

# Get help for any command
scrapling --help
scrapling extract --help
# Launch web interface
scrapling web --host 127.0.0.1 --port 8765
```

## Requirements
This section requires you to install the extra `shell` dependency group, like the following:
```bash
pip install "scrapling[shell]"
```
and the installation of the fetchers' dependencies with the following command
```bash
scrapling install
```
This downloads all browsers, along with their system dependencies and fingerprint manipulation dependencies.

## Web UI
Install the `web` extra to run the local interface:
```bash
pip install "scrapling[web]"
```
Then launch it with `scrapling web` and open the shown URL in your browser. The command serves a built-in frontend and `/api/*` endpoints from the Web API.
