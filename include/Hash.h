#pragma once

#include <string>

namespace Hash {
    // Computes the 64-bit FNV-1a hash of a string and returns it as a 16-character lowercase hex string.
    std::string fnv1a(const std::string& data);
}
