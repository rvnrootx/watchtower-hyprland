import QtQuick
import Quickshell
import Quickshell.Io

QtObject {
    id: root

    readonly property string stateHome: {
        const xdg = Quickshell.env("XDG_STATE_HOME")
        const home = Quickshell.env("HOME") || ""

        return xdg && xdg.length > 0
            ? xdg
            : home + "/.local/state"
    }

    readonly property string runtimePath:
        stateHome + "/watchtower/active-theme.json"

    property var document: ({})
    property string loadError: ""
    property bool ready: false

    readonly property string activeTheme:
        document.active_theme || "none"

    readonly property var theme:
        document.theme || null

    readonly property var palette:
        theme ? theme.palette : fallbackPalette

    readonly property var typography:
        theme ? theme.typography : fallbackTypography

    readonly property var shape:
        theme ? theme.shape : fallbackShape

    readonly property var effects:
        theme ? theme.effects : fallbackEffects

    readonly property var animation:
        theme ? theme.animation : fallbackAnimation

    readonly property var fallbackPalette: ({
        background: "#080D16",
        foreground: "#EAF2FF",
        surface: "#111C2D",
        surface_alt: "#18283D",
        primary: "#1677FF",
        secondary: "#526D91",
        accent: "#36A3FF",
        border: "#28466A",
        success: "#38C98B",
        warning: "#F5B942",
        danger: "#EF5350"
    })

    readonly property var fallbackTypography: ({
        family: "Inter",
        size: 10,
        weight: 500
    })

    readonly property var fallbackShape: ({
        radius: 14,
        border_width: 1
    })

    readonly property var fallbackEffects: ({
        transparency: 0.88,
        blur: true
    })

    readonly property var fallbackAnimation: ({
        enabled: true,
        duration: 220
    })

    function color(token) {
        return palette[token] || fallbackPalette[token] || "#FF00FF"
    }

    function reloadTheme() {
        if (!themeFile.loaded)
            return

        try {
            const parsed = JSON.parse(themeFile.text())

            if (parsed.schema_version !== 1)
                throw new Error("Unsupported runtime theme schema")

            if (parsed.theme !== null &&
                    (!parsed.theme.palette || !parsed.theme.typography)) {
                throw new Error("Incomplete theme data")
            }

            document = parsed
            loadError = ""
            ready = true

            console.info("[Watchtower] Theme loaded:", activeTheme)
        } catch (error) {
            loadError = String(error)
            console.warn("[Watchtower] Theme load failed:", loadError)
        }
    }

    // QtObject has no default child property.
    // Declare FileView as an explicit object property.
    property FileView themeFile: FileView {
        path: root.runtimePath
        watchChanges: true
        preload: true
        printErrors: false

        onLoaded: root.reloadTheme()
        onFileChanged: reload()

        onLoadFailed: function(error) {
            root.loadError = "Unable to read active theme JSON"
            root.ready = false

            console.warn(
                "[Watchtower] Theme file unavailable:",
                root.runtimePath,
                error
            )
        }
    }

    Component.onCompleted: {
        console.info(
            "[Watchtower] Theme service initialized:",
            runtimePath
        )
    }
}
