#ifndef {{ name_upper }}_H
#define {{ name_upper }}_H

#ifdef __cplusplus
extern "C" {
#endif

#include <stddef.h>

/**
 * A simple calculator demonstrating basic functionality.
 */

/**
 * Add two numbers.
 */
int {{ name }}_add(int a, int b);

/**
 * Get the library name and version.
 * Returns a statically allocated string that should not be freed.
 */
const char* {{ name }}_version(void);

#ifdef __cplusplus
}
#endif

#endif /* {{ name_upper }}_H */ 