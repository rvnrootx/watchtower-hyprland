# Watchtower

### A character-driven Hyprland desktop environment.

**Watchtower** is an independent, modular, and highly customizable desktop environment built around [Hyprland](https://hypr.land/) and [Quickshell](https://quickshell.org/), inspired by the Justice League universe.

Transform your Linux desktop into a fully interactive experience with character-based themes, a macOS/Android-inspired Dynamic Island, system monitoring, intelligent notifications, and extensive desktop automation.

> *One desktop. Six identities. Infinite possibilities.*

---

## Overview

Watchtower brings together the flexibility of Hyprland, the power of Quickshell, and a centralized theme engine to create a cohesive desktop experience.

Rather than simply changing wallpapers, Watchtower transforms the entire desktop according to the selected character identity.

### Character identities

| Character | Theme | Visual identity |
|---|---|---|
| Batman | Dark Knight | Black / Gold |
| Superman | Man of Steel | Blue / Red |
| Wonder Woman | Warrior | Crimson / Gold |
| The Flash | Speed Force | Red / Yellow |
| Nightwing | The Protector | Black / Electric Blue |
| Red Hood | The Outlaw | Black / Blood Red |

Each identity can define its own wallpapers, colors, icons, cursors, sounds, animations, and interface styling.

## Features

### Dynamic Island
An interactive top-center interface inspired by macOS Dynamic Island and Android notification islands.

- Music playback and media controls.
- Real-time notification previews.
- Volume and brightness indicators.
- Battery and charging information.
- Download progress.
- Expandable system controls.
- Configurable animations and interaction states.

### Character Theme Engine
A centralized theme management system.

- Six initial character identities.
- Dynamic color generation.
- Wallpaper and lock-screen management.
- GTK and Qt styling.
- Icon and cursor themes.
- Character-specific animations.
- Sound profiles.
- Live theme switching.

### Quickshell Desktop
A modular desktop interface built with QML.

- Custom top bar.
- Workspace integration.
- Application launcher.
- Notification center.
- Control center.
- Desktop widgets.
- Multi-monitor support.

### Batcomputer
A system monitoring dashboard inspired by Batman's computer.

- CPU and GPU monitoring.
- RAM and swap usage.
- Storage statistics.
- Network throughput.
- Battery information.
- Running processes.
- Hardware information.

### Advanced Features
- Character selector.
- Sound identity system.
- Stealth Mode.
- Automatic theme scheduler.
- Wallpaper automation.
- System diagnostics.
- Centralized command interface.

## Technology Stack

| Component | Technology |
|---|---|
| Window Manager | Hyprland |
| Desktop Shell | Quickshell |
| UI | QML / JavaScript |
| Installer | Bash |
| Theme Configuration | YAML |
| Runtime Configuration | JSON |
| Color Generation | Matugen |
| Wallpaper Backend | swww |
| Audio | PipeWire |
| System Integration | D-Bus |
| Scheduling | systemd user timers |
| Lock Screen | hyprlock |
| Idle Management | hypridle |

## Architecture

Watchtower follows a modular architecture consisting of:

- **Core:** Theme management, automation, system services, and configuration management.
- **Shell:** Quickshell-based user interface.
- **Themes:** Character-specific visual configurations.
- **Hyprland:** Window management, animations, keybindings, and session integration.
- **Installer:** Dependency detection, installation, backups, and deployment.

See [ARCHITECTURE.md](docs/ARCHITECTURE.md) for the detailed technical specification.

## Installation

> **Development status:** Watchtower is currently in the planning and initial development stage. Installation instructions will be published when the first working release is available.

Planned installation:

```bash
git clone https://github.com/rvnrootx/watchtower-hyprland.git
cd watchtower-hyprland

chmod +x install.sh
./install.sh
```

## Command Interface

The planned `watchtower` command interface will provide centralized desktop management.

```bash
# Theme management
watchtower theme list
watchtower theme apply nightwing

# Wallpaper management
watchtower wallpaper next

# Shell management
watchtower shell restart

# Dynamic Island
watchtower island toggle

# Stealth Mode
watchtower stealth enable

# Scheduler
watchtower schedule status

# System diagnostics
watchtower status
watchtower doctor
```

## System Requirements

Initial development targets Arch Linux and Arch-based distributions.

- Arch Linux / EndeavourOS / CachyOS.
- Hyprland-compatible Wayland environment.
- Quickshell.
- PipeWire.
- systemd user session.
- Intel, AMD, or NVIDIA graphics.

The project aims to support NVIDIA, AMD, and Intel GPUs, subject to hardware and driver compatibility testing.

## Roadmap

- [ ] Project foundation and repository architecture.
- [ ] Installer and configuration backup system.
- [ ] Dedicated Hyprland session.
- [ ] Centralized theme engine.
- [ ] Six character identities.
- [ ] Quickshell desktop interface.
- [ ] Dynamic Island.
- [ ] Notification center.
- [ ] Control center.
- [ ] Character selector.
- [ ] Batcomputer dashboard.
- [ ] Sound engine.
- [ ] Stealth Mode.
- [ ] Theme scheduler.
- [ ] Performance optimization and release.

## Project Philosophy

Watchtower is designed around a few principles:

- Modularity over monolithic configuration.
- Automation without sacrificing user control.
- Visual identity without compromising performance.
- Hardware compatibility.
- Reversible system changes.
- Consistent and centralized configuration.
- Open-source development.

## Contributing

Contributions, ideas, bug reports, and suggestions will be welcome as development progresses.

## License

To be determined before the first public release.

---

**Watchtower — The League starts here.**