// SPDX-License-Identifier: MPL-2.0
// Reads a DXF or DWG with cadcodec and prints what it holds in a form that
// compares between the two: the version, each layer with its colour, then
// per model-space entity its type, layer and geometry (numbers to 1e-9),
// and for a 3DSOLID whether its SAT parses and validates. Usage:
// dxf-dwg-reference FILE
use acadrust::entities::EntityType;
use acadrust::types::Color;
use acadrust::{DwgReader, DxfReader, SatDocument};

fn n(v: f64) -> String {
    let r = (v * 1e9).round() / 1e9;
    format!("{}", if r == 0.0 { 0.0 } else { r })
}

fn p(v: &acadrust::types::Vector3) -> String {
    format!("({} {} {})", n(v.x), n(v.y), n(v.z))
}

fn colour(c: &Color) -> String {
    match c {
        Color::Index(i) => format!("{i}"),
        other => format!("{other:?}"),
    }
}

fn main() {
    let path = std::env::args().nth(1).expect("usage: dxf-dwg-reference FILE");
    let doc = if path.to_lowercase().ends_with(".dwg") {
        DwgReader::from_file(&path).expect("open dwg").read().expect("read dwg")
    } else {
        DxfReader::from_file(&path).expect("open dxf").read().expect("read dxf")
    };
    println!("version {:?}", doc.version);
    let mut layers: Vec<String> = doc.layers.iter().map(|l| format!("layer {} colour {}", l.name, colour(&l.color))).collect();
    layers.sort();
    for l in layers {
        println!("{l}");
    }
    for e in doc.model_space_entities() {
        match e {
            EntityType::Line(l) => println!("LINE {} {} {}", l.common.layer, p(&l.start), p(&l.end)),
            EntityType::LwPolyline(l) => {
                let pts: Vec<String> = l.vertices.iter().map(|v| format!("({} {})", n(v.location.x), n(v.location.y))).collect();
                println!("LWPOLYLINE {} closed {} elevation {} {}", l.common.layer, l.is_closed, n(l.elevation), pts.join(" "));
            }
            EntityType::Polyline3D(l) => {
                let pts: Vec<String> = l.vertices.iter().map(|v| p(&v.position)).collect();
                println!("POLYLINE3D {} closed {} {}", l.common.layer, l.flags.closed, pts.join(" "));
            }
            EntityType::PolyfaceMesh(m) => {
                let pts: Vec<String> = m.vertices.iter().map(|v| p(&v.location)).collect();
                let faces: Vec<String> = m.faces.iter().map(|f| format!("[{} {} {} {}]", f.index1, f.index2, f.index3, f.index4)).collect();
                println!("POLYFACE {} {} {}", m.common.layer, pts.join(" "), faces.join(" "));
            }
            EntityType::Text(t) => println!(
                "TEXT {} {:?} at {} height {} rotation {} align {:?}",
                t.common.layer, t.value, p(&t.insertion_point), n(t.height), n(t.rotation), t.horizontal_alignment
            ),
            EntityType::Solid3D(s) => {
                let sat = s.acis_data.sat_data.clone();
                let verdict = match SatDocument::parse(&sat) {
                    Ok(d) => {
                        let errors = d.validate();
                        format!("faces {} edges {} vertices {} errors {}", d.faces().len(), d.edges().len(), d.vertices().len(), errors.len())
                    }
                    Err(e) => format!("unparsed {e:?}"),
                };
                println!("3DSOLID {} {}", s.common.layer, verdict);
            }
            other => println!("{} {}", other.as_entity().entity_type(), other.as_entity().layer()),
        }
    }
}
