#include "AddCommand.h"
#include "StagingArea.h"
#include "FileUtils.h"
#include "VcsExceptions.h"
#include <iostream>
#include <filesystem>

// Constructs the add command bound to the target repository
AddCommand::AddCommand(Repository& repo)
    : repo_(repo) {}

// Executes the staging of one or more specified files
void AddCommand::execute(const std::vector<std::string>& args) {
    repo_.requireInit();

    if (args.empty()) {
        throw VcsExceptions::InvalidCommandArgsException("Nothing specified, nothing added. Usage: branchlite add <file>...");
    }

    StagingArea stagingArea;
    stagingArea.load(repo_.getIndexPath());

    for (const auto& fileArg : args) {
        if (fileArg == ".") {
            // Stage all root workspace files (excluding binaries and VCS metadata)
            for (const auto& entry : std::filesystem::directory_iterator(repo_.getRootDir())) {
                if (entry.is_regular_file()) {
                    std::string fname = entry.path().filename().string();
                    if (fname != "branchlite.exe" && fname != "ARCHITECTURE.png" && fname[0] != '.') {
                        std::string content = FileUtils::readFile(entry.path());
                        std::string blobHash = repo_.storeBlob(content);
                        stagingArea.add(fname, blobHash);
                    }
                }
            }
            continue;
        }

        std::filesystem::path targetPath(fileArg);

        if (!std::filesystem::exists(targetPath)) {
            throw VcsExceptions::FileNotFoundVcsException(fileArg);
        }

        if (std::filesystem::is_directory(targetPath)) {
            throw VcsExceptions::InvalidCommandArgsException("'" + fileArg + "' is a directory; please specify individual files or '.'");
        }

        std::string content = FileUtils::readFile(targetPath);
        std::string blobHash = repo_.storeBlob(content);

        // Normalize path relative to repository root with portable generic slashes
        std::string normalizedPath = std::filesystem::relative(
            std::filesystem::absolute(targetPath),
            std::filesystem::absolute(repo_.getRootDir())
        ).generic_string();

        stagingArea.add(normalizedPath, blobHash);
    }

    stagingArea.save(repo_.getIndexPath());
}
