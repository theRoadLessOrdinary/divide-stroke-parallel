# Divide Stroke into Parallel Paths

An Inkscape extension that replaces a stroked path with several thinner parallel paths that together cover the same band.

Menu: **Extensions > Map's Edge Tools > General > Paths > Divide Stroke into Parallel Paths** (extension ID `maps_edge.divide_stroke_parallel`). It is also a button on the [Map's Edge Tool Panel](https://github.com/theRoadLessOrdinary/maps-edge-panel).

## Using it

1. Select one or more stroked paths.
2. Run **Divide Stroke into Parallel Paths** and set **Number of parallel paths** (2 to 100).

Example: a path with a 24 wide stroke, divided into 2, becomes two paths, each with a 12 wide stroke, running 6 to either side of the original line.

- The new paths keep the original's style, apart from the stroke width.
- They are numbered left to right as seen travelling along the original path.
- Where the original bends tighter than a new path's distance from it, that path cannot stay parallel and comes to a point there. A message says so when this happens.

## Requirements

- Inkscape 1.x (developed and used on Inkscape 1.4.4, Flatpak, on Linux; other platforms have not been tried)
- Python 3 with `numpy` available to Inkscape's Python

## Install

Copy the files in this repository into a folder of their own inside Inkscape's user extensions directory, then restart Inkscape. To find that directory, open **Edit > Preferences > System** and look at **User extensions**. Typical locations:

| Install type | User extensions folder |
|---|---|
| Linux (native) | `~/.config/inkscape/extensions/` |
| Linux (Flatpak) | `~/.var/app/org.inkscape.Inkscape/config/inkscape/extensions/` |
| macOS | `~/Library/Application Support/org.inkscape.Inkscape/config/inkscape/extensions/` |
| Windows | `%APPDATA%\inkscape\extensions\` |

For example, on native Linux:

```bash
git clone https://github.com/theRoadLessOrdinary/divide-stroke-parallel.git \
    ~/.config/inkscape/extensions/divide-stroke-parallel
```

To uninstall, delete the folder and restart Inkscape.
