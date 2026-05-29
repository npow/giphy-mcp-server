# giphy-mcp-server

MCP server for the [Giphy API](https://developers.giphy.com/) — search, trending, and random GIFs as tools for AI coding agents.

## Tools

| Tool | Description |
|------|-------------|
| `search_gifs` | Search for GIFs by query string |
| `get_trending_gifs` | Get currently trending GIFs |
| `get_random_gif` | Get a random GIF, optionally filtered by tag |
| `get_gif_by_id` | Get a specific GIF by its Giphy ID |
| `translate` | Translate a word or phrase to the perfect GIF |

## Setup

1. Get a free API key at [developers.giphy.com](https://developers.giphy.com/)
2. Set the `GIPHY_API_KEY` environment variable

## Usage

### With Claude Code

```json
{
  "mcpServers": {
    "giphy": {
      "command": "uvx",
      "args": ["giphy-mcp-server"],
      "env": {
        "GIPHY_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

### With pip

```bash
pip install giphy-mcp-server
giphy-mcp-server
```

### From source

```bash
git clone https://github.com/npow/giphy-mcp-server.git
cd giphy-mcp-server
pip install -e .
giphy-mcp-server
```

## Development

```bash
pip install -e ".[test]"
pytest
```

## License

MIT
