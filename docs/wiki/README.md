# Open BIM Studio documentation

Open BIM Studio is an [OpenAEC Foundation](https://github.com/OpenAEC-Foundation) desktop application for creating and editing building models. You model walls, floors, roofs, columns, beams, piles, reinforcement and steel connections, look at them in 2D and 3D, and develop plans, sections, schedules and sheets from the same model. The application and its CAD kernel are written in DynLex. It runs natively on Linux (Vulkan/GLFW); a Windows port is in the repository.

> **Development preview.** `main` is the shared development baseline, not a production release. Features and file formats still change.

## Pages

| Page | What it covers |
|---|---|
| [User guide](User-guide.md) | How the program is organised: the ribbon and disciplines, modelling tools, sketches, views and sheets, properties and types |
| [Automation API](Automation-API.md) | Driving the editor from a script or an AI assistant: the folder protocol, its verbs and the MCP server |
| [Development](Development.md) | Building from source, the module layout, tests and how changes reach `main` |
| [Status](Status.md) | Where the project stands now: what was finished recently, what is open, what is in progress |

## Links

- Repository README: [README.md](https://github.com/OpenAEC-Foundation/open-bim-studio#readme) (and [Dutch](https://github.com/OpenAEC-Foundation/open-bim-studio/blob/main/README.nl.md))
- Previews: [releases](https://github.com/OpenAEC-Foundation/open-bim-studio/releases)
- Roadmap: [docs/roadmap.md](https://github.com/OpenAEC-Foundation/open-bim-studio/blob/main/docs/roadmap.md) · open risks: [docs/risks.md](https://github.com/OpenAEC-Foundation/open-bim-studio/blob/main/docs/risks.md)
- Issues: [open issues](https://github.com/OpenAEC-Foundation/open-bim-studio/issues)

These pages describe the program as it is on `main`. Where they and the code or an ADR disagree, the code and the ADRs win.
