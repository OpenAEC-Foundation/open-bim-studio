use acadrust::entities::{Face3D, Insert, Polyline3D};
use acadrust::types::Matrix3;
use acadrust::{
    Arc, BlockRecord, CadDocument, Circle, DwgReader, DwgWriter, Ellipse, EntityType, Line,
    LwPolyline, TableEntry, Vector2, Vector3,
};
use std::f64::consts::{PI, TAU};
use std::io::{self, Write};
use std::path::Path;

const MAX_SEGMENTS: usize = 1_000_000;
const MAX_FILE_BYTES: u64 = 256 * 1024 * 1024;

#[derive(Default)]
struct Wireframe {
    entities: usize,
    unsupported: usize,
    segments: Vec<[f64; 6]>,
}

impl Wireframe {
    fn segment(&mut self, first: Vector3, last: Vector3) -> Result<(), String> {
        let values = [first.x, first.y, first.z, last.x, last.y, last.z];
        if !values.iter().all(|value| value.is_finite()) {
            return Err("Non-finite drawing coordinate".into());
        }
        if self.segments.len() == MAX_SEGMENTS {
            return Err("Drawing exceeds wireframe segment limit".into());
        }
        self.segments.push(values);
        Ok(())
    }

    fn arc<F>(&mut self, start: f64, sweep: f64, point: F) -> Result<(), String>
    where
        F: Fn(f64) -> Vector3,
    {
        if !start.is_finite() || !sweep.is_finite() || sweep.abs() > TAU + 1e-8 {
            return Err("Invalid arc angle".into());
        }
        let steps = ((sweep.abs() / (PI / 36.0)).ceil() as usize).clamp(1, 144);
        let mut previous = point(start);
        for index in 1..=steps {
            let angle = start + sweep * (index as f64 / steps as f64);
            let next = point(angle);
            self.segment(previous, next)?;
            previous = next;
        }
        Ok(())
    }

    fn chain(&mut self, points: &[Vector3], closed: bool) -> Result<(), String> {
        for pair in points.windows(2) {
            self.segment(pair[0], pair[1])?;
        }
        if closed && points.len() > 2 {
            self.segment(*points.last().unwrap(), points[0])?;
        }
        Ok(())
    }

    fn bulged_edge(&mut self, first: Vector3, last: Vector3, bulge: f64) -> Result<(), String> {
        if bulge.abs() < 1e-12 {
            return self.segment(first, last);
        }
        if !bulge.is_finite() {
            return Err("Invalid polyline bulge".into());
        }
        let dx = last.x - first.x;
        let dy = last.y - first.y;
        let chord = dx.hypot(dy);
        if chord <= 1e-12 {
            return Ok(());
        }
        let sweep = 4.0 * bulge.atan();
        let offset = chord * (1.0 - bulge * bulge) / (4.0 * bulge);
        let center_x = (first.x + last.x) * 0.5 - dy / chord * offset;
        let center_y = (first.y + last.y) * 0.5 + dx / chord * offset;
        let radius = (first.x - center_x).hypot(first.y - center_y);
        let start = (first.y - center_y).atan2(first.x - center_x);
        self.arc(start, sweep, |angle| {
            Vector3::new(
                center_x + radius * angle.cos(),
                center_y + radius * angle.sin(),
                first.z + (last.z - first.z) * ((angle - start) / sweep),
            )
        })
    }

    fn add(&mut self, entity: &EntityType) -> Result<(), String> {
        self.entities += 1;
        match entity {
            EntityType::Line(line) => self.segment(line.start, line.end),
            EntityType::Circle(circle) => {
                if !circle.radius.is_finite() || circle.radius <= 0.0 {
                    return Err("Invalid circle radius".into());
                }
                self.arc(0.0, TAU, |angle| circle.point_at_angle_wcs(angle))
            }
            EntityType::Arc(arc) => {
                if !arc.radius.is_finite() || arc.radius <= 0.0 {
                    return Err("Invalid arc radius".into());
                }
                self.arc(arc.start_angle, arc.sweep_angle(), |angle| {
                    arc.point_at_angle_wcs(angle)
                })
            }
            EntityType::Ellipse(ellipse) => {
                let major = ellipse.major_axis;
                let radius = major.length();
                let normal = ellipse.normal;
                let normal_length = normal.length();
                let ratio = ellipse.minor_axis_ratio;
                let delta = ellipse.end_parameter - ellipse.start_parameter;
                if !radius.is_finite()
                    || radius <= 0.0
                    || !normal_length.is_finite()
                    || normal_length <= 0.0
                    || !ratio.is_finite()
                    || ratio <= 0.0
                    || !delta.is_finite()
                    || delta.abs() > TAU + 1e-8
                {
                    return Err("Invalid ellipse geometry".into());
                }
                let minor_direction = normal.cross(&major);
                let minor_length = minor_direction.length();
                if !minor_length.is_finite() || minor_length <= 0.0 {
                    return Err("Invalid ellipse axes".into());
                }
                let minor = minor_direction * (radius * ratio / minor_length);
                let sweep = if delta < 0.0 { delta + TAU } else { delta };
                self.arc(ellipse.start_parameter, sweep, |angle| {
                    let cosine = angle.cos();
                    let sine = angle.sin();
                    Vector3::new(
                        ellipse.center.x + major.x * cosine + minor.x * sine,
                        ellipse.center.y + major.y * cosine + minor.y * sine,
                        ellipse.center.z + major.z * cosine + minor.z * sine,
                    )
                })
            }
            EntityType::LwPolyline(line) => {
                let basis = Matrix3::arbitrary_axis(line.normal);
                let count = line.vertices.len();
                let edges = if line.is_closed && count > 1 {
                    count
                } else {
                    count.saturating_sub(1)
                };
                for index in 0..edges {
                    let first = &line.vertices[index];
                    let last = &line.vertices[(index + 1) % count];
                    let from = Vector3::new(first.location.x, first.location.y, line.elevation);
                    let to = Vector3::new(last.location.x, last.location.y, line.elevation);
                    // Tessellate in the entity plane before applying its object-space basis.
                    let mut local = Wireframe::default();
                    local.bulged_edge(from, to, first.bulge)?;
                    for segment in local.segments {
                        self.segment(
                            basis * Vector3::new(segment[0], segment[1], segment[2]),
                            basis * Vector3::new(segment[3], segment[4], segment[5]),
                        )?;
                    }
                }
                Ok(())
            }
            EntityType::Polyline(line) => self.chain(
                &line
                    .vertices
                    .iter()
                    .map(|vertex| vertex.location)
                    .collect::<Vec<_>>(),
                line.is_closed(),
            ),
            EntityType::Polyline3D(line) => self.chain(
                &line
                    .vertices
                    .iter()
                    .map(|vertex| vertex.position)
                    .collect::<Vec<_>>(),
                line.is_closed(),
            ),
            EntityType::Polyline2D(line) => {
                let basis = Matrix3::arbitrary_axis(line.normal);
                let count = line.vertices.len();
                let edges = if line.is_closed() && count > 1 {
                    count
                } else {
                    count.saturating_sub(1)
                };
                for index in 0..edges {
                    let first = &line.vertices[index];
                    let last = &line.vertices[(index + 1) % count];
                    let from = Vector3::new(first.location.x, first.location.y, line.elevation);
                    let to = Vector3::new(last.location.x, last.location.y, line.elevation);
                    let mut local = Wireframe::default();
                    local.bulged_edge(from, to, first.bulge)?;
                    for segment in local.segments {
                        self.segment(
                            basis * Vector3::new(segment[0], segment[1], segment[2]),
                            basis * Vector3::new(segment[3], segment[4], segment[5]),
                        )?;
                    }
                }
                Ok(())
            }
            EntityType::Face3D(face) => self.chain(&face.corners(), true),
            _ => {
                self.unsupported += 1;
                Ok(())
            }
        }
    }

    fn add_document_entity(
        &mut self,
        document: &CadDocument,
        entity: &EntityType,
        ancestry: &mut Vec<String>,
    ) -> Result<(), String> {
        if let EntityType::Insert(insert) = entity {
            if self.entities >= MAX_SEGMENTS {
                return Err("Drawing exceeds entity limit".into());
            }
            self.entities += 1;
            let Some(block) = document.block_records.get(&insert.block_name) else {
                self.unsupported += 1;
                return Ok(());
            };
            if ancestry.len() >= 16 || ancestry.contains(&insert.block_name) {
                self.unsupported += 1;
                return Ok(());
            }
            let expanded_count = block
                .entity_handles
                .len()
                .saturating_mul(insert.column_count as usize)
                .saturating_mul(insert.row_count as usize);
            if expanded_count > MAX_SEGMENTS.saturating_sub(self.entities) {
                return Err("Block reference exceeds entity limit".into());
            }
            ancestry.push(insert.block_name.clone());
            for child in insert.explode_from_document(document) {
                self.add_document_entity(document, &child, ancestry)?;
            }
            ancestry.pop();
            Ok(())
        } else {
            if self.entities >= MAX_SEGMENTS {
                return Err("Drawing exceeds entity limit".into());
            }
            self.add(entity)
        }
    }

    fn write(&self, mut output: impl Write) -> io::Result<()> {
        writeln!(
            output,
            "DYNEDRA-DWG-1 {} {} {}",
            self.entities,
            self.segments.len(),
            self.unsupported
        )?;
        for s in &self.segments {
            writeln!(
                output,
                "{:.17} {:.17} {:.17} {:.17} {:.17} {:.17}",
                s[0], s[1], s[2], s[3], s[4], s[5]
            )?;
        }
        Ok(())
    }
}

fn export(path: &Path) -> Result<(), String> {
    let size = std::fs::metadata(path)
        .map_err(|error| error.to_string())?
        .len();
    if size > MAX_FILE_BYTES {
        return Err("DWG file exceeds size limit".into());
    }
    let mut reader = DwgReader::from_file(path).map_err(|error| error.to_string())?;
    let drawing = reader.read().map_err(|error| error.to_string())?;
    let mut wireframe = Wireframe::default();
    for entity in drawing.model_space_entities() {
        wireframe.add_document_entity(&drawing, entity, &mut Vec::new())?;
    }
    wireframe
        .write(io::stdout().lock())
        .map_err(|error| error.to_string())
}

fn fixture(path: &Path) -> Result<(), String> {
    let mut drawing = CadDocument::new();
    drawing
        .add_entity(EntityType::Line(Line::from_coords(
            -4.0, -2.0, 0.0, 4.0, -2.0, 0.0,
        )))
        .map_err(|error| error.to_string())?;
    drawing
        .add_entity(EntityType::Circle(Circle::from_coords(0.0, 0.0, 0.0, 1.5)))
        .map_err(|error| error.to_string())?;
    drawing
        .add_entity(EntityType::Arc(Arc::from_coords(
            0.0,
            0.0,
            1.0,
            1.0,
            0.0,
            PI / 2.0,
        )))
        .map_err(|error| error.to_string())?;
    let mut polyline = LwPolyline::new();
    polyline.add_point_with_bulge(Vector2::new(0.0, 3.0), (PI / 8.0).tan());
    polyline.add_point(Vector2::new(2.0, 3.0));
    polyline.add_point(Vector2::new(2.0, 4.0));
    drawing
        .add_entity(EntityType::LwPolyline(polyline))
        .map_err(|error| error.to_string())?;
    drawing
        .add_entity(EntityType::Polyline3D(Polyline3D::from_points(vec![
            Vector3::new(-1.0, 0.0, 0.0),
            Vector3::new(0.0, 1.0, 1.0),
            Vector3::new(1.0, 0.0, 2.0),
        ])))
        .map_err(|error| error.to_string())?;
    drawing
        .add_entity(EntityType::Face3D(Face3D::triangle(
            Vector3::new(0.0, -1.0, 1.0),
            Vector3::new(1.0, -1.0, 1.0),
            Vector3::new(0.0, -1.0, 2.0),
        )))
        .map_err(|error| error.to_string())?;
    drawing
        .add_entity(EntityType::Ellipse(Ellipse::from_center_axes(
            Vector3::new(-2.0, 2.0, 0.0),
            Vector3::new(2.0, 0.0, 0.0),
            0.5,
        )))
        .map_err(|error| error.to_string())?;

    let mut block = BlockRecord::new("DynedraSymbol");
    let block_handle = drawing.allocate_handle();
    block.set_handle(block_handle);
    block.block_entity_handle = drawing.allocate_handle();
    block.block_end_handle = drawing.allocate_handle();
    drawing
        .block_records
        .add(block)
        .map_err(|error| error.to_string())?;
    let mut block_line = EntityType::Line(Line::from_coords(0.0, 0.0, 0.0, 2.0, 0.0, 0.0));
    block_line.common_mut().owner_handle = block_handle;
    drawing
        .add_entity(block_line)
        .map_err(|error| error.to_string())?;
    let mut block_circle = EntityType::Circle(Circle::from_coords(1.0, 0.0, 0.0, 0.5));
    block_circle.common_mut().owner_handle = block_handle;
    drawing
        .add_entity(block_circle)
        .map_err(|error| error.to_string())?;
    drawing
        .add_entity(EntityType::Insert(Insert::new(
            "DynedraSymbol",
            Vector3::new(8.0, 0.0, 0.0),
        )))
        .map_err(|error| error.to_string())?;
    DwgWriter::write_to_file(path, &drawing).map_err(|error| error.to_string())
}

fn main() {
    let arguments: Vec<_> = std::env::args_os().collect();
    let result = match arguments.as_slice() {
        [_, command, path] if command == "export" => export(Path::new(path)),
        [_, command, path] if command == "fixture" => fixture(Path::new(path)),
        _ => Err("Usage: dynedra-dwg-reader <export|fixture> <path.dwg>".into()),
    };
    if let Err(error) = result {
        eprintln!("DWG reader: {error}");
        std::process::exit(1);
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn bulge_and_closed_chain_have_expected_endpoints() {
        let mut wireframe = Wireframe::default();
        wireframe
            .bulged_edge(
                Vector3::new(0.0, 0.0, 0.0),
                Vector3::new(2.0, 0.0, 0.0),
                1.0,
            )
            .unwrap();
        assert!(wireframe.segments.len() > 2);
        assert!((wireframe.segments[0][0] - 0.0).abs() < 1e-12);
        assert!((wireframe.segments.last().unwrap()[3] - 2.0).abs() < 1e-12);
        assert!(wireframe
            .segments
            .iter()
            .any(|segment| segment[1].abs() > 0.5));
    }

    #[test]
    fn two_vertex_closed_polyline_draws_both_edges() {
        let mut line = LwPolyline::new();
        line.add_point(Vector2::new(0.0, 0.0));
        line.add_point(Vector2::new(2.0, 0.0));
        line.close();
        let mut wireframe = Wireframe::default();
        wireframe.add(&EntityType::LwPolyline(line)).unwrap();
        assert_eq!(wireframe.segments.len(), 2);
        assert_eq!(wireframe.segments[0][0], 0.0);
        assert_eq!(wireframe.segments[1][0], 2.0);
    }

    #[test]
    fn quarter_ellipse_has_expected_endpoints() {
        let mut ellipse = Ellipse::from_center_axes(
            Vector3::new(3.0, 4.0, 1.0),
            Vector3::new(2.0, 0.0, 0.0),
            0.5,
        );
        ellipse.end_parameter = PI / 2.0;
        let mut wireframe = Wireframe::default();
        wireframe.add(&EntityType::Ellipse(ellipse)).unwrap();
        assert_eq!(wireframe.segments.len(), 18);
        assert!((wireframe.segments[0][0] - 5.0).abs() < 1e-12);
        assert!((wireframe.segments.last().unwrap()[4] - 5.0).abs() < 1e-12);
        assert!((wireframe.segments.last().unwrap()[5] - 1.0).abs() < 1e-12);
    }
}
