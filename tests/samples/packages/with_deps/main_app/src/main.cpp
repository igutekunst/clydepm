#include <iostream>
#include <formatter/formatter.hpp>

int main() {
    std::string name = "World";
    std::string year = "2024";
    
    // Use our formatter library
    std::string message = formatter::format("Hello, {}! Welcome to {}.", name, year);
    std::cout << message << std::endl;
    
    return 0;
} 