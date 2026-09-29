/*
 * safe_string.c - see safe_string.h.
 */
#include "safe_string.h"

#include <ctype.h>
#include <errno.h>
#include <limits.h>
#include <stdlib.h>
#include <string.h>

size_t str_copy(char *dst, size_t size, const char *src)
{
    size_t len = strlen(src);
    if (size > 0u) {
        size_t n = (len < size - 1u) ? len : size - 1u;
        memcpy(dst, src, n);
        dst[n] = '\0';
    }
    return len;
}

size_t str_append(char *dst, size_t size, const char *src)
{
    size_t used = strlen(dst);          /* caller guarantees dst is terminated within size */
    if (used >= size) {
        return used + strlen(src);
    }
    return used + str_copy(dst + used, size - used, src);
}

int parse_i32(const char *s, int32_t min, int32_t max, int32_t *out)
{
    char *end;
    long v;

    if (s == NULL || *s == '\0' || isspace((unsigned char)*s)) {
        return -1;                      /* strtol would skip leading spaces silently */
    }
    errno = 0;
    v = strtol(s, &end, 10);
    if (end == s || *end != '\0' || errno == ERANGE) {
        return -1;
    }
    if (v < (long)min || v > (long)max) {
        return -1;
    }
    *out = (int32_t)v;
    return 0;
}

int parse_u16(const char *s, uint16_t *out)
{
    int32_t v;
    if (s != NULL && *s == '-') {
        return -1;                      /* strtoul("-1") would wrap to ULONG_MAX without error */
    }
    if (parse_i32(s, 0, UINT16_MAX, &v) != 0) {
        return -1;
    }
    *out = (uint16_t)v;
    return 0;
}
