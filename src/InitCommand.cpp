#include "InitCommand.h"
#include <iostream>

// Constructs the init command bound to the target repository.
InitCommand::InitCommand(Repository& repo)
    : repo_(repo) {}

// Executes the repository initialization process.
void InitCommand::execute(const std::vector<std::string>& /*args*/) {
    repo_.init();
    std::cout << "Initialized empty BranchLite repository in "
              << std::filesystem::absolute(repo_.getBranchLiteDir()).generic_string() << "\n";
}
