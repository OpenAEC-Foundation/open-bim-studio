// Workload 2 — top-down BVH build over 1 million random axis-aligned boxes.
//
// Median split on the longest axis of the node's own bounding box, leaf size 4.
// The median is found with a Hoare-partition quickselect whose pivot is the
// centroid of the middle element of the range, so the partition — and therefore
// the whole tree — is deterministic and identical in both languages.
//
// Timed region: the build only. Box generation is outside it and reported
// separately.

#include "common.hpp"

#include <cstdlib>

static const std::int64_t box_count = 1000000;
static const std::int64_t leaf_size = 4;
static const double half_extent_scale = 0.01;

// --- Storage ---------------------------------------------------------------
//
// boxes holds six f64 per box: lo x, lo y, lo z, hi x, hi y, hi z.
// order is the index permutation the build partitions in place.

struct BvhNode {
    double minx;
    double miny;
    double minz;
    double maxx;
    double maxy;
    double maxz;
    std::int64_t left;
    std::int64_t right;
    std::int64_t first;
    std::int64_t span;
};

static double *boxes;
static std::int64_t *order;
static BvhNode *nodes;
static std::int64_t nodecount = 0;

// --- Box access ------------------------------------------------------------

static inline double low_bound(std::int64_t item, std::int64_t axis) { return boxes[(6 * item) + axis]; }

static inline double high_bound(std::int64_t item, std::int64_t axis) { return boxes[(6 * item) + axis + 3]; }

static inline double centroid_of(std::int64_t item, std::int64_t axis) {
    return (low_bound(item, axis) + high_bound(item, axis)) * 0.5;
}

static inline std::int64_t ordered_box_at(std::int64_t slot) { return order[slot]; }

static inline void swap_ordered_boxes(std::int64_t one, std::int64_t two) {
    std::int64_t held = order[one];
    order[one] = order[two];
    order[two] = held;
}

// --- Deterministic quickselect --------------------------------------------
//
// Hoare partition, pivot = centroid of the middle element. hi is exclusive.

static void select_median(std::int64_t lo, std::int64_t hi, std::int64_t rank, std::int64_t axis) {
    std::int64_t low = lo;
    std::int64_t high = hi;
    while ((high - low) > 1) {
        double pivot = centroid_of(ordered_box_at(low + ((high - low) / 2)), axis);
        std::int64_t cursor = low;
        std::int64_t trail = high - 1;
        while (cursor <= trail) {
            while (centroid_of(ordered_box_at(cursor), axis) < pivot) {
                cursor = cursor + 1;
            }
            while (centroid_of(ordered_box_at(trail), axis) > pivot) {
                trail = trail - 1;
            }
            if (cursor <= trail) {
                swap_ordered_boxes(cursor, trail);
                cursor = cursor + 1;
                trail = trail - 1;
            }
        }
        if (rank <= trail) {
            high = trail + 1;
        } else if (rank >= cursor) {
            low = cursor;
        } else {
            return;
        }
    }
}

// --- Build -----------------------------------------------------------------

static std::int64_t build_bvh_node(std::int64_t first, std::int64_t span) {
    std::int64_t self = nodecount;
    nodecount = nodecount + 1;

    std::int64_t item = ordered_box_at(first);
    double minx = low_bound(item, 0);
    double miny = low_bound(item, 1);
    double minz = low_bound(item, 2);
    double maxx = high_bound(item, 0);
    double maxy = high_bound(item, 1);
    double maxz = high_bound(item, 2);
    std::int64_t cursor = first + 1;
    while (cursor < (first + span)) {
        item = ordered_box_at(cursor);
        minx = minx < low_bound(item, 0) ? minx : low_bound(item, 0);
        miny = miny < low_bound(item, 1) ? miny : low_bound(item, 1);
        minz = minz < low_bound(item, 2) ? minz : low_bound(item, 2);
        maxx = maxx > high_bound(item, 0) ? maxx : high_bound(item, 0);
        maxy = maxy > high_bound(item, 1) ? maxy : high_bound(item, 1);
        maxz = maxz > high_bound(item, 2) ? maxz : high_bound(item, 2);
        cursor = cursor + 1;
    }

    std::int64_t leftchild = 0 - 1;
    std::int64_t rightchild = 0 - 1;

    if (span > leaf_size) {
        std::int64_t axis = 0;
        double widest = maxx - minx;
        if ((maxy - miny) > widest) {
            axis = 1;
            widest = maxy - miny;
        }
        if ((maxz - minz) > widest) {
            axis = 2;
        }
        std::int64_t half = span / 2;
        select_median(first, first + span, first + half, axis);
        leftchild = build_bvh_node(first, half);
        rightchild = build_bvh_node(first + half, span - half);
    }

    BvhNode built;
    built.minx = minx;
    built.miny = miny;
    built.minz = minz;
    built.maxx = maxx;
    built.maxy = maxy;
    built.maxz = maxz;
    built.left = leftchild;
    built.right = rightchild;
    built.first = first;
    built.span = span;
    nodes[self] = built;
    return self;
}

// --- Driver ----------------------------------------------------------------

int main() {
    boxes = (double *)std::calloc((std::size_t)(6 * box_count), sizeof(double));
    order = (std::int64_t *)std::calloc((std::size_t)box_count, sizeof(std::int64_t));
    nodes = (BvhNode *)std::calloc((std::size_t)(box_count + 16), sizeof(BvhNode));

    reseed_with(88172645463325252ull);

    std::int64_t index = 0;
    while (index < box_count) {
        double cx = next_random_unit_number();
        double cy = next_random_unit_number();
        double cz = next_random_unit_number();
        double hx = next_random_unit_number() * half_extent_scale;
        double hy = next_random_unit_number() * half_extent_scale;
        double hz = next_random_unit_number() * half_extent_scale;
        boxes[6 * index] = cx - hx;
        boxes[(6 * index) + 1] = cy - hy;
        boxes[(6 * index) + 2] = cz - hz;
        boxes[(6 * index) + 3] = cx + hx;
        boxes[(6 * index) + 4] = cy + hy;
        boxes[(6 * index) + 5] = cz + hz;
        order[index] = index;
        index = index + 1;
    }

    std::int64_t started = clock_milliseconds();
    std::int64_t root = build_bvh_node(0, box_count);
    std::int64_t finished = clock_milliseconds();

    BvhNode top = nodes[root];
    print_integer(nodecount);
    print_real(top.minx);
    print_real(top.miny);
    print_real(top.minz);
    print_real(top.maxx);
    print_real(top.maxy);
    print_real(top.maxz);
    print_real(input_checksum());
    print_integer(generator_state());
    print_integer(finished - started);
    return 0;
}
