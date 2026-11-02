#pragma once

#include "Command.h"
#include "Repository.h"

// Command to stage files into the index and store content blobs in the object database.
class AddCommand : public Command {
private:
    Repository& repo_;

public:
    // Constructs the add command bound to the target repository.
    explicit AddCommand(Repository& repo);

    // Executes the staging of one or more specified files.
    void execute(const std::vector<std::string>& args) override;
};
