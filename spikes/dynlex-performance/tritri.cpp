// Workload 1 — triangle/triangle intersection over 1 million random pairs.
//
// The test is Moeller-Trumbore ray/triangle (1997) applied edge-wise: the two
// triangles are reported as intersecting when any of the three edges of A, taken
// as a segment, pierces B, or any edge of B pierces A. This is the variant the
// brief allows; it is not the full Moeller 1997 tri-tri overlap test and it does
// not detect coplanar overlap. Both languages run exactly this test.
//
// Triangles are three uniform random points in the unit cube.

#include "common.hpp"

static const std::int64_t pair_count = 1000000;
static const double parallel_epsilon = 0.000000000001;

// --- Vector algebra on the point record -----------------------------------

static inline SamplePoint difference_of(SamplePoint left, SamplePoint right) {
    return sample_point_at(left.x - right.x, left.y - right.y, left.z - right.z);
}

static inline SamplePoint cross_of(SamplePoint left, SamplePoint right) {
    double cx = (left.y * right.z) - (left.z * right.y);
    double cy = (left.z * right.x) - (left.x * right.z);
    double cz = (left.x * right.y) - (left.y * right.x);
    return sample_point_at(cx, cy, cz);
}

static inline double dot_of(SamplePoint left, SamplePoint right) {
    return (left.x * right.x) + ((left.y * right.y) + (left.z * right.z));
}

static inline double absolute_value_of(double v) { return v < 0.0 ? -v : v; }

// --- Moeller-Trumbore, segment form ---------------------------------------

static inline bool segment_pierces(SamplePoint orig, SamplePoint dest, SamplePoint va, SamplePoint vb,
                                   SamplePoint vc) {
    SamplePoint dir = difference_of(dest, orig);
    SamplePoint edgeone = difference_of(vb, va);
    SamplePoint edgetwo = difference_of(vc, va);
    SamplePoint pvec = cross_of(dir, edgetwo);
    double det = dot_of(edgeone, pvec);
    if (absolute_value_of(det) < parallel_epsilon) {
        return false;
    }
    double inv = 1.0 / det;
    SamplePoint tvec = difference_of(orig, va);
    double bary = dot_of(tvec, pvec) * inv;
    if (bary < 0.0) {
        return false;
    }
    if (bary > 1.0) {
        return false;
    }
    SamplePoint qvec = cross_of(tvec, edgeone);
    double bartwo = dot_of(dir, qvec) * inv;
    if (bartwo < 0.0) {
        return false;
    }
    if ((bary + bartwo) > 1.0) {
        return false;
    }
    double along = dot_of(edgetwo, qvec) * inv;
    if (along < 0.0) {
        return false;
    }
    if (along > 1.0) {
        return false;
    }
    return true;
}

static inline bool triangles_meet(SamplePoint pa, SamplePoint pb, SamplePoint pc, SamplePoint qa, SamplePoint qb,
                                  SamplePoint qc) {
    if (segment_pierces(pa, pb, qa, qb, qc)) {
        return true;
    }
    if (segment_pierces(pb, pc, qa, qb, qc)) {
        return true;
    }
    if (segment_pierces(pc, pa, qa, qb, qc)) {
        return true;
    }
    if (segment_pierces(qa, qb, pa, pb, pc)) {
        return true;
    }
    if (segment_pierces(qb, qc, pa, pb, pc)) {
        return true;
    }
    if (segment_pierces(qc, qa, pa, pb, pc)) {
        return true;
    }
    return false;
}

// --- Driver ----------------------------------------------------------------

int main() {
    reseed_with(88172645463325252ull);

    std::int64_t hits = 0;
    std::int64_t started = clock_milliseconds();
    std::int64_t index = 0;
    while (index < pair_count) {
        SamplePoint pa = next_random_sample_point();
        SamplePoint pb = next_random_sample_point();
        SamplePoint pc = next_random_sample_point();
        SamplePoint qa = next_random_sample_point();
        SamplePoint qb = next_random_sample_point();
        SamplePoint qc = next_random_sample_point();
        if (triangles_meet(pa, pb, pc, qa, qb, qc)) {
            hits = hits + 1;
        }
        index = index + 1;
    }
    std::int64_t finished = clock_milliseconds();

    print_integer(hits);
    print_real(input_checksum());
    print_integer(generator_state());
    print_integer(finished - started);
    return 0;
}
