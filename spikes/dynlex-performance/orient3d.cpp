// Workload 3 — plain f64 orient3d over 10 million random point quadruples.
//
// Non-adaptive: the 4x4 determinant in Shewchuk's translated-to-d form, with no
// error bound and no exact fallback. Counts the quadruples with a positive
// determinant.

#include "common.hpp"

static inline double the_orient3d(SamplePoint pa, SamplePoint pb, SamplePoint pc, SamplePoint pd) {
    double adx = pa.x - pd.x;
    double bdx = pb.x - pd.x;
    double cdx = pc.x - pd.x;
    double ady = pa.y - pd.y;
    double bdy = pb.y - pd.y;
    double cdy = pc.y - pd.y;
    double adz = pa.z - pd.z;
    double bdz = pb.z - pd.z;
    double cdz = pc.z - pd.z;
    return (adx * ((bdy * cdz) - (bdz * cdy))) + ((bdx * ((cdy * adz) - (cdz * ady))) + (cdx * ((ady * bdz) - (adz * bdy))));
}

static const std::int64_t quadruple_count = 10000000;

int main() {
    reseed_with(88172645463325252ull);

    std::int64_t positives = 0;
    std::int64_t started = clock_milliseconds();
    std::int64_t index = 0;
    while (index < quadruple_count) {
        SamplePoint pa = next_random_sample_point();
        SamplePoint pb = next_random_sample_point();
        SamplePoint pc = next_random_sample_point();
        SamplePoint pd = next_random_sample_point();
        if (the_orient3d(pa, pb, pc, pd) > 0.0) {
            positives = positives + 1;
        }
        index = index + 1;
    }
    std::int64_t finished = clock_milliseconds();

    print_integer(positives);
    print_real(input_checksum());
    print_integer(generator_state());
    print_integer(finished - started);
    return 0;
}
