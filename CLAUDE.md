# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a video management system with a Vue.js frontend and Flask backend. It allows users to scan local directories for video files, manage video metadata (tags, descriptions, thumbnails), and play videos through a web interface.

## Development Commands

### Backend (Python Flask)
- **Start development server**: `start_server.bat` (Windows batch file that sets up venv and runs Flask)
- **Manual setup**: 
  - `cd backend`
  - `python -m venv venv` (if venv doesn't exist)
  - `venv\Scripts\activate` (Windows)
  - `pip install -r requirements.txt`
  - `python app.py`
- **Backend runs on**: `http://127.0.0.1:5000`

### Frontend (Vue.js + Vite)
- **Development server**: `npm run dev` (in frontend directory)
- **Build**: `npm run build` 
- **Preview build**: `npm run preview`
- **Install dependencies**: `npm install`

## Architecture

### Backend Structure
- **Main application**: `backend/app.py` - Single Flask file containing all API routes
- **Data storage**: JSON files (`data.json` for video metadata, `last_path.json` for UI state)
- **FFmpeg integration**: Uses local FFmpeg binaries (`ffmpeg.exe`, `ffprobe.exe`, `ffplay.exe`) for thumbnail generation and video duration extraction
- **Static files**: Serves video files and thumbnails from local filesystem

### API Endpoints
- `GET /api/videos` - Get all videos
- `PUT /api/videos/<index>` - Update video metadata
- `DELETE /api/videos/<index>` - Delete single video
- `POST /api/videos/delete_batch` - Delete multiple videos
- `POST /api/videos/reorder` - Reorder videos (drag & drop)
- `POST /api/scan` - Scan directory for videos
- `GET/POST /api/last_path` - Remember last scanned path
- `GET /api/stream_video` - Stream video file
- `GET /api/thumbnail` - Get thumbnail image
- `POST /api/upload_thumbnail/<index>` - Upload custom thumbnail

### Frontend Structure
- **Framework**: Vue 3 with Composition API
- **Router**: Vue Router with hash-based routing
- **Build tool**: Vite
- **Main components**:
  - `App.vue` - Root component with navigation
  - `Manage.vue` - Video management interface with drag-and-drop reordering
  - `List.vue` - Video browsing with search, pagination, sorting
  - `Player.vue` - Video playback interface

### Key Features
- **Video scanning**: Recursively scans directories for video files (.mp4, .mkv, .avi, .mov)
- **Thumbnail generation**: Automatically generates thumbnails using FFmpeg
- **Drag & drop reordering**: Uses vuedraggable for manual video ordering
- **Search and filtering**: Text search and sort by filename or add time
- **Batch operations**: Multiple video selection and deletion
- **Local video streaming**: Direct file serving through Flask

## File Storage
- Video metadata stored in `backend/data.json`
- Thumbnails generated alongside video files or in `backend/static/thumbnails/`
- Supports both auto-generated and user-uploaded thumbnails

## Important Notes
- Backend contains embedded FFmpeg binaries for Windows
- Uses Chinese language interface
- All video paths are stored as absolute file system paths
- Thumbnails are generated at 50-second mark of videos
- API base URL is hardcoded to `http://127.0.0.1:5000` in frontend