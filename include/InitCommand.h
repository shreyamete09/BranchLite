#pragma once

#include "Command.h"
#include "Repository.h"

// Command to initialize a new BranchLite repository.
class InitCommand : public Command {
private:
    Repository& repo_;

public:
    // Constructs the init command bound to the target repository.
    explicit InitCommand(Repository& repo);

    // Executes the repository initialization process.
    void execute(const std::vector<std::string>& args) override;
};
