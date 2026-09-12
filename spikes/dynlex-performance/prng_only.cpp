// Workload — PRNG-only baseline, drawing the same 1.2e8 doubles as orient3d.cpp.
//
// Added in response to a review finding (I1): the orient3d and tritri timed
// regions start the clock before generation, so the PRNG draws are inside the
// measured time and that was not disclosed. This workload isolates the
// generation cost by drawing the *same* doubles in the *same* order as
// orient3d.cpp — four sample points (12 doubles) per iteration, 1e7
// iterations — and doing nothing else in the timed region, so its median can
// be subtracted from orient3d's to estimate the determinant-only share.

#include "common.hpp"

static const std::int64_t quadruple_count = 10000000;

int main() {
    reseed_with(88172645463325252ull);

    std::int64_t started = clock_milliseconds();
    std::int64_t index = 0;
    while (index < quadruple_count) {
        SamplePoint pa = next_random_sample_point();
        SamplePoint pb = next_random_sample_point();
        SamplePoint pc = next_random_sample_point();
        SamplePoint pd = next_random_sample_point();
        (void)pa;
        (void)pb;
        (void)pc;
        (void)pd;
        index = index + 1;
    }
    std::int64_t finished = clock_milliseconds();

    print_real(input_checksum());
    print_integer(generator_state());
    print_integer(finished - started);
    return 0;
}
