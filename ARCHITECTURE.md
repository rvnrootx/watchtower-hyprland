# Watchtower — System Architecture

**Document:** Technical Architecture Specification  
**Project:** Watchtower  
**Platform:** Arch Linux / Arch-based distributions  
**Compositor:** Hyprland  
**Desktop Shell:** Quickshell  
**Status:** Proposed Architecture — v0.1.0

---

# 1. Introduction

Watchtower is a modular, character-driven desktop environment built around Hyprland and Quickshell.

Its architecture separates system configuration, desktop presentation, theme management, automation, and hardware integration.

The objective is to provide a cohesive desktop environment that can dynamically change its visual identity without requiring a complete desktop restart.

## 1.1 Architectural goals

1. Modular subsystem architecture.
2. Centralized theme management.
3. Independent UI and system logic.
4. Reliable installation and recovery.
5. Hardware-aware configuration.
6. Event-driven system integration.
7. Configurable animations and effects.
8. Extensible character themes.
9. Minimal background resource consumption.
10. Independent development and testing of modules.

## 1.2 Non-goals

The initial release will not attempt to:

- Replace the Linux desktop stack.
- Replace Hyprland as a compositor.
- Implement its own display manager.
- Replace PipeWire or NetworkManager.
- Provide a complete distribution.
- Support every Linux distribution.
- Depend on an AI service for ordinary desktop functionality.

---

# 2. High-Level Architecture

Watchtower is organized into four primary layers.

## 2.1 Presentation Layer

Responsible for all visible desktop interfaces.

Technology: Quickshell / QML.

Components:

- Dynamic Island.
- Top bar.
- Control Center.
- Notification Center.
- Character Selector.
- Batcomputer.
- Desktop widgets.
- Application launcher.

## 2.2 Core Services Layer

Responsible for reusable desktop functionality.

Components:

- Theme Engine.
- Wallpaper Engine.
- Event Router.
- Sound Engine.
- System Monitor.
- Scheduler.
- Configuration Manager.

## 2.3 System Integration Layer

Responsible for interacting with Linux services and applications.

Interfaces:

- D-Bus.
- PipeWire.
- MPRIS.
- UPower.
- NetworkManager.
- BlueZ.
- systemd.
- Hyprland IPC.
- Linux hardware interfaces.

## 2.4 Installation and Management Layer

Responsible for deployment and lifecycle management.

Components:

- Installer.
- Dependency Manager.
- GPU Detection.
- Backup Manager.
- Configuration Deployment.
- Diagnostics.
- Uninstaller.
- Update Manager.

---

# 3. Component Architecture

## 3.1 Quickshell

Quickshell is the primary presentation framework.

It provides the desktop interface and communicates with core services.

### Responsibilities

- Render desktop components.
- Manage visual states.
- Respond to user interaction.
- Display system events.
- Manage workspace information.
- React to theme changes.
- Provide keyboard and mouse interaction.

### Design principles

- Reusable QML components.
- Shared color tokens.
- Centralized service objects.
- Minimal duplicated logic.
- Asynchronous operations where necessary.
- No direct execution of arbitrary shell commands from UI components.

The shell must be independently restartable without reinstalling or reconfiguring the environment.

## 3.2 Theme Engine

The Theme Engine is the central visual configuration manager.

Each character theme is declarative and independent.

### Responsibilities

- Load theme definitions.
- Validate configuration.
- Generate color tokens.
- Apply wallpaper configuration.
- Update Quickshell styling.
- Apply compatible Hyprland settings.
- Apply GTK and cursor settings.
- Manage theme-specific sound profiles.
- Support preview and rollback.

### Theme switching lifecycle

1. Receive theme selection.
2. Locate theme definition.
3. Validate configuration and assets.
4. Generate temporary configuration.
5. Prepare changes.
6. Apply supported configuration updates.
7. Notify Quickshell.
8. Persist active theme.
9. Roll back if a critical operation fails.

Theme application must not restart Hyprland.

### Theme isolation

Each character theme must contain its own configuration and assets.

Themes must not directly modify unrelated user configuration.

---

# 4. Theme Configuration Specification

Proposed directory:

```text
themes/
├── batman/
│   ├── theme.yaml
│   ├── wallpaper/
│   ├── sounds/
│   └── assets/
│
├── superman/
├── wonder-woman/
├── flash/
├── nightwing/
└── redhood/
```

### Example theme.yaml

```yaml
schema_version: 1

identity:
  id: nightwing
  name: Nightwing
  description: The Protector

colors:
  background: "#080B12"
  surface: "#111827"
  primary: "#168BFF"
  secondary: "#0752A0"
  accent: "#00B7FF"
  text: "#EAF3FF"

wallpaper:
  desktop: wallpaper/main.jpg
  lockscreen: wallpaper/lock.jpg

appearance:
  icon_theme: Papirus-Dark
  cursor_theme: Bibata-Modern-Ice
  font: Inter

effects:
  blur: true
  animations: smooth
  glow: true

sound:
  enabled: true
  profile: nightwing
```

This schema is illustrative and must be validated against a formal schema before implementation.

Themes should support inheritance in a future version, allowing users to create custom variations without copying every asset.

---

# 5. Dynamic Island Architecture

The Dynamic Island is a dedicated Quickshell module.

It acts as a unified presentation surface for transient desktop events.

## 5.1 Internal components

- Island Window.
- State Manager.
- Event Queue.
- Priority Resolver.
- Animation Controller.
- Media Presentation.
- Notification Presentation.
- Hardware OSD Presentation.

## 5.2 State model

```text
IDLE
 ├── MUSIC
 ├── NOTIFICATION
 ├── VOLUME
 ├── BRIGHTNESS
 ├── DOWNLOAD
 ├── BATTERY
 ├── FOCUS
 └── EXPANDED
```

The state manager must preserve underlying persistent states.

For example, a notification can temporarily replace the music display without destroying the active music session.

## 5.3 Event priority

Events are classified by importance.

| Priority | Event |
|---|---|
| Critical | Critical hardware/system alerts |
| High | Important notifications |
| Normal | Music and media information |
| Low | Volume, brightness, download progress |
| Persistent | Active media and pinned information |

The event resolver decides what should be visible.

Events should have configurable timeouts and dismissal policies.

## 5.4 Positioning

The island will use Wayland layer-shell surfaces.

Requirements:

- Top-center positioning.
- Configurable margins.
- Correct layer ordering.
- No accidental full-width exclusive zone.
- Appropriate behavior with maximized windows.
- Multi-monitor support.
- Configurable animation and size.

The island should be usable with both mouse and keyboard.

---

# 6. Notification Architecture

The notification subsystem will expose the freedesktop notification interface through Quickshell.

### Responsibilities

- Receive desktop notifications.
- Display notification popups.
- Maintain notification history.
- Support dismissal.
- Support urgency levels.
- Provide application icons.
- Respect Do Not Disturb.
- Integrate with Dynamic Island.

Only one notification daemon should own the notification interface.

Watchtower must not start a competing notification daemon by default.

Notification actions and replies should be supported when provided by the originating application and available through the notification interface.

---

# 7. Control Center Architecture

The Control Center is a collection of independent system-control modules.

| Module | Integration |
|---|---|
| Audio | PipeWire |
| Microphone | PipeWire |
| Brightness | brightnessctl |
| Wi-Fi | NetworkManager |
| Bluetooth | BlueZ |
| Battery | UPower |
| Power Profiles | power-profiles-daemon |
| Night Light | hyprsunset |
| Focus | Watchtower notification service |

Each module must:

1. Read actual system state.
2. Display current state.
3. Apply changes through the relevant system interface.
4. Handle permission and service errors.
5. Refresh its displayed state after changes.

Unavailable controls should be disabled with an explanatory message.

---

# 8. Batcomputer Architecture

Batcomputer is the system-monitoring interface.

It collects real hardware and operating-system telemetry.

### Data sources

- CPU: `/proc/stat`, `/proc/cpuinfo`.
- Memory: `/proc/meminfo`.
- GPU: vendor-specific monitoring interfaces.
- Storage: filesystem statistics.
- Network: `/proc/net/dev` or NetworkManager.
- Battery: UPower.
- Processes: `/proc` or process utilities.
- System: `uname`, `os-release`, systemd.

### Display modules

- CPU utilization.
- CPU temperature where available.
- GPU utilization.
- GPU memory.
- GPU temperature.
- RAM and swap.
- Storage utilization.
- Network throughput.
- Battery status.
- System uptime.
- Active processes.

### Performance requirements

- Configurable update intervals.
- No unnecessary high-frequency polling.
- Asynchronous data retrieval.
- Graceful handling of missing sensors.
- No fabricated metrics.

The dashboard must not become a resource-intensive monitoring service.

---

# 9. Sound Engine

The Sound Engine provides optional character-specific UI sounds.

### Responsibilities

- Load character sound profiles.
- Play notification sounds.
- Play optional interaction sounds.
- Manage master volume.
- Support mute.
- Respect Stealth Mode.
- Avoid overlapping sound effects excessively.

All sound assets must be original or appropriately licensed.

---

# 10. Stealth Mode

Stealth Mode is a reversible desktop profile.

### Activation behavior

- Disable decorative sounds.
- Reduce animation activity.
- Disable nonessential blur and visual effects.
- Suppress noncritical notification popups.
- Hide optional widgets.
- Preserve critical system alerts.

### Design requirements

- Save previous desktop state.
- Apply profile overrides.
- Restore previous state on deactivation.
- Survive Quickshell restarts.
- Never disable essential system services.

Stealth Mode is a visual and notification profile, not a security or privacy guarantee.

---

# 11. Scheduler Architecture

The scheduler manages automatic theme changes.

Technology: systemd user timers and services.

### Supported operations

- Scheduled character switching.
- Day/night profiles.
- Manual override.
- Enable/disable.
- Persistent configuration.
- Schedule status.

### Example configuration

```yaml
enabled: true

schedule:
  - time: "06:00"
    theme: superman

  - time: "12:00"
    theme: flash

  - time: "18:00"
    theme: nightwing

  - time: "22:00"
    theme: batman
```

The scheduler must use the user's local timezone.

Manual theme changes should remain active until the next scheduled transition unless permanent manual mode is selected.

---

# 12. Installer Architecture

The installer is independent of Quickshell.

Technology: Bash.

### Responsibilities

- Detect Arch Linux and supported derivatives.
- Detect GPU hardware.
- Verify prerequisites.
- Install packages.
- Back up conflicting configuration.
- Deploy Watchtower configuration.
- Create a dedicated Hyprland session.
- Configure user services.
- Validate installation.
- Support rollback.

### Installation sequence

```text
Preflight
   |
   v
Hardware Detection
   |
   v
Dependency Resolution
   |
   v
Backup
   |
   v
Package Installation
   |
   v
Configuration Deployment
   |
   v
Session Registration
   |
   v
Service Configuration
   |
   v
Validation
   |
   v
Complete
```

### Safety requirements

- Idempotent installation.
- Dry-run support.
- No blind configuration overwrites.
- Explicit error reporting.
- Transaction-like deployment.
- Recoverable configuration changes.
- Package installation through pacman.
- Optional AUR dependencies must be clearly identified.

---

# 13. Session Isolation

Watchtower will provide a dedicated Hyprland session.

It must coexist with existing Hyprland installations.

### Requirements

- Separate session entry.
- Dedicated configuration directory.
- Dedicated Quickshell startup.
- Independent keybindings.
- Independent theme configuration.
- Independent user services where necessary.

Existing user sessions must remain available.

The installer must never replace an existing display manager configuration or the user's default Hyprland session without explicit permission.

---

# 14. Hardware Compatibility

Initial targets:

- Intel integrated graphics.
- AMD integrated and dedicated graphics.
- NVIDIA dedicated graphics.

The installer will detect the GPU and existing driver configuration.

It must not automatically replace working drivers.

### Hardware-dependent components

| Feature | Dependency |
|---|---|
| GPU metrics | Vendor-specific monitoring interface |
| Brightness | Backlight interface |
| Battery | UPower |
| Audio | PipeWire |
| Network | NetworkManager |
| Bluetooth | BlueZ |

Unavailable hardware features should degrade gracefully.

---

# 15. CLI Architecture

The central management interface is `watchtower`.

It provides a consistent interface for shell, theme, automation and system operations.

### Command groups

```text
watchtower
├── theme
│   ├── list
│   ├── current
│   ├── apply
│   └── preview
│
├── wallpaper
│   ├── next
│   └── set
│
├── shell
│   ├── restart
│   └── reload
│
├── island
│   ├── toggle
│   └── music
│
├── stealth
│   ├── enable
│   ├── disable
│   └── status
│
├── schedule
│   ├── enable
│   ├── disable
│   └── status
│
├── sound
│   ├── enable
│   ├── mute
│   └── profile
│
└── system
    ├── status
    ├── doctor
    ├── logs
    └── restore
```

The CLI should be the shared management interface for terminal commands and other desktop components.

Commands that affect the running shell should use a controlled IPC mechanism instead of restarting the entire environment unnecessarily.

---

# 16. Configuration and File Locations

Watchtower must separate source code, user configuration, assets, generated state and logs.

| Directory | Purpose |
|---|---|
| `~/.config/watchtower/` | User configuration |
| `~/.local/share/watchtower/` | Themes and assets |
| `~/.local/bin/` | CLI and helper commands |
| `~/.cache/watchtower/` | Generated and temporary files |
| `~/.local/state/watchtower/` | Logs and runtime state |
| `~/.config/systemd/user/` | User services and timers |

The repository itself should remain independent of the live configuration directory.

User customizations must not be overwritten during updates.

---

# 17. Repository Structure

```text
watchtower/
│
├── install.sh
├── uninstall.sh
├── update.sh
├── watchtower
├── VERSION
├── LICENSE
├── README.md
├── ARCHITECTURE.md
│
├── installer/
│   ├── preflight.sh
│   ├── detect-distro.sh
│   ├── detect-gpu.sh
│   ├── packages.sh
│   ├── backup.sh
│   ├── deploy.sh
│   ├── configure-session.sh
│   └── verify.sh
│
├── core/
│   ├── theme-engine/
│   ├── wallpaper-engine/
│   ├── event-router/
│   ├── sound-engine/
│   ├── scheduler/
│   ├── system-monitor/
│   └── config-manager/
│
├── shell/
│   └── quickshell/
│       ├── shell.qml
│       ├── components/
│       ├── services/
│       ├── config/
│       └── modules/
│           ├── island/
│           ├── bar/
│           ├── notifications/
│           ├── control-center/
│           ├── character-selector/
│           ├── batcomputer/
│           └── widgets/
│
├── themes/
│   ├── batman/
│   ├── superman/
│   ├── wonder-woman/
│   ├── flash/
│   ├── nightwing/
│   └── redhood/
│
├── hyprland/
│   ├── base/
│   ├── keybindings/
│   ├── animations/
│   ├── window-rules/
│   └── session/
│
├── assets/
│   ├── wallpapers/
│   ├── icons/
│   ├── cursors/
│   ├── fonts/
│   └── sounds/
│
├── packaging/
│   ├── packages-arch.txt
│   └── systemd/
│
├── tests/
│   ├── installer/
│   ├── themes/
│   ├── shell/
│   └── integration/
│
└── docs/
    ├── ARCHITECTURE.md
    ├── INSTALLATION.md
    ├── THEMES.md
    ├── DEVELOPMENT.md
    └── TROUBLESHOOTING.md
```

---

# 18. Security and Reliability

Watchtower will operate with the current user's privileges wherever possible.

Requirements:

- No unnecessary root-level background services.
- No arbitrary command execution from theme files.
- Validate external configuration.
- Validate wallpaper and asset paths.
- Avoid unsafe shell interpolation.
- Keep user configuration backups.
- Do not modify unrelated system services.
- Use appropriate permissions for hardware controls.
- Keep diagnostic logs free of sensitive information.

Themes must be declarative data, not executable scripts.

---

# 19. Testing Strategy

Testing must happen at three levels.

### Unit Testing

- Theme configuration validation.
- Color generation.
- Configuration parsing.
- Event priority.
- Scheduler logic.
- CLI argument handling.

### Integration Testing

- Quickshell and Hyprland IPC.
- Media integration.
- Notification integration.
- PipeWire controls.
- Theme application.
- User services.
- GPU detection.

### System Testing

- Fresh installation.
- Existing Hyprland installation.
- NVIDIA, AMD and Intel.
- Multiple displays.
- Quickshell crash recovery.
- Scheduler after reboot.
- Uninstallation and restoration.

---

# 20. Development Milestones

| Milestone | Deliverable |
|---|---|
| M0 | Repository and development foundation |
| M1 | Installer and isolated session |
| M2 | Theme Engine and six identities |
| M3 | Quickshell foundation |
| M4 | Dynamic Island and notifications |
| M5 | Control Center and Batcomputer |
| M6 | Character Selector and advanced systems |
| M7 | Testing and release engineering |

---

# 21. Future Extensibility

The architecture should allow future additions without rewriting the core.

Potential additions:

- Custom user-created characters.
- Community theme repository.
- Animated wallpapers.
- Additional desktop identities.
- AI-assisted Batcomputer.
- Voice-controlled desktop actions.
- Plugin architecture.
- Additional Linux distribution support.

These are future possibilities, not first-release requirements.

---

# 22. Architectural Completion Criteria

The architecture is considered successfully implemented when:

1. Watchtower installs independently of existing Hyprland configurations.
2. Six character identities can be switched reliably.
3. Theme changes propagate across supported components.
4. Quickshell can restart independently.
5. Dynamic Island handles real system events.
6. System controls report and modify actual system state.
7. Batcomputer displays real telemetry.
8. Stealth Mode is reversible.
9. Scheduler works independently of the UI.
10. Installation and uninstallation are recoverable.

---

**End of Architecture Specification**

*Watchtower — The League starts here.*