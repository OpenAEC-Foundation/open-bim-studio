/* SPDX-License-Identifier: MPL-2.0 */
/*
 * The calls of the BIM slice whose C names or types differ between POSIX
 * (glibc) and Windows (the UCRT through llvm-mingw), under one name each,
 * so that the same DynLex source links on both. Built as the static library
 * `libobs_platform.a` before the slice is compiled; the slice calls it as
 * the library "obs_platform". Every number crosses as a 64-bit integer, so
 * no `int`, `long` or `struct timespec` layout reaches DynLex. Paths and
 * text are UTF-8; on Windows paths go through the wide (UTF-16) calls.
 */
#ifndef _WIN32
#define _POSIX_C_SOURCE 200809L
#define _XOPEN_SOURCE 700
#endif

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#ifdef _WIN32
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <direct.h>
#include <process.h>
#else
#include <limits.h>
#include <pthread.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <unistd.h>
#endif

/* 1 on Windows, 0 elsewhere. */
int64_t obs_platform_is_windows(void) {
#ifdef _WIN32
	return 1;
#else
	return 0;
#endif
}

#ifdef _WIN32
/* `text` (UTF-8) as a new UTF-16 string, or NULL; free it after. */
static wchar_t *obs_platform_wide(const char *text) {
	int count = MultiByteToWideChar(CP_UTF8, 0, text, -1, NULL, 0);
	if (count <= 0)
		return NULL;
	wchar_t *wide = (wchar_t *)malloc((size_t)count * sizeof(wchar_t));
	if (wide == NULL)
		return NULL;
	if (MultiByteToWideChar(CP_UTF8, 0, text, -1, wide, count) != count) {
		free(wide);
		return NULL;
	}
	return wide;
}
#endif

/* The folder of the running program, its parts separated by '/', written
 * to `buffer` of `size` bytes with its terminating zero: its length, or -1
 * when it cannot be found or does not fit. */
int64_t obs_platform_executable_folder(char *buffer, int64_t size) {
	if (size <= 1)
		return -1;
#ifdef _WIN32
	static wchar_t widePath[32768];
	DWORD wideLength = GetModuleFileNameW(NULL, widePath, 32768);
	if (wideLength == 0 || wideLength >= 32768)
		return -1;
	int written = WideCharToMultiByte(CP_UTF8, 0, widePath, -1, buffer, (int)size, NULL, NULL);
	if (written <= 0)
		return -1;
	int64_t length = (int64_t)written - 1;
	for (int64_t cursor = 0; cursor < length; cursor++)
		if (buffer[cursor] == '\\')
			buffer[cursor] = '/';
#else
	ssize_t read = readlink("/proc/self/exe", buffer, (size_t)(size - 1));
	if (read <= 0)
		return -1;
	buffer[read] = 0;
	int64_t length = (int64_t)read;
#endif
	int64_t lastSlash = -1;
	for (int64_t cursor = 0; cursor < length; cursor++)
		if (buffer[cursor] == '/')
			lastSlash = cursor;
	if (lastSlash <= 0)
		return -1;
	buffer[lastSlash] = 0;
	return lastSlash;
}

/* Sets environment variable `name` to `value` in this process: 0 when it
 * was set. */
int64_t obs_platform_set_environment(const char *name, const char *value) {
#ifdef _WIN32
	return _putenv_s(name, value) == 0 ? 0 : -1;
#else
	return setenv(name, value, 1) == 0 ? 0 : -1;
#endif
}

/* Seconds since 1970-01-01 UTC. */
int64_t obs_platform_wall_seconds(void) {
#ifdef _WIN32
	return (int64_t)_time64(NULL);
#else
	return (int64_t)time(NULL);
#endif
}

/* A monotonic clock in microseconds, for measuring; -1 when it fails. */
int64_t obs_platform_monotonic_microseconds(void) {
#ifdef _WIN32
	LARGE_INTEGER frequency;
	LARGE_INTEGER count;
	if (!QueryPerformanceFrequency(&frequency) || !QueryPerformanceCounter(&count) || frequency.QuadPart <= 0)
		return -1;
	int64_t whole = count.QuadPart / frequency.QuadPart;
	int64_t rest = count.QuadPart % frequency.QuadPart;
	return whole * 1000000 + (rest * 1000000) / frequency.QuadPart;
#else
	struct timespec reading;
	if (clock_gettime(CLOCK_MONOTONIC, &reading) != 0)
		return -1;
	return (int64_t)reading.tv_sec * 1000000 + (int64_t)reading.tv_nsec / 1000;
#endif
}

/* The calendar of `seconds` (since 1970, UTC), in local time when `local`
 * is not 0, else in UTC, written to `fields`: year, month (1 to 12), day,
 * hour, minute, second. 0 when it was; thread-safe on both platforms. */
int64_t obs_platform_calendar(int64_t seconds, int64_t local, int64_t *fields) {
	struct tm calendar;
	memset(&calendar, 0, sizeof calendar);
#ifdef _WIN32
	__time64_t moment = (__time64_t)seconds;
	errno_t failed = local ? _localtime64_s(&calendar, &moment) : _gmtime64_s(&calendar, &moment);
	if (failed != 0)
		return -1;
#else
	time_t moment = (time_t)seconds;
	struct tm *made = local ? localtime_r(&moment, &calendar) : gmtime_r(&moment, &calendar);
	if (made == NULL)
		return -1;
#endif
	fields[0] = (int64_t)calendar.tm_year + 1900;
	fields[1] = (int64_t)calendar.tm_mon + 1;
	fields[2] = calendar.tm_mday;
	fields[3] = calendar.tm_hour;
	fields[4] = calendar.tm_min;
	fields[5] = calendar.tm_sec;
	return 0;
}

/* Makes directory `path` (its parent must exist): 0 when it was made or
 * already was there. */
int64_t obs_platform_make_directory(const char *path) {
#ifdef _WIN32
	wchar_t *wide = obs_platform_wide(path);
	if (wide == NULL)
		return -1;
	int made = _wmkdir(wide);
	DWORD attributes = GetFileAttributesW(wide);
	free(wide);
	if (made == 0)
		return 0;
	return (attributes != INVALID_FILE_ATTRIBUTES && (attributes & FILE_ATTRIBUTE_DIRECTORY)) ? 0 : -1;
#else
	if (mkdir(path, 0755) == 0)
		return 0;
	struct stat status;
	return (stat(path, &status) == 0 && S_ISDIR(status.st_mode)) ? 0 : -1;
#endif
}

/* `path` made absolute (resolved where it exists), written to `buffer` of
 * `size` bytes with its terminating zero: its length, or -1 when it does
 * not fit or cannot be made. */
int64_t obs_platform_absolute_path(const char *path, char *buffer, int64_t size) {
	if (size <= 0)
		return -1;
#ifdef _WIN32
	wchar_t *wide = obs_platform_wide(path);
	if (wide == NULL)
		return -1;
	wchar_t *full = _wfullpath(NULL, wide, 0);
	free(wide);
	if (full == NULL)
		return -1;
	int written = WideCharToMultiByte(CP_UTF8, 0, full, -1, buffer, (int)size, NULL, NULL);
	free(full);
	if (written <= 0)
		return -1;
	return (int64_t)written - 1;
#else
	char *resolved = realpath(path, NULL);
	if (resolved != NULL) {
		size_t length = strlen(resolved);
		if ((int64_t)length + 1 > size) {
			free(resolved);
			return -1;
		}
		memcpy(buffer, resolved, length + 1);
		free(resolved);
		return (int64_t)length;
	}
	/* Not there (yet): from the working directory, as it is written. */
	size_t pathLength = strlen(path);
	if (path[0] == '/') {
		if ((int64_t)pathLength + 1 > size)
			return -1;
		memcpy(buffer, path, pathLength + 1);
		return (int64_t)pathLength;
	}
	if (getcwd(buffer, (size_t)size) == NULL)
		return -1;
	size_t folderLength = strlen(buffer);
	if ((int64_t)(folderLength + 1 + pathLength + 1) > size)
		return -1;
	buffer[folderLength] = '/';
	memcpy(buffer + folderLength + 1, path, pathLength + 1);
	return (int64_t)(folderLength + 1 + pathLength);
#endif
}

/* The size of open file `handle` in bytes (64-bit on both platforms), its
 * position put back at the start; -1 when it cannot be read. */
int64_t obs_platform_file_size(FILE *handle) {
#ifdef _WIN32
	if (_fseeki64(handle, 0, SEEK_END) != 0)
		return -1;
	int64_t size = (int64_t)_ftelli64(handle);
	if (_fseeki64(handle, 0, SEEK_SET) != 0)
		return -1;
#else
	if (fseeko(handle, 0, SEEK_END) != 0)
		return -1;
	int64_t size = (int64_t)ftello(handle);
	if (fseeko(handle, 0, SEEK_SET) != 0)
		return -1;
#endif
	return size;
}

/* A thread of its own running `entry` with `argument`, its stack
 * `stackBytes` large: its handle is written to `handle`; 0 when it started. */
typedef void *(*obs_platform_entry)(void *);

#ifdef _WIN32
struct obs_platform_start {
	obs_platform_entry entry;
	void *argument;
};

static unsigned __stdcall obs_platform_trampoline(void *startValue) {
	struct obs_platform_start start = *(struct obs_platform_start *)startValue;
	free(startValue);
	start.entry(start.argument);
	return 0;
}
#endif

int64_t obs_platform_start_thread(obs_platform_entry entry, void *argument, int64_t stackBytes, int64_t *handle) {
#ifdef _WIN32
	struct obs_platform_start *start = (struct obs_platform_start *)malloc(sizeof *start);
	if (start == NULL)
		return -1;
	start->entry = entry;
	start->argument = argument;
	uintptr_t made = _beginthreadex(NULL, (unsigned)stackBytes, obs_platform_trampoline, start, 0, NULL);
	if (made == 0) {
		free(start);
		return -1;
	}
	*handle = (int64_t)made;
	return 0;
#else
	pthread_attr_t attributes;
	if (pthread_attr_init(&attributes) != 0)
		return -1;
	pthread_attr_setstacksize(&attributes, (size_t)stackBytes);
	pthread_t thread;
	int failed = pthread_create(&thread, &attributes, entry, argument);
	pthread_attr_destroy(&attributes);
	if (failed != 0)
		return -1;
	*handle = (int64_t)thread;
	return 0;
#endif
}

/* Waits for the thread `handle` names to end and lets it go: 0 when it did. */
int64_t obs_platform_join_thread(int64_t handle) {
#ifdef _WIN32
	HANDLE thread = (HANDLE)(uintptr_t)handle;
	DWORD waited = WaitForSingleObject(thread, INFINITE);
	CloseHandle(thread);
	return waited == WAIT_OBJECT_0 ? 0 : -1;
#else
	return pthread_join((pthread_t)handle, NULL) == 0 ? 0 : -1;
#endif
}

/* HarfBuzz is the native OpenType shaping service. Keep its types behind
 * this bridge: DynLex sees only six signed 64-bit fields per shaped glyph.
 * Atlas faces have a fixed pixel size and remain alive for the atlas lifetime.
 * https://harfbuzz.github.io/harfbuzz-hb-ft.html
 */
#ifndef _WIN32
#include <dlfcn.h>
#endif

struct obs_shaped_glyph {
    int64_t glyph, cluster, advance_x, advance_y, offset_x, offset_y;
};
_Static_assert(sizeof(struct obs_shaped_glyph) == 48, "DynLex shaped glyph ABI");
struct obs_hb_info { uint32_t glyph, mask, cluster, private1, private2; };
struct obs_hb_position { int32_t ax, ay, ox, oy; uint32_t private1; };
struct obs_hb_api {
    void *(*font_create)(void *);
    void (*font_destroy)(void *);
    void *(*buffer_create)(void);
    void (*buffer_destroy)(void *);
    void (*buffer_add)(void *, const char *, int, unsigned, int);
    void (*buffer_guess)(void *);
    void (*shape)(void *, void *, const void *, unsigned);
    struct obs_hb_info *(*infos)(void *, unsigned *);
    struct obs_hb_position *(*positions)(void *, unsigned *);
};
static struct obs_hb_api obs_hb;
static int obs_hb_state;
#ifdef _WIN32
static SRWLOCK obs_shape_lock = SRWLOCK_INIT;
#define OBS_SHAPE_LOCK() AcquireSRWLockExclusive(&obs_shape_lock)
#define OBS_SHAPE_UNLOCK() ReleaseSRWLockExclusive(&obs_shape_lock)
#else
static pthread_mutex_t obs_shape_lock = PTHREAD_MUTEX_INITIALIZER;
#define OBS_SHAPE_LOCK() pthread_mutex_lock(&obs_shape_lock)
#define OBS_SHAPE_UNLOCK() pthread_mutex_unlock(&obs_shape_lock)
#endif

static int obs_hb_load(void) {
    if (obs_hb_state) return obs_hb_state > 0;
#ifdef _WIN32
    HMODULE module = LoadLibraryW(L"harfbuzz.dll");
    if (!module) module = LoadLibraryW(L"harfbuzz-0.dll");
    if (!module) module = LoadLibraryW(L"libharfbuzz-0.dll");
#define OBS_HB_SYMBOL(field, name) do { \
    FARPROC symbol = GetProcAddress(module, name); \
    if (!symbol || sizeof(symbol) != sizeof(obs_hb.field)) return 0; \
    memcpy(&obs_hb.field, &symbol, sizeof(symbol)); \
} while (0)
#else
    void *module = dlopen("libharfbuzz.so.0", RTLD_NOW | RTLD_LOCAL);
#define OBS_HB_SYMBOL(field, name) do { \
    void *symbol = dlsym(module, name); \
    if (!symbol || sizeof(symbol) != sizeof(obs_hb.field)) return 0; \
    memcpy(&obs_hb.field, &symbol, sizeof(symbol)); \
} while (0)
#endif
    obs_hb_state = -1;
    if (!module) return 0;
    OBS_HB_SYMBOL(font_create, "hb_ft_font_create_referenced");
    OBS_HB_SYMBOL(font_destroy, "hb_font_destroy");
    OBS_HB_SYMBOL(buffer_create, "hb_buffer_create");
    OBS_HB_SYMBOL(buffer_destroy, "hb_buffer_destroy");
    OBS_HB_SYMBOL(buffer_add, "hb_buffer_add_utf8");
    OBS_HB_SYMBOL(buffer_guess, "hb_buffer_guess_segment_properties");
    OBS_HB_SYMBOL(shape, "hb_shape");
    OBS_HB_SYMBOL(infos, "hb_buffer_get_glyph_infos");
    OBS_HB_SYMBOL(positions, "hb_buffer_get_glyph_positions");
#undef OBS_HB_SYMBOL
    obs_hb_state = 1;
    return 1;
}

int64_t obs_platform_has_text_shaper(void) {
    OBS_SHAPE_LOCK();
    int available = obs_hb_load();
    OBS_SHAPE_UNLOCK();
    return available;
}

/* A bounded cache avoids reshaping static UI labels on every frame. Hashes
 * select a bucket; face, byte count and bytes must also match exactly. */
#define OBS_SHAPE_SLOTS 2048
#define OBS_SHAPE_BUDGET (8u * 1024u * 1024u)
struct obs_shape_cache_entry {
    void *face;
    uint64_t hash;
    size_t bytes, count;
    char *text;
    struct obs_shaped_glyph *glyphs;
};
static struct obs_shape_cache_entry obs_shape_cache[OBS_SHAPE_SLOTS];
static size_t obs_shape_bytes;

static void obs_shape_drop(struct obs_shape_cache_entry *entry) {
    if (entry->text) obs_shape_bytes -= entry->bytes + 1 + entry->count * sizeof(*entry->glyphs);
    free(entry->text);
    free(entry->glyphs);
    memset(entry, 0, sizeof(*entry));
}

/* NULL output queries the required glyph count; insufficient capacity
 * returns its negative. All glyph positions are FreeType 26.6 pixel units. */
int64_t obs_platform_shape_utf8(void *face, const char *text, int64_t bytes,
                              struct obs_shaped_glyph *output, int64_t capacity) {
    if (!face || !text || bytes < 0 || bytes > 4096 || capacity < 0) return -1;
    if (bytes == 0) return 0;
    uint64_t hash = UINT64_C(14695981039346656037);
    for (int64_t i = 0; i < bytes; ++i) hash = (hash ^ (unsigned char)text[i]) * UINT64_C(1099511628211);
    OBS_SHAPE_LOCK();
    if (!obs_hb_load()) { OBS_SHAPE_UNLOCK(); return -1; }
    struct obs_shape_cache_entry *entry = &obs_shape_cache[hash % OBS_SHAPE_SLOTS];
    if (!(entry->face == face && entry->hash == hash && entry->bytes == (size_t)bytes &&
          entry->text && memcmp(entry->text, text, (size_t)bytes) == 0)) {
        void *font = obs_hb.font_create(face);
        void *buffer = obs_hb.buffer_create();
        if (!font || !buffer) {
            if (font) obs_hb.font_destroy(font);
            if (buffer) obs_hb.buffer_destroy(buffer);
            OBS_SHAPE_UNLOCK(); return -1;
        }
        obs_hb.buffer_add(buffer, text, (int)bytes, 0, (int)bytes);
        obs_hb.buffer_guess(buffer);
        obs_hb.shape(font, buffer, NULL, 0);
        unsigned count = 0, position_count = 0;
        struct obs_hb_info *infos = obs_hb.infos(buffer, &count);
        struct obs_hb_position *positions = obs_hb.positions(buffer, &position_count);
        size_t cost = (size_t)bytes + 1 + (size_t)count * sizeof(struct obs_shaped_glyph);
        if (!infos || !positions || count != position_count || cost > OBS_SHAPE_BUDGET) {
            obs_hb.buffer_destroy(buffer); obs_hb.font_destroy(font);
            OBS_SHAPE_UNLOCK(); return -1;
        }
        char *saved = malloc((size_t)bytes + 1);
        struct obs_shaped_glyph *glyphs = count ? malloc((size_t)count * sizeof(*glyphs)) : NULL;
        if (!saved || (count && !glyphs)) {
            free(saved); free(glyphs);
            obs_hb.buffer_destroy(buffer); obs_hb.font_destroy(font);
            OBS_SHAPE_UNLOCK(); return -1;
        }
        memcpy(saved, text, (size_t)bytes); saved[bytes] = '\0';
        for (unsigned i = 0; i < count; ++i) {
            glyphs[i] = (struct obs_shaped_glyph){infos[i].glyph, infos[i].cluster,
                positions[i].ax, positions[i].ay, positions[i].ox, positions[i].oy};
        }
        obs_hb.buffer_destroy(buffer); obs_hb.font_destroy(font);
        obs_shape_drop(entry);
        if (obs_shape_bytes + cost > OBS_SHAPE_BUDGET) {
            for (unsigned i = 0; i < OBS_SHAPE_SLOTS; ++i) obs_shape_drop(&obs_shape_cache[i]);
        }
        *entry = (struct obs_shape_cache_entry){face, hash, (size_t)bytes, count, saved, glyphs};
        obs_shape_bytes += cost;
    }
    int64_t result = (int64_t)entry->count;
    if (output) {
        if (capacity < result) result = -result;
        else if (entry->count) memcpy(output, entry->glyphs, entry->count * sizeof(*output));
    }
    OBS_SHAPE_UNLOCK();
    return result;
}
