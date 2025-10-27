# Linear Integration Guide

## Overview

Connect your SaaS project to Linear for project management, issue tracking, and roadmap planning.

---

## Setup

### 1. Get Linear API Key

1. Go to Linear → Settings → Account → API
2. Click "Create new API key"
3. Give it a name (e.g., "Claude Code Integration")
4. Copy the API key (format: `lin_api_XXXXXXXXXXXXXXXXXXXXXXXX`)

### 2. Get Workspace and Team IDs

**Via Linear UI:**
1. Open Linear in browser
2. Go to Settings → General
3. Note your workspace URL (e.g., `https://linear.app/verdaio`)
4. Click on your team → Team Settings
5. Copy team ID from URL (e.g., `VER` or the UUID)

**Via API (alternative):**
```bash
# Get workspace info
curl -X POST https://api.linear.app/graphql \
  -H "Authorization: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "{ viewer { id name organization { id name } } }"}'

# Get teams
curl -X POST https://api.linear.app/graphql \
  -H "Authorization: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "{ teams { nodes { id name key } } }"}'
```

### 3. Configure Project

Edit `.config/linear-config.json` in your project:

```json
{
  "apiKey": "lin_api_XXXXXXXXXXXXXXXXXXXXXXXX",
  "enabled": true,
  "projectId": "saas202509",
  "workspaceId": "YOUR_WORKSPACE_ID",
  "teamId": "YOUR_TEAM_ID",
  "linearProjectId": null,
  "syncSettings": {
    "syncSprints": true,
    "syncRoadmaps": false,
    "syncPRDs": false,
    "autoCreateIssues": false
  }
}
```

### 4. Map Project to Linear Team

Each SaaS project can map to a Linear team:

| Project | Linear Team | Team ID |
|---------|-------------|---------|
| saas202501 | Your choice | See teams list |
| saas202502 | Your choice | See teams list |
| saas202503 | Your choice | See teams list |

---

## Usage

### Get Available Teams

Ask Claude: "What Linear teams do I have?"

Claude will call the API and show your teams with IDs.

### Create Linear Project

Ask Claude: "Create a Linear project for this SaaS"

Claude will:
1. Read your config
2. Create project in Linear via API
3. Store project ID in config
4. Link the project to your team

### Sync Sprint Plans to Linear

Ask Claude: "Sync my sprint plan to Linear"

Claude will:
1. Read your current sprint plan
2. Parse user stories and tasks
3. Create issues in Linear via GraphQL API
4. Create project milestone for the sprint
5. Link issues to milestone

### Manual API Testing

Linear uses GraphQL API (not REST):

```bash
# Create a project
curl -X POST https://api.linear.app/graphql \
  -H "Authorization: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "mutation { projectCreate(input: { name: \"Project Name\", teamIds: [\"TEAM_ID\"] }) { project { id name url } } }"
  }'

# Create an issue
curl -X POST https://api.linear.app/graphql \
  -H "Authorization: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "mutation { issueCreate(input: { title: \"Task name\", description: \"Description\", teamId: \"TEAM_ID\", projectId: \"PROJECT_ID\" }) { issue { id identifier url } } }"
  }'

# Query projects
curl -X POST https://api.linear.app/graphql \
  -H "Authorization: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "{ projects { nodes { id name url state } } }"
  }'
```

---

## Features

### Sync Sprint Plans

When `syncSprints: true`:
- Claude can push sprint plans to Linear
- Creates project milestone for each sprint
- Converts user stories to issues
- Links issues to sprint milestone
- Maintains status sync (Todo/In Progress/Done)

### Sync Roadmaps (Optional)

When `syncRoadmaps: true`:
- Now/Next/Later sections become project phases
- Features become issues with target dates
- Roadmap items link to Linear roadmap view

### Sync PRDs (Optional)

When `syncPRDs: true`:
- PRD features become Linear issues
- Acceptance criteria become issue descriptions
- Links back to PRD file

---

## Linear vs ClickUp

**Use Linear when:**
- You want product roadmap visualization
- Your team prefers keyboard-first workflows
- You need tight GitHub integration
- You want cycle-based planning

**Use ClickUp when:**
- You need more flexible custom fields
- You want time tracking built-in
- You prefer visual task management
- You need Gantt charts and dependencies

**Use both when:**
- Linear for product/engineering work
- ClickUp for operations/business tasks

---

## API Reference

**Base URL:** `https://api.linear.app/graphql`

**Authentication:** Header: `Authorization: YOUR_API_KEY`

**API Type:** GraphQL (not REST)

**Common Queries:**

```graphql
# Get viewer info
query {
  viewer {
    id
    name
    email
  }
}

# Get teams
query {
  teams {
    nodes {
      id
      name
      key
    }
  }
}

# Get projects
query {
  projects {
    nodes {
      id
      name
      url
      state
    }
  }
}

# Get issues in project
query {
  project(id: "PROJECT_ID") {
    issues {
      nodes {
        id
        identifier
        title
        state {
          name
        }
      }
    }
  }
}
```

**Common Mutations:**

```graphql
# Create project
mutation {
  projectCreate(input: {
    name: "Project Name"
    description: "Description"
    teamIds: ["TEAM_ID"]
    state: "planned"
  }) {
    project {
      id
      name
      url
    }
  }
}

# Create issue
mutation {
  issueCreate(input: {
    title: "Issue title"
    description: "Issue description"
    teamId: "TEAM_ID"
    projectId: "PROJECT_ID"
    priority: 1
  }) {
    issue {
      id
      identifier
      url
    }
  }
}

# Update issue status
mutation {
  issueUpdate(
    id: "ISSUE_ID"
    input: {
      stateId: "STATE_ID"
    }
  ) {
    issue {
      id
      state {
        name
      }
    }
  }
}
```

**Docs:** https://developers.linear.app/docs/graphql/working-with-the-graphql-api

---

## Security

- **Never commit** `.config/linear-config.json` with your API key to public repos
- Add to `.gitignore`: `.config/linear-config.json`
- Use environment variables for production: `LINEAR_API_KEY`
- API keys have full account access - treat them like passwords

---

## Troubleshooting

**Issue:** API returns "Unauthorized"
- Check API key is valid (starts with `lin_api_`)
- Regenerate key if needed from Linear settings

**Issue:** Can't find team
- Run teams query (see API Reference above)
- Use the team's `id` field, not the `key`

**Issue:** Project creation fails
- Verify team ID exists
- Check you have permission to create projects
- Ensure workspace has available project slots

**Issue:** Issues not syncing
- Check `syncSettings.syncSprints` is `true`
- Verify sprint plan format matches template
- Ensure Linear project ID is set in config

---

## Example Workflow

### Initial Setup

1. **Get credentials:**
   - Generate API key in Linear
   - Find workspace and team IDs
   - Configure `.config/linear-config.json`

2. **Create Linear project:**
   - Ask Claude: "Create Linear project for this SaaS"
   - Claude creates project and stores ID

### Sprint Planning

3. **Create sprint plan:**
   - Ask Claude: "Create sprint 1 plan"
   - Claude creates `sprints/current/sprint-01-[name].md`

4. **Sync to Linear:**
   - Ask Claude: "Sync sprint 1 to Linear"
   - Claude creates milestone "Sprint 1"
   - Creates issues for each user story
   - Links issues to milestone

### Track Progress

5. **Check status:**
   - Update issues in Linear (change status, add comments)
   - Ask Claude: "What's the status of sprint 1?"
   - Claude queries Linear API for current state

6. **Roadmap planning:**
   - Create roadmap in `product/roadmap/`
   - Ask Claude: "Sync roadmap to Linear"
   - Features appear in Linear projects view

---

## Integration with ClickUp

**Both tools can coexist:**

```json
// linear-config.json
{
  "enabled": true,
  "syncSprints": true
}

// clickup-config.json
{
  "enabled": true,
  "syncSprints": false
}
```

**Suggested division:**
- **Linear:** Product features, engineering tasks, sprints
- **ClickUp:** Operations, marketing, business tasks

---

## Next Steps

- Set up Linear cycles for sprint planning
- Create issue templates for common task types
- Configure Linear automations for status transitions
- Set up Linear's GitHub integration
- Use Linear's roadmap view for planning

---

**Linear API Version:** v1 (GraphQL)
**Guide Version:** 1.0
**Last Updated:** 2025-10-24
