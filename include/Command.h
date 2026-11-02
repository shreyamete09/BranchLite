#pragma once

#include <vector>
#include <string>

// Abstract base class representing an executable CLI command in BranchLite.
class Command {
public:
    // Virtual destructor for safe polymorphic destruction of child commands.
    virtual ~Command() = default;

    // Pure virtual method executed when the command is invoked with CLI arguments.
    virtual void execute(const std::vector<std::string>& args) = 0;
};
