from mcp.server.fastmcp import FastMCP
import os
from typing import Optional

mcp = FastMCP("todo-server")
todos = []
# Track Notion page IDs for each task
task_to_notion_id = {}

# Notion configuration (you'll need to set these)
NOTION_TOKEN = os.getenv("NOTION_TOKEN", "")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID", "")

@mcp.tool()
def add_task(task: str):
    """Add a new task"""
    todos.append(task)
    return {"message": f"Task added: {task}"}

@mcp.tool()
def list_tasks():
    """List all tasks"""
    return {"todos": todos}

@mcp.tool()
def remove_task(task: str):
    """Remove a task from local list and Notion"""
    if task in todos:
        todos.remove(task)
        
        # Also remove from Notion if we have the page ID
        if task in task_to_notion_id and NOTION_TOKEN and NOTION_DATABASE_ID:
            try:
                from notion_client import Client
                notion = Client(auth=NOTION_TOKEN)
                notion.pages.update(task_to_notion_id[task], archived=True)
                del task_to_notion_id[task]
                return {"message": f"Task removed: {task} (also deleted from Notion)"}
            except Exception as e:
                return {"message": f"Task removed locally: {task} (Notion deletion failed: {str(e)})"}
        
        return {"message": f"Task removed: {task}"}
    return {"message": "Task not found"}

@mcp.tool()
def sync_to_notion():
    """Sync all current tasks to Notion database"""
    if not NOTION_TOKEN or not NOTION_DATABASE_ID:
        return {"message": "Notion not configured. Set NOTION_TOKEN and NOTION_DATABASE_ID environment variables."}
    
    try:
        from notion_client import Client
        
        notion = Client(auth=NOTION_TOKEN)
        
        # Clear existing mapping
        task_to_notion_id.clear()
        
        # Add each task to Notion
        for task in todos:
            response = notion.pages.create(
                parent={"database_id": NOTION_DATABASE_ID},
                properties={
                    "Name": {
                        "title": [
                            {
                                "text": {
                                    "content": task
                                }
                            }
                        ]
                    }
                }
            )
            # Store the Notion page ID for this task
            task_to_notion_id[task] = response["id"]
        
        return {"message": f"Successfully synced {len(todos)} tasks to Notion"}
        
    except ImportError:
        return {"message": "Notion client not installed. Run: pip install notion-client"}
    except Exception as e:
        return {"message": f"Error syncing to Notion: {str(e)}"}

@mcp.tool()
def setup_notion(token: str, database_id: str):
    """Setup Notion integration with your token and database ID"""
    global NOTION_TOKEN, NOTION_DATABASE_ID
    NOTION_TOKEN = token
    NOTION_DATABASE_ID = database_id
    return {"message": "Notion integration configured successfully"}

if __name__ == "__main__":
    mcp.run()
