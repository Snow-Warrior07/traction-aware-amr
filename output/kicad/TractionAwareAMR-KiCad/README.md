# Traction-aware AMR: editable KiCad 10 project

Open traction_carrier.kicad_pro in KiCad 10, then use the schematic and PCB buttons.
Open PCB Editor > View > 3D Viewer for the component model.

The project includes its custom AMR symbol library and project library tables.
Standard footprints/3D models use the installed KiCad 10 standard libraries.
Footprints are embedded in the PCB; schematic symbols are embedded and supplied
in AMR.kicad_sym. Schematic symbol UUIDs are linked to PCB footprints.

Carrier: 96 x 96 mm, two copper layers, 29 components, 29 connected signal/power
nets plus 18 single-pad no-connect nets. Motor current stays in external drivers.
No physical hardware is required for this demonstration.

Local KiCad 10.0.6 validation: ERC 0; all-track DRC 0; unconnected items 0;
schematic/PCB parity issues 0. Check reports are included under verification/.
Exports include two actual 3D renders, schematic SVG, board STEP, Gerbers/drill,
netlist and BOM. These software checks do not establish manufacturing readiness.

Demo: https://snow-warrior07.github.io/traction-aware-amr/
Source: https://github.com/Snow-Warrior07/traction-aware-amr
