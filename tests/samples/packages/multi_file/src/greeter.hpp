#pragma once
#include <string>

class Greeter {
public:
    Greeter(const std::string& name);
    void greet() const;
    
private:
    std::string name_;
}; 