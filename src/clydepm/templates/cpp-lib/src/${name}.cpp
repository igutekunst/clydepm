#include "${name}/${name}.hpp"

namespace ${name} {

int Calculator::add(int a, int b) {
    return a + b;
}

std::string Calculator::version() {
    return "${name} version ${version}";
}

} // namespace ${name} 