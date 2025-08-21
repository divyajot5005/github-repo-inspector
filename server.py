#!/usr/bin/env python3
"""
Simple GitHub Repository Inspector MCP Server
"""

import asyncio
import json
import logging
import os
import subprocess
import aiohttp
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List
from urllib.parse import urlparse
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent#, MarkdownContent
from mcp.types import ServerInfo, ServerCapabilities



# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("github-mcp-server")

try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import Tool, TextContent
except ImportError as e:
    print(f"Error importing MCP: {e}")
    print("Please install: pip install mcp")
    exit(1)

# Global server instance
app = Server("github-inspector")

# Global state
repo_path = None
obsidian_vault_path = None
github_token = os.getenv('GITHUB_TOKEN')
github_owner = None
github_repo = None

@app.list_tools()
async def list_tools() -> List[Tool]:
    return [
        Tool(
            name="setup_github_repo",
            description="Setup GitHub repository for analysis",
            inputSchema={
                "type": "object",
                "properties": {
                    "github_url": {"type": "string", "description": "GitHub repository URL"},
                    "local_path": {"type": "string", "description": "Local path (optional)"},
                    "obsidian_vault": {"type": "string", "description": "Obsidian vault path (optional)"}
                },
                "required": ["github_url"]
            }
        ),
        Tool(
            name="git_status",
            description="Get current repository status",
            inputSchema={"type": "object", "properties": {}, "required": []}
        ),
        Tool(
            name="git_commits",
            description="Get recent commits",
            inputSchema={
                "type": "object",
                "properties": {"limit": {"type": "integer", "default": 10}},
                "required": []
            }
        ),
        Tool(
            name="github_issues",
            description="Get GitHub issues",
            inputSchema={
                "type": "object",
                "properties": {
                    "state": {"type": "string", "enum": ["open", "closed", "all"], "default": "open"},
                    "limit": {"type": "integer", "default": 10}
                },
                "required": []
            }
        ),
        Tool(
            name="github_prs",
            description="Get GitHub pull requests", 
            inputSchema={
                "type": "object",
                "properties": {
                    "state": {"type": "string", "enum": ["open", "closed", "all"], "default": "open"},
                    "limit": {"type": "integer", "default": 10}
                },
                "required": []
            }
        ),
        Tool(
            name="export_to_obsidian",
            description="Export analysis to Obsidian",
            inputSchema={
                "type": "object", 
                "properties": {
                    "content": {"type": "string"},
                    "note_name": {"type": "string"},
                    "category": {"type": "string", "default": "GitHub Analysis"}
                },
                "required": ["content", "note_name"]
            }
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    global repo_path, obsidian_vault_path, github_owner, github_repo
    
    try:
        if name == "setup_github_repo":
            github_url = arguments["github_url"]
            local_path = arguments.get("local_path")
            obsidian_vault = arguments.get("obsidian_vault")
            
            # Parse GitHub URL
            parsed = urlparse(github_url)
            if parsed.hostname != "github.com":
                return [TextContent(type="text", text="❌ Only GitHub URLs supported")]
            
            path_parts = parsed.path.strip('/').split('/')
            if len(path_parts) < 2:
                return [TextContent(type="text", text="❌ Invalid GitHub URL format")]
            
            github_owner = path_parts[0]
            github_repo = path_parts[1].replace('.git', '')
            
            # Set local path
            if not local_path:
                local_path = os.path.join(os.getcwd(), github_repo)
            
            # Clone or connect
            if os.path.exists(local_path) and os.path.exists(os.path.join(local_path, '.git')):
                repo_path = os.path.abspath(local_path)
                status = f"✅ Connected to existing repo: {repo_path}"
            else:
                try:
                    subprocess.run(["git", "clone", github_url, local_path], 
                                 capture_output=True, text=True, check=True)
                    repo_path = os.path.abspath(local_path)
                    status = f"✅ Cloned repo to: {repo_path}"
                except subprocess.CalledProcessError as e:
                    return [TextContent(type="text", text=f"❌ Clone failed: {e.stderr}")]
            
            # Set obsidian vault
            if obsidian_vault and os.path.exists(obsidian_vault):
                obsidian_vault_path = os.path.abspath(obsidian_vault)
                status += f"\n📝 Obsidian vault: {obsidian_vault_path}"
            
            status += f"\n🐙 GitHub: {github_owner}/{github_repo}"
            return [TextContent(type="text", text=status)]
            
        elif name == "git_status":
            if not repo_path:
                return [TextContent(type="text", text="❌ No repo setup. Use setup_github_repo first.")]
            
            try:
                result = subprocess.run(["git", "status", "--short"], 
                                      cwd=repo_path, capture_output=True, text=True)
                status_short = result.stdout.strip()
                
                result = subprocess.run(["git", "status"], 
                                      cwd=repo_path, capture_output=True, text=True)
                status_full = result.stdout.strip()
                
                output = f"## Git Status\n\n"
                if status_short:
                    output += f"**Changes:**\n```\n{status_short}\n```\n\n"
                output += f"**Full Status:**\n```\n{status_full}\n```"
                
                return [TextContent(type="text", text=output)]
            except Exception as e:
                return [TextContent(type="text", text=f"❌ Git status failed: {e}")]
                
        elif name == "git_commits":
            if not repo_path:
                return [TextContent(type="text", text="❌ No repo setup. Use setup_github_repo first.")]
            
            limit = arguments.get("limit", 10)
            
            try:
                result = subprocess.run([
                    "git", "log", f"-{limit}", 
                    "--pretty=format:%h|%an|%ad|%s", "--date=short"
                ], cwd=repo_path, capture_output=True, text=True)
                
                commits = result.stdout.strip().split('\n')
                output = f"## Recent Commits (Last {limit})\n\n"
                
                for commit in commits:
                    if '|' in commit:
                        parts = commit.split('|', 3)
                        if len(parts) >= 4:
                            hash_val, author, date, message = parts
                            output += f"- **{hash_val}** ({date}) {author}: {message}\n"
                
                return [TextContent(type="text", text=output)]
            except Exception as e:
                return [TextContent(type="text", text=f"❌ Git log failed: {e}")]
                
        elif name == "github_issues":
            if not github_owner or not github_repo:
                return [TextContent(type="text", text="❌ No GitHub repo setup.")]
            
            state = arguments.get("state", "open")
            limit = arguments.get("limit", 10)
            
            try:
                url = f"https://api.github.com/repos/{github_owner}/{github_repo}/issues"
                headers = {"Accept": "application/vnd.github.v3+json"}
                
                if github_token:
                    headers["Authorization"] = f"token {github_token}"
                
                params = {"state": state, "per_page": limit}
                
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, headers=headers, params=params) as response:
                        if response.status != 200:
                            error = await response.text()
                            return [TextContent(type="text", text=f"❌ GitHub API error: {response.status}\n{error}")]
                        
                        issues = await response.json()
                
                output = f"## GitHub Issues ({state}) - {github_owner}/{github_repo}\n\n"
                
                if not issues:
                    output += "No issues found.\n"
                    return [TextContent(type="text", text=output)]
                
                for issue in issues:
                    if 'pull_request' not in issue:  # Skip PRs
                        labels = ", ".join([l['name'] for l in issue.get('labels', [])])
                        output += f"**#{issue['number']}** {issue['title']}\n"
                        output += f"👤 {issue['user']['login']} • 📅 {issue['created_at'][:10]}"
                        if labels:
                            output += f" • 🏷️ {labels}"
                        output += f"\n🔗 {issue['html_url']}\n\n"
                
                return [TextContent(type="text", text=output)]
            except Exception as e:
                return [TextContent(type="text", text=f"❌ GitHub issues error: {e}")]
                
        elif name == "github_prs":
            if not github_owner or not github_repo:
                return [TextContent(type="text", text="❌ No GitHub repo setup.")]
            
            state = arguments.get("state", "open")
            limit = arguments.get("limit", 10)
            
            try:
                url = f"https://api.github.com/repos/{github_owner}/{github_repo}/pulls"
                headers = {"Accept": "application/vnd.github.v3+json"}
                
                if github_token:
                    headers["Authorization"] = f"token {github_token}"
                
                params = {"state": state, "per_page": limit}
                
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, headers=headers, params=params) as response:
                        if response.status != 200:
                            error = await response.text()
                            return [TextContent(type="text", text=f"❌ GitHub API error: {response.status}\n{error}")]
                        
                        prs = await response.json()
                
                output = f"## GitHub Pull Requests ({state}) - {github_owner}/{github_repo}\n\n"
                
                if not prs:
                    output += "No pull requests found.\n"
                    return [TextContent(type="text", text=output)]
                
                for pr in prs:
                    output += f"**#{pr['number']}** {pr['title']}\n"
                    output += f"👤 {pr['user']['login']} • 📅 {pr['created_at'][:10]}"
                    output += f" • {pr['head']['ref']} → {pr['base']['ref']}"
                    if pr.get('draft'):
                        output += " • 📝 Draft"
                    output += f"\n🔗 {pr['html_url']}\n\n"
                
                return [TextContent(type="text", text=output)]
            except Exception as e:
                return [TextContent(type="text", text=f"❌ GitHub PRs error: {e}")]
                
        elif name == "export_to_obsidian":
            if not obsidian_vault_path:
                return [TextContent(type="text", text="❌ No Obsidian vault configured.")]
            
            content = arguments["content"]
            note_name = arguments["note_name"]
            category = arguments.get("category", "GitHub Analysis")
            
            try:
                # Create folder
                folder_path = Path(obsidian_vault_path) / category
                folder_path.mkdir(parents=True, exist_ok=True)
                
                # Create filename
                timestamp = datetime.now().strftime("%Y-%m-%d-%H%M%S")
                filename = f"{timestamp}-{note_name.replace(' ', '-')}.md"
                file_path = folder_path / filename
                
                # Create content with metadata
                full_content = f"""---
created: {datetime.now().isoformat()}
tags: [github, git, analysis, {category.lower().replace(' ', '-')}]
repository: {repo_path or "N/A"}
github_repo: {f"{github_owner}/{github_repo}" if github_owner else "N/A"}
---

# {note_name}

Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
Repository: `{repo_path or "N/A"}`
{f"GitHub: [{github_owner}/{github_repo}](https://github.com/{github_owner}/{github_repo})" if github_owner else ""}

---

{content}
"""
                
                # Write file
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(full_content)
                
                return [TextContent(type="text", text=f"✅ Exported to: {file_path}")]
            except Exception as e:
                return [TextContent(type="text", text=f"❌ Export failed: {e}")]
        
        else:
            return [TextContent(type="text", text=f"❌ Unknown tool: {name}")]
            
    except Exception as e:
        logger.error(f"Tool error {name}: {e}")
        return [TextContent(type="text", text=f"❌ Error: {str(e)}")]

async def main():
    """Run the MCP server"""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            ServerInfo(
                name="github-inspector",
                version="1.0.0",
                capabilities=ServerCapabilities(
                    tools=True,
                    text=True
                )
            )
        )

if __name__ == "__main__":
    asyncio.run(main())