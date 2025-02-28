#ifndef {{ name_upper }}_HPP
#define {{ name_upper }}_HPP

#include <string>

namespace {{ name }} {

/**
 * A simple class demonstrating basic functionality.
 */
class Calculator {
public:
    Calculator() = default;
    
    /**
     * Add two numbers.
     */
    int add(int a, int b);
    
    /**
     * Get the library name and version.
     */
    static std::string version();
};

} // namespace {{ name }}

#endif /* {{ name_upper }}_HPP */ 