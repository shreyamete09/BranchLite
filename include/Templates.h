#pragma once

#include <iostream>
#include <string>
#include <map>
#include <vector>

// Enumeration for entry change status
enum class FileState {
    Unmodified,
    Modified,
    Added,
    Deleted
};

// Generic container/formatter class template demonstrating class templates with non-type parameter
template <typename T, size_t MaxDisplay = 100>
class ObjectRegistry {
private:
    std::vector<T> items_;
public:
    // Adds an item to the generic registry
    void add(const T& item) {
        if (items_.size() < MaxDisplay) {
            items_.push_back(item);
        }
    }

    // Returns count of items
    size_t size() const {
        return items_.size();
    }

    // Subscript operator overloading for array-like index access
    const T& operator[](size_t index) const {
        return items_.at(index);
    }

    // Friend template function to display generic items
    template <typename U, size_t N>
    friend std::ostream& operator<<(std::ostream& os, const ObjectRegistry<U, N>& reg);
};

template <typename U, size_t N>
std::ostream& operator<<(std::ostream& os, const ObjectRegistry<U, N>& reg) {
    for (size_t i = 0; i < reg.items_.size(); ++i) {
        os << "[" << i << "] " << reg.items_[i] << "\n";
    }
    return os;
}

// Function template demonstrating generic formatting with overloaded template functions
template <typename T>
std::string formatSummary(const std::string& label, const T& value) {
    return label + ": " + std::to_string(value);
}

// Overloaded function template for std::string specialization
template <>
inline std::string formatSummary<std::string>(const std::string& label, const std::string& value) {
    return label + ": " + value;
}
