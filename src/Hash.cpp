#include "Hash.h"
#include <cstdint>
#include <iomanip>
#include <sstream>

namespace Hash {

// Computes the 64-bit FNV-1a hash of the given data string.
std::string fnv1a(const std::string& data) {
    constexpr uint64_t FNV_OFFSET_BASIS = 14695981039346656037ULL;
    constexpr uint64_t FNV_PRIME = 1099511628211ULL;

    uint64_t hash = FNV_OFFSET_BASIS;
    for (unsigned char byte : data) {
        hash ^= static_cast<uint64_t>(byte);
        hash *= FNV_PRIME;
    }

    std::ostringstream oss;
    oss << std::hex << std::setfill('0') << std::setw(16) << hash;
    return oss.str();
}

} // namespace Hash
