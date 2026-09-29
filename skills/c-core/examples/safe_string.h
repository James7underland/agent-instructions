/*
 * safe_string.h - bounded string copy and checked number parsing (C99).
 */
#ifndef SAFE_STRING_H
#define SAFE_STRING_H

#include <stddef.h>
#include <stdint.h>

/* Copies at most size-1 chars, always terminates when size > 0.
   Returns strlen(src); truncation happened if the result >= size. */
size_t str_copy(char *dst, size_t size, const char *src);

/* Appends src to dst (which holds a terminated string in a buffer of 'size').
   Returns the length the result would have had; truncated if >= size. */
size_t str_append(char *dst, size_t size, const char *src);

/* Strict decimal parsing: the whole string must be a number within range.
   Leading/trailing spaces are not accepted. Return 0 on success, -1 on error. */
int parse_i32(const char *s, int32_t min, int32_t max, int32_t *out);
int parse_u16(const char *s, uint16_t *out);

#endif /* SAFE_STRING_H */
