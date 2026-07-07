# Scripts - Start and Stop

Platform-specific scripts to start and stop the Kanban Studio Docker container.

## Files

- `start.sh` / `stop.sh` - Mac / Linux (bash)
- `start.bat` / `stop.bat` - Windows (batch)

## Usage

Run from the project root or from the scripts directory:

```bash
./scripts/start.sh      # Mac/Linux
scripts\start.bat       # Windows
```

Starts the full stack (frontend + backend) in a Docker container at http://localhost:8000.