#pragma once

#include "Command.h"
#include "Repository.h"

// Command to create a new branch or list all existing branches.
class BranchCommand : public Command {
private:
    Repository& repo_;

public:
    // Constructs the branch command bound to the target repository
    explicit BranchCommand(Repository& repo);

    // Executes branch creation or listing
    void execute(const std::vector<std::string>& args) override;
};
