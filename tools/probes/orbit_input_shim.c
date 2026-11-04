/* SPDX-License-Identifier: MPL-2.0
 * Diagnostic input/profiling shim, never linked into the product.
 * An owned mmap control block enables finite camera motion in this process only.
 * Outside that interval all GLFW input delegates to the real implementation.
 */
#define _POSIX_C_SOURCE 200809L
#include <dlfcn.h>
#include <fcntl.h>
#include <math.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <time.h>
#include <unistd.h>
#ifdef __linux__
#include <sys/prctl.h>
#endif

typedef struct GLFWwindow GLFWwindow;
static volatile uint64_t *control;
static int initialised;
static uint64_t command_start;
static uint64_t input_start;
static uint64_t reported_input;
static uint64_t scroll_at;
static uint64_t scroll_start;
static int custom_anchor;
static double anchor_x,anchor_y;
typedef void (*ScrollCallback)(GLFWwindow *, double, double);
static ScrollCallback scroll_callback;
__attribute__((constructor)) static void prepare_output(void) {
    if (getenv("OBS_ORBIT_CONTROL")) {
#ifdef __linux__
        /* Only the owning harness and its debugger children may inspect us. */
        if (getenv("OBS_NAV_SAMPLE_STACKS"))
            prctl(PR_SET_PTRACER, (unsigned long)getppid(), 0UL, 0UL, 0UL);
#endif
        setvbuf(stdout, NULL, _IOLBF, 0);
        const char *point_x=getenv("OBS_NAV_ANCHOR_X"),*point_y=getenv("OBS_NAV_ANCHOR_Y");
        if(point_x && point_y) {
            char *end_x,*end_y;
            anchor_x=strtod(point_x,&end_x);anchor_y=strtod(point_y,&end_y);
            custom_anchor=!*end_x && !*end_y && isfinite(anchor_x) && isfinite(anchor_y);
        }
        fprintf(stderr, "OBS_ORBIT_SHIM pid=%ld parent=%ld\n", (long)getpid(), (long)getppid());
    }
}
static uint64_t now_ns(void) {
    struct timespec t;
    clock_gettime(CLOCK_MONOTONIC, &t);
    return (uint64_t)t.tv_sec * 1000000000ULL + (uint64_t)t.tv_nsec;
}
static int active(double *elapsed) {
    if (!initialised) {
        initialised = 1;
        const char *path = getenv("OBS_ORBIT_CONTROL");
        if (path) {
            int fd = open(path, O_RDONLY);
            struct stat st;
            if (fd >= 0) {
                if (!fstat(fd, &st) && st.st_size == 32) {
                    void *p = mmap(NULL, 32, PROT_READ, MAP_SHARED, fd, 0);
                    if (p != MAP_FAILED) control = p;
                }
                close(fd);
            }
        }
    }
    if (!control || control[2] != (uint64_t)getppid()) return 0;
    uint64_t start = control[0], now = now_ns();
    if (!start || now < start || now - start >= control[1]) return 0;
    *elapsed = (double)(now - start) / 1e9;
    return 1;
}
void glfwGetCursorPos(GLFWwindow *window, double *x, double *y) {
    static void (*real)(GLFWwindow *, double *, double *);
    if (!real) real = dlsym(RTLD_NEXT, "glfwGetCursorPos");
    real(window, x, y); /* Retain the real input-query cost and side effects. */
    double elapsed;
    if (active(&elapsed)) {
        unsigned mode = (unsigned)control[3];
        /* Controlled ablation: fold the inset in the fixed 1440x900 harness. */
        if (mode == 4) {
            *x = 310.0; *y = 650.0;
            return;
        }
        *x = (custom_anchor ? anchor_x : (mode == 1 || mode == 2 ? 650.0 : 850.0)) +
             (mode == 1 || mode == 5 ? 0 : (int)(230.0 * sin(elapsed * .9)));
        *y = (custom_anchor ? anchor_y : 450.0) + (mode == 1 || mode == 5 ? 0 : (int)(125.0 * sin(elapsed * .6)));
        if ((mode == 1 || mode == 5) && scroll_callback) {
            uint64_t now = now_ns();
            if (scroll_start != control[0]) {
                scroll_start = control[0];
                scroll_at = 0;
            }
            if (now - scroll_at >= 50000000ULL) {
                double steps = ((unsigned)(elapsed / 2.0) % 2) ? -.125 : .125;
                scroll_at = input_start = now;
                scroll_callback(window, 0, steps);
                fprintf(stderr, "OBS_INPUT at_ns=%llu steps=%.3f\n",
                        (unsigned long long)now, steps);
            }
        } else {
            input_start = now_ns();
        }
    }
}
ScrollCallback glfwSetScrollCallback(GLFWwindow *window, ScrollCallback callback) {
    static ScrollCallback (*real)(GLFWwindow *, ScrollCallback);
    if (!real) real = dlsym(RTLD_NEXT, "glfwSetScrollCallback");
    scroll_callback = callback;
    return real(window, callback);
}
int glfwGetMouseButton(GLFWwindow *window, int button) {
    static int (*real)(GLFWwindow *, int);
    if (!real) real = dlsym(RTLD_NEXT, "glfwGetMouseButton");
    int value = real(window, button);
    double elapsed;
    if (active(&elapsed)) {
        if (button == 0 && control[3] == 4) return 1;
        if (button == 1 && control[3] == 0) return 1;
        if (button == 2 && (control[3] == 2 || control[3] == 3)) return 1;
    }
    return value;
}
int vkBeginCommandBuffer(void *command, const void *info) {
    static int (*real)(void *, const void *);
    if (!real) real = dlsym(RTLD_NEXT, "vkBeginCommandBuffer");
    command_start = now_ns();
    return real(command, info);
}
int vkEndCommandBuffer(void *command) {
    static int (*real)(void *);
    if (!real) real = dlsym(RTLD_NEXT, "vkEndCommandBuffer");
    int result = real(command);
    double elapsed;
    if (active(&elapsed)) fprintf(stderr,"OBS_HOST record_us=%llu\n",(unsigned long long)((now_ns()-command_start)/1000));
    return result;
}
int vkQueuePresentKHR(void *queue, const void *info) {
    static int (*real)(void *, const void *);
    if (!real) real = dlsym(RTLD_NEXT, "vkQueuePresentKHR");
    uint64_t started = now_ns();
    int result = real(queue, info);
    double elapsed;
    if (active(&elapsed)) {
        uint64_t now = now_ns();
        fprintf(stderr,"OBS_HOST present_us=%llu at_ns=%llu input_age_us=%llu\n",
                (unsigned long long)((now-started)/1000),
                (unsigned long long)now,
                (unsigned long long)(input_start ? (now-input_start)/1000 : 0));
        if (input_start && input_start != reported_input) {
            fprintf(stderr,"OBS_HOST first_input_us=%llu\n",
                    (unsigned long long)((now-input_start)/1000));
            reported_input = input_start;
        }
    }
    return result;
}
