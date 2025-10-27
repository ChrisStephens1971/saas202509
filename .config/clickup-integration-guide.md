# ClickUp Integration Guide

## Overview

Connect your SaaS project to ClickUp for task management and sprint tracking.

---

## Setup

### 1. Get ClickUp API Key

1. Go to ClickUp → Settings → Apps
2. Generate API Token
3. Copy the token (format: `pk_XXXXXXX_YYYYYYYY`)

### 2. Configure Project

Edit `.config/clickup-config.json`:

```json
{
  "apiKey": "YOUR_API_KEY_HERE",
  "enabled": true,
  "projectId": "saas202504",
  "teamId": "9017328947",           // Your ClickUp workspace ID
  "teamName": "Verdaio",            // Your workspace name
  "spaceId": null,                  // Optional: specific space
  "syncSettings": {
    "syncSprints": true,            // Sync sprint plans to ClickUp
    "syncPRDs": false,              // Sync PRDs as tasks
    "syncRoadmaps": false,          // Sync roadmap items
    "autoCreateTasks": false        // Auto-create tasks from docs
  }
}
```

### 3. Map Project to ClickUp Workspace

Each SaaS project can map to a ClickUp workspace (team):

| Project | ClickUp Workspace | Team ID |
|---------|-------------------|---------|
| saas202501 | Your choice | See availableTeams |
| saas202502 | Your choice | See availableTeams |
| saas202503 | Your choice | See availableTeams |
| saas202504 | Your choice | See availableTeams |

---

## Usage

### Get Available Workspaces

Ask Claude: "What ClickUp workspaces do I have?"

Claude will call the API and show your workspaces with IDs.

### Map This Project to a Workspace

Ask Claude: "Map this project to the [WorkspaceName] ClickUp workspace"

Claude will:
1. Read your config
2. Update `teamId` and `teamName`
3. Confirm the mapping

### Create Tasks from Sprint Plan

Ask Claude: "Sync my sprint plan to ClickUp"

Claude will:
1. Read your current sprint plan
2. Parse tasks and user stories
3. Create tasks in ClickUp via API
4. Link back to the sprint plan

### Manual API Testing

```bash
# Get your teams (workspaces)
curl -H "Authorization: YOUR_API_KEY" \
  https://api.clickup.com/api/v2/team

# Get spaces in a team
curl -H "Authorization: YOUR_API_KEY" \
  https://api.clickup.com/api/v2/team/TEAM_ID/space

# Create a task
curl -X POST \
  -H "Authorization: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"name": "Task name", "description": "Task description"}' \
  https://api.clickup.com/api/v2/list/LIST_ID/task
```

---

## Features

### Sync Sprint Plans

When `syncSprints: true`:
- Claude can push sprint plans to ClickUp
- Creates folders for each sprint
- Converts user stories to tasks
- Maintains status sync

### Sync PRDs (Optional)

When `syncPRDs: true`:
- PRD features become ClickUp tasks
- Acceptance criteria become checklists
- Links to the PRD file

### Sync Roadmaps (Optional)

When `syncRoadmaps: true`:
- Now/Next/Later sections become ClickUp lists
- Features become tasks with timelines

---

## API Reference

**Base URL:** `https://api.clickup.com/api/v2`

**Authentication:** Header: `Authorization: YOUR_API_KEY`

**Common Endpoints:**
- `GET /team` - List workspaces
- `GET /team/{team_id}/space` - List spaces
- `GET /space/{space_id}/folder` - List folders
- `GET /folder/{folder_id}/list` - List task lists
- `POST /list/{list_id}/task` - Create task
- `GET /task/{task_id}` - Get task
- `PUT /task/{task_id}` - Update task

**Docs:** https://clickup.com/api

---

## Security

- **Never commit** `.config/clickup-config.json` with your API key to public repos
- Add to `.gitignore`: `.config/clickup-config.json`
- Use environment variables for production: `CLICKUP_API_KEY`

---

## Troubleshooting

**Issue:** API returns 401 Unauthorized
- Check API key is valid
- Regenerate token if needed

**Issue:** Can't find workspace
- Run: `curl -H "Authorization: KEY" https://api.clickup.com/api/v2/team`
- Copy the correct `team_id`

**Issue:** Tasks not syncing
- Check `syncSettings.syncSprints` is `true`
- Verify sprint plan format matches template
- Check ClickUp workspace is accessible

---

## Example Workflow

1. **Initial setup:**
   - Get API key
   - Configure `.config/clickup-config.json`
   - Map project to workspace

2. **Create sprint plan:**
   - Ask Claude: "Create sprint 1 plan"
   - Claude creates `sprints/current/sprint-01-[name].md`

3. **Sync to ClickUp:**
   - Ask Claude: "Sync sprint 1 to ClickUp"
   - Claude creates folder "Sprint 1" in ClickUp
   - Creates tasks for each user story
   - Links tasks back to sprint plan

4. **Track progress:**
   - Update tasks in ClickUp
   - Ask Claude: "What's the status of sprint 1?"
   - Claude reads from ClickUp API

---

## Next Steps

- Set up ClickUp Custom Fields for better tracking
- Create ClickUp templates for recurring tasks
- Use ClickUp automations with Claude-created tasks
- Integrate with Time Tracking
