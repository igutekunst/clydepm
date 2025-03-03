#include <formatter/formatter.hpp>

namespace formatter {

std::string format(const std::string& fmt, const std::string& arg1) {
    size_t pos = fmt.find("{}");
    if (pos == std::string::npos) {
        return fmt;
    }
    return fmt.substr(0, pos) + arg1 + fmt.substr(pos + 2);
}

std::string format(const std::string& fmt, const std::string& arg1, const std::string& arg2) {
    std::string result = fmt;
    
    // Replace first {}
    size_t pos = result.find("{}");
    if (pos != std::string::npos) {
        result = result.substr(0, pos) + arg1 + result.substr(pos + 2);
    }
    
    // Replace second {}
    pos = result.find("{}");
    if (pos != std::string::npos) {
        result = result.substr(0, pos) + arg2 + result.substr(pos + 2);
    }
    
    return result;
}

} // namespace formatter 