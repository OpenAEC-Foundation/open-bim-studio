// SPDX-License-Identifier: MPL-2.0
// Rust counterpart of `wall_slice_workload.dl` against the pinned cadkernel:
// mode 0 repeats the window difference on the wall box, mode 1 repeats the
// plan slice of the cut wall at 1.2 m. Prints the total face count.
use cadkernel::brep::{combine, make, slice_by_plane, Operation};
use cadkernel::space::Plane;

fn main() {
    let args: Vec<String> = std::env::args().collect();
    let mode: usize = args[1].parse().unwrap();
    let iterations: usize = args[2].parse().unwrap();
    let wall = make::cuboid([0.0, 0.0, 0.0], [6.32, 0.32, 3.0]).unwrap();
    let window = make::cuboid([1.0, -0.1, 0.9], [1.3, 0.52, 1.6]).unwrap();
    let cut = combine(wall.clone(), window.clone(), Operation::Difference, 1e-9).unwrap();
    let plane = Plane::from_axes([0.0, 0.0, 1.2], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0]);
    let mut faces = 0usize;
    for _ in 0..iterations {
        if mode == 0 {
            let body = combine(wall.clone(), window.clone(), Operation::Difference, 1e-9).unwrap();
            faces += body.faces.len();
        } else {
            let sliced = slice_by_plane(&cut, plane).unwrap().unwrap();
            faces += sliced.negative.faces.len() + sliced.positive.faces.len();
        }
    }
    println!("{faces}");
}
