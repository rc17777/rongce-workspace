---
name: drawio
description: "Always use when user asks to create, generate, draw, or design a diagram, flowchart, architecture diagram, ER diagram, sequence diagram, class diagram, network diagram, mockup, wireframe, or UI sketch, or mentions draw.io, drawio, .drawio files, or diagram export to PNG/SVG/PDF."
---

# draw.io Diagram Generator

Generate draw.io diagrams as native .drawio files. Optionally export to PNG, SVG, or PDF with the diagram XML embedded (so the exported file remains editable in draw.io).

## Workflow

1. Generate draw.io XML in mxGraphModel format for the requested diagram
2. Write the XML to a .drawio file in the current working directory using the Write tool
3. If the user requested an export format (png, svg, pdf), locate the draw.io CLI (see below), export with --embed-diagram, then delete the source .drawio file. If the CLI is not found, keep the .drawio file and tell the user they can install the draw.io desktop app to enable export, or open the .drawio file directly
4. Open the result — the exported file if exported, or the .drawio file otherwise. If the open command fails, print the file path so the user can open it manually

## Format Detection

Check the user's request for a format preference. Examples:
- "create a flowchart" → flowchart.drawio
- "png flowchart for login" → login-flow.drawio.png
- "svg ER diagram" → er-diagram.drawio.svg
- "pdf architecture overview" → architecture-overview.drawio.pdf

If no format is mentioned, just write the .drawio file and open it in draw.io.

| Format | Embed XML | Notes |
|--------|-----------|-------|
| png | Yes (-e) | Viewable everywhere, editable in draw.io |
| svg | Yes (-e) | Scalable, editable in draw.io |
| pdf | Yes (-e) | Printable, editable in draw.io |
| jpg | No | Lossy, no embedded XML support |

## draw.io CLI Location

The draw.io desktop app includes a command-line interface for exporting.

First, detect the environment, then locate the CLI accordingly:

**Windows:**
```
"C:\Program Files\draw.io\draw.io.exe"
```

Use `where drawio` to check if it's on PATH before falling back to the platform-specific path.

## Export Command

```
drawio -x -f <format> -e -b 10 -o <output> <input.drawio>
```

Key flags:
- `-x` / `--export`: export mode
- `-f` / `--format`: output format (png, svg, pdf, jpg)
- `-e` / `--embed-diagram`: embed diagram XML in the output (PNG, SVG, PDF only)
- `-o` / `--output`: output file path
- `-b` / `--border`: border width around diagram (default: 0)
- `-t` / `--transparent`: transparent background (PNG only)
- `-s` / `--scale`: scale the diagram size
- `--width` / `--height`: fit into specified dimensions (preserves aspect ratio)
- `-a` / `--all-pages`: export all pages (PDF only)
- `-p` / `--page-index`: select a specific page (1-based)

## Open Command (Windows)

```
start <file>
```

## File Naming

- Use a descriptive filename based on the diagram content (e.g., login-flow, database-schema)
- Use lowercase with hyphens for multi-word names
- For export, use double extensions: name.drawio.png, name.drawio.svg, name.drawio.pdf
- After a successful export, delete the intermediate .drawio file — the exported file contains the full diagram

## XML Structure

Every diagram must have this structure:

```xml
<mxGraphModel adaptiveColors="auto">
  <root>
    <mxCell id="0"/>
    <mxCell id="1" parent="0"/>
    <!-- Diagram cells go here with parent="1" -->
  </root>
</mxGraphModel>
```

- Cell `id="0"` is the root layer
- Cell `id="1"` is the default parent layer
- All diagram elements use `parent="1"` unless using multiple layers

## Basic Shapes

**Rounded rectangle:**
```xml
<mxCell id="2" value="Label" style="rounded=1;whiteSpace=wrap;html=1;" vertex="1" parent="1">
  <mxGeometry x="100" y="100" width="120" height="60" as="geometry"/>
</mxCell>
```

**Diamond (decision):**
```xml
<mxCell id="3" value="Condition?" style="rhombus;whiteSpace=wrap;html=1;" vertex="1" parent="1">
  <mxGeometry x="100" y="200" width="120" height="80" as="geometry"/>
</mxCell>
```

**Arrow (edge):**
```xml
<mxCell id="4" value="" style="edgeStyle=orthogonalEdgeStyle;html=1;" edge="1" source="2" target="3" parent="1">
  <mxGeometry relative="1" as="geometry"/>
</mxCell>
```

**Labeled arrow:**
```xml
<mxCell id="5" value="Yes" style="edgeStyle=orthogonalEdgeStyle;html=1;" edge="1" source="3" target="6" parent="1">
  <mxGeometry relative="1" as="geometry"/>
</mxCell>
```

## Common Style Properties

| Property | Values | Use for |
|----------|--------|---------|
| rounded=1 | 0 or 1 | Rounded corners |
| whiteSpace=wrap | wrap | Text wrapping |
| fillColor=#dae8fc | Hex color | Background color |
| strokeColor=#6c8ebf | Hex color | Border color |
| fontColor=#333333 | Hex color | Text color |
| shape=cylinder3 | shape name | Database cylinders |
| shape=mxgraph.flowchart.document | shape name | Document shapes |
| ellipse | style keyword | Circles/ovals |
| rhombus | style keyword | Diamonds |
| edgeStyle=orthogonalEdgeStyle | style keyword | Right-angle connectors |
| edgeStyle=elbowEdgeStyle | style keyword | Elbow connectors |
| dashed=1 | 0 or 1 | Dashed lines |
| swimlane | style keyword | Swimlane containers |
| group | style keyword | Invisible container |
| container=1 | 0 or 1 | Enable container behavior |
| pointerEvents=0 | 0 or 1 | Prevent container from capturing connections |
| html=1 | 0 or 1 | Enable HTML rendering in labels |

## HTML in Labels

Always include `html=1` in the style when the value attribute contains any HTML tags (`<b>`, `<br>`, `<font>`, etc.).

HTML in attribute values must be XML-escaped:
- `<` → `&lt;`
- `>` → `&gt;`
- `&` → `&amp;`
- `"` → `&quot;`

**Line breaks:** Use `\n` (works with both html=1 and html=0) or `<br>` (requires html=1).

**Bold/italic:** Use `fontStyle=1` (bold), `fontStyle=2` (italic), `fontStyle=4` (underline). Values combine via bitwise OR. Use HTML tags only when formatting part of the label.

## Edge Rules

**CRITICAL:** Every edge mxCell must contain a `<mxGeometry relative="1" as="geometry" />` child element. Self-closing edge cells are invalid.

```xml
<mxCell id="e1" edge="1" parent="1" source="a" target="b" style="edgeStyle=orthogonalEdgeStyle;rounded=1;html=1;">
  <mxGeometry relative="1" as="geometry" />
</mxCell>
```

Edge routing is automatic (ELK handles it). Do NOT add waypoints or exitX/exitY overrides.

### Edge Styles

| Style | Syntax | Best for |
|-------|--------|----------|
| Orthogonal | edgeStyle=orthogonalEdgeStyle | Flowcharts, architecture, network |
| Straight | no edgeStyle | UML class/sequence |
| Entity Relation | edgeStyle=entityRelationEdgeStyle | ER diagrams |
| Curved | curved=1 | Mind maps |
| Elbow | edgeStyle=elbowEdgeStyle;elbow=vertical; | Simple 1-bend flows |

Useful edge attributes: `rounded=1`, `endArrow=classic`, `dashed=1`, `strokeColor=#...`, `strokeWidth=2`

## Containers

**Swimlane (titled):**
```xml
<mxCell id="svc1" value="User Service" style="swimlane;startSize=30;fillColor=#dae8fc;strokeColor=#6c8ebf;html=1;" vertex="1" parent="1">
  <mxGeometry x="100" y="100" width="300" height="200" as="geometry"/>
</mxCell>
```

**Group (invisible):**
```xml
<mxCell id="grp1" value="" style="group;" vertex="1" parent="1">
  <mxGeometry x="100" y="100" width="300" height="200" as="geometry"/>
</mxCell>
```

Children set `parent="containerId"` and use coordinates relative to the container.

Always add `pointerEvents=0;` to container styles that should not capture connections.

## Swimlanes (Flat)

Use flat swimlanes at `parent="1"`, stacked vertically. One row of nodes per lane.

Fixed values:
- Lane size: `x=0, y=lane_index*150, width=CANVAS_W, height=150`
- Lane style: `swimlane;horizontal=0;startSize=110;fillColor=...;html=1;`
- Child nodes: `parent="laneId"`, `x = 120 + col*180`, `y = 45`, size `140×60` (or `140×80` for diamonds)
- Cross-lane edges: `parent="1"` (not inside a lane)

Pick `CANVAS_W = max_col * 180 + 300`. Lane colors: `#f5f5f5`, `#e8f4f8`, `#fff0e6`, `#e8f5e9`, `#fff9e6`, `#fce4ec`

Example:
```xml
<mxCell id="lane1" value="Customer" style="swimlane;horizontal=0;startSize=110;fillColor=#f5f5f5;html=1;" vertex="1" parent="1">
  <mxGeometry x="0" y="0" width="1800" height="150" as="geometry"/>
</mxCell>
<mxCell id="n1" value="Place Order" style="rounded=1;whiteSpace=wrap;html=1;" vertex="1" parent="lane1">
  <mxGeometry x="120" y="45" width="140" height="60" as="geometry"/>
</mxCell>
<mxCell id="lane2" value="System" style="swimlane;horizontal=0;startSize=110;fillColor=#e8f4f8;html=1;" vertex="1" parent="1">
  <mxGeometry x="0" y="150" width="1800" height="150" as="geometry"/>
</mxCell>
<mxCell id="n2" value="Validate" style="rounded=1;whiteSpace=wrap;html=1;" vertex="1" parent="lane2">
  <mxGeometry x="300" y="45" width="140" height="60" as="geometry"/>
</mxCell>
<mxCell id="e1" edge="1" parent="1" source="n1" target="n2" style="edgeStyle=orthogonalEdgeStyle;rounded=1;html=1;">
  <mxGeometry relative="1" as="geometry"/>
</mxCell>
```

## Rigid Grid Layout

Use for every XML diagram:
- Column x = col_index * 180 + 40 (col 0 = 40, col 1 = 220, col 2 = 400, …)
- Row y = row_index * 120 + 40 (row 0 = 40, row 1 = 160, row 2 = 280, …)
- Node size: rectangles 140×60, diamonds 140×80, circles 60×60, documents 120×80, cylinders 100×70

## XML Well-formedness Rules

- NEVER include ANY XML comments in the output
- Escape special characters in attribute values: `&`, `<`, `>`, `"`
- Always use unique id values for each mxCell

## Diagram Generation Rules

- Do NOT debate the topic — pick one concrete scenario and commit
- Do NOT compute x/y coordinates in prose — use the rigid grid, do arithmetic mentally
- Do NOT add waypoints — edges route automatically
- Do NOT narrate building process — just emit XML
- Match the language of labels to the user's language

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| draw.io CLI not found | Desktop app not installed | Keep the .drawio file, tell user to install |
| Export produces corrupt file | Invalid XML | Validate XML well-formedness |
| Diagram opens blank | Missing root cells | Ensure id="0" and id="1" exist |
| Edges not rendering | Self-closing edge cell | Use expanded form with child mxGeometry |
| File won't open after export | Wrong path | Print absolute file path |
