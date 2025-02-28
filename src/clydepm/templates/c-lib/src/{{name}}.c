#include "{{ name }}/{{ name }}.h"

int {{ name }}_add(int a, int b) {
    return a + b;
}

const char* {{ name }}_version(void) {
    static const char version[] = "{{ name }} version {{ version }}";
    return version;
} 