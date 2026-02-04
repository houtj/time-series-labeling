# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.8] - 2026-02-04

### Changed
- Template editor: moved 8-channel limit validation from "Add Channel" button to "Save" button, allowing users to upload test files with more columns and select which channels to keep

## [2.0.7] - 2026-02-04

### Changed
- Simplified large dataset optimization architecture: backend now handles all resampling (5k points per channel with union), frontend only renders


## [2.0.3] - 2025-12-16

### Added
- Edit file description button in labeling toolbar navigation section
- Reusable description dialog component for editing file descriptions
- File description can now be edited directly from the labeling page

## [2.0.2] - 2025-11-03

### Added
- On-the-fly event class creation in labeling dialog with automatic color generation
- Keyboard shortcuts: `E` for label mode, `G` for guideline mode
- Plotly toolbar with zoom, pan, and download controls

### Fixed
- Events and guidelines panels now properly scroll when content overflows
- File description update API endpoint mismatch
- Event description dialog state synchronization
- Project descriptions dialog scrolling behavior
- Auto-detected events now display immediately without page refresh
- Auto-detection process can now be properly cancelled
- File navigation preserves all component states correctly
- Conversation history persistence for chat and auto-detection

### Changed
- Removed manual "Save Labels" button (auto-save handles all changes)
- Docker commands updated to use `docker compose` instead of `docker-compose`


