#include <stdio.h>
#include <string.h>

int main(int argc, char* argv[]) {
    // Get program name
    const char* program_name = argc > 0 ? argv[0] : "{{ name }}";
    
    printf("Hello from %s v%s!\n", program_name, "{{ version }}");
    
    // Print any additional arguments
    if (argc > 1) {
        printf("\nArguments:\n");
        for (int i = 1; i < argc; i++) {
            printf("  %d: %s\n", i, argv[i]);
        }
    }
    
    return 0;
} 