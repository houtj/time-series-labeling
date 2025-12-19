# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.4] - 2025-12-19

### Added
- Window features computation endpoint (`POST /window-indicator/features`)
- Real-time frequency, energy, and morphology feature display in label selection dialog
- Automatic feature calculation after second click in label mode
- Self-contained feature computation (frequency bands, energy metrics, waveform morphology)
- Loading state and error handling for feature computation

### Technical
- New backend route: `hill_backend/routes/window_indicator.py` with independent feature computation
- New frontend service: `WindowFeaturesService` for fetching computed features
- Enhanced label selection dialog with expandable features section
- Type-safe window index handling for Plotly click events

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


