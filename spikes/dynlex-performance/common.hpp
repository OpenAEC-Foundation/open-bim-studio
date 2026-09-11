// Shared prelude for the three C++ workloads.
//
// Throwaway spike code. Line-for-line counterpart of common.dl: same clock,
// same generator, same checksum, same output formatting.

#ifndef SPIKE_COMMON_HPP
#define SPIKE_COMMON_HPP

#include <cstdint>
#include <cstdio>
#include <ctime>

// --- Output ---------------------------------------------------------------

static inline void print_integer(std::int64_t message) { std::printf("%lld\n", (long long)message); }

static inline void print_real(double message) { std::printf("%.17g\n", message); }

// --- Clock ----------------------------------------------------------------
//
// The same libc clock() the DynLex prelude calls, through the same UCRT.

static inline std::int64_t clock_milliseconds() {
    return (std::int64_t)((std::clock() * (std::clock_t)1000) / CLOCKS_PER_SEC);
}

// --- xorshift64* ----------------------------------------------------------

static std::uint64_t seedstate = 88172645463325252ull;
static double inputsum = 0.0;

static inline void reseed_with(std::uint64_t value) {
    seedstate = value;
    inputsum = 0.0;
}

static inline std::int64_t next_random_bits() {
    std::uint64_t s = seedstate;
    s ^= s >> 12;
    s ^= s << 25;
    s ^= s >> 27;
    seedstate = s;
    return (std::int64_t)(s * 2685821657736338717ull);
}

// 2 ** -53. DynLex has no scientific-notation float literals (see FINDINGS.md),
// so it is written as an exact division of two exactly representable doubles;
// this side is written the same way rather than as 0x1.0p-53.
static const double unit_scale = (1.0 / 9007199254740992.0);

static inline double next_random_unit_number() {
    double value = (double)((std::uint64_t)next_random_bits() >> 11) * unit_scale;
    inputsum += value;
    return value;
}

static inline double input_checksum() { return inputsum; }

static inline std::int64_t generator_state() { return (std::int64_t)seedstate; }

// --- A point-like record --------------------------------------------------
//
// Three f64 members, the shape the kernel's geometry types will have.

struct SamplePoint {
    double x;
    double y;
    double z;
};

static inline SamplePoint sample_point_at(double px, double py, double pz) {
    SamplePoint p;
    p.x = px;
    p.y = py;
    p.z = pz;
    return p;
}

static inline SamplePoint next_random_sample_point() {
    double px = next_random_unit_number();
    double py = next_random_unit_number();
    double pz = next_random_unit_number();
    return sample_point_at(px, py, pz);
}

#endif
