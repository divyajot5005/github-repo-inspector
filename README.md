# github-repo-inspector
An MCP-style control panel for Git repositories. Provides repository overviews, status checks, and branch comparison summaries. Features smart Obsidian integration to auto-generate daily development logs, analysis notes, and link commits to features.

# GitHub MCP Server Setup Guide

## 🚀 Quick Setup (5 minutes)

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Get GitHub Token (Optional but Recommended)
1. Go to GitHub Settings → Developer settings → Personal access tokens
2. Generate new token (classic)
3. Select scopes: `repo`, `read:org`, `read:user`
4. Copy the token

### 3. Configure Claude Desktop
Add to your Claude Desktop MCP config file:

```json
{
  "mcpServers": {
    "github-inspector": {
      "command": "python",
      "args": ["/path/to/server.py"],
      "env": {
        "GITHUB_TOKEN": "ghp_your_token_here"
      }
    }
  }
}
```

### 4. Test the Server
```bash
python server.py
```

## 🎯 Usage Examples

Once connected to Claude:

### Basic GitHub Operations
```
"Clone https://github.com/microsoft/vscode to /tmp/vscode and set up analysis"
"Show me the current git status"
"Get the last 10 commits from the main branch"
"Show me open issues for this repository"
"List all open pull requests"
```

### Advanced Analysis & Export
```
"Compare the main branch with develop branch and export to Obsidian as 'Branch Analysis'"
"Get all issues labeled 'bug' and export to Obsidian"
"Create a weekly development summary and save to Obsidian"
"Analyze recent commits and suggest workflow improvements"
```

## 📊 What Gets Exported to Obsidian

### File Structure
```
Your-Vault/
├── Git Analysis/
│   ├── 2025-08-22-123456-Weekly Review.md
│   ├── 2025-08-22-123501-Issue Analysis.md
│   └── 2025-08-22-123520-PR Summary.md
├── Branch Analysis/
│   └── 2025-08-22-124000-main-vs-develop.md
└── GitHub Data/
    ├── 2025-08-22-124500-Open Issues.md
    └── 2025-08-22-125000-Recent PRs.md
```

### Note Features
- **YAML frontmatter** with tags, timestamps, repo info
- **GitHub links** automatically added
- **Markdown formatting** for readability
- **Cross-references** between related notes
- **Search-friendly** tags and metadata

## 🔧 Features

### Local Git Operations
- ✅ Repository status and working directory changes
- ✅ Commit history with visual graphs
- ✅ Branch comparisons and diffs
- ✅ File-specific analysis

### GitHub Integration
- ✅ Clone repositories directly from GitHub URLs
- ✅ Fetch issues with filtering (open/closed/labels)
- ✅ Get pull requests with detailed info
- ✅ Repository statistics and metadata
- ✅ Automatic rate limiting and error handling

### Obsidian Export
- ✅ Organized folder structure
- ✅ Rich metadata and cross-linking
- ✅ GitHub-flavored markdown
- ✅ Automatic timestamping and tagging

## 🛠 Troubleshooting

### Common Issues

**"GitHub API request failed: 403"**
- Add a GitHub token to increase rate limits
- Check token permissions (needs `repo` scope)

**"Repository not found"**
- Ensure the GitHub URL is correct
- For private repos, token must have access

**"Obsidian export failed"**
- Check vault path exists and is writable
- Ensure folder structure permissions

### Rate Limits
- **Without token**: 60 requests/hour
- **With token**: 5000 requests/hour
- Server automatically handles rate limiting

## 🔒 Security Notes

- GitHub tokens are stored in environment variables
- Never commit tokens to version control
- Use minimal required token permissions
- Consider using fine-grained tokens for better security

## 🚀 Ready to Use!

The server will work immediately with any public GitHub repository. For private repos or higher rate limits, add your GitHub token to the configuration.

Start with: `"Clone https://github.com/owner/repo and analyze it"`
