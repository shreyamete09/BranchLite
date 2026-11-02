#pragma once

#include "Command.h"
#include "Repository.h"

// Command to reset the current branch tip back by one commit while preserving working directory files.
class ResetCommand : public Command {
private:
    Repository& repo_;

public:
    // Constructs the reset command bound to the target repository
    explicit ResetCommand(Repository& repo);

    // Executes the undo/reset operation
    void execute(const std::vector<std::string>& args) override;
};
