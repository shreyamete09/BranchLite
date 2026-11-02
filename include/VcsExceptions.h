#pragma once

#include <exception>
#include <string>

namespace VcsExceptions {

// Base exception for all BranchLite exceptions demonstrating exception inheritance.
class VcsException : public std::exception {
protected:
    std::string message_;
public:
    explicit VcsException(std::string msg) : message_(std::move(msg)) {}
    const char* what() const noexcept override {
        return message_.c_str();
    }
};

// Thrown when an operation is executed outside an initialized repository.
class RepositoryNotInitializedException : public VcsException {
public:
    RepositoryNotInitializedException()
        : VcsException("fatal: not a branchlite repository (or any of the parent directories): .branchlite") {}
};

// Thrown when trying to initialize a repository that already exists.
class RepositoryAlreadyExistsException : public VcsException {
public:
    RepositoryAlreadyExistsException()
        : VcsException("fatal: BranchLite repository already exists.") {}
};

// Thrown when a specified file path or revision is not found.
class FileNotFoundVcsException : public VcsException {
public:
    explicit FileNotFoundVcsException(const std::string& path)
        : VcsException("fatal: pathspec '" + path + "' did not match any files") {}
};

// Thrown when a commit is attempted with an empty staging area.
class EmptyStagingAreaException : public VcsException {
public:
    EmptyStagingAreaException()
        : VcsException("fatal: no changes added to commit (use \"branchlite add\")") {}
};

// Thrown when command-line arguments are invalid or missing.
class InvalidCommandArgsException : public VcsException {
public:
    explicit InvalidCommandArgsException(const std::string& msg)
        : VcsException("fatal: " + msg) {}
};

} // namespace VcsExceptions
