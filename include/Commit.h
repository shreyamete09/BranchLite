#pragma once

#include <string>
#include <map>
#include <iostream>

// Forward declaration for friend class / function
class Repository;

// Represents a snapshot of the repository at a specific point in time.
class Commit {
private:
    std::string id_;
    std::string parent_;
    std::string parent2_; // Second parent for merge commits ("" or "-" if none)
    std::string timestamp_;
    std::string message_;
    std::map<std::string, std::string> files_; // filename -> hash

    // Static member variable: tracks total Commit objects created in memory
    static int commitObjectCount_;

public:
    // Default constructor demonstrating constructor overloading & default arguments
    Commit();

    // Parameterized constructor initializing all commit attributes
    Commit(std::string id, std::string parent, std::string timestamp,
           std::string message, std::map<std::string, std::string> files,
           std::string parent2 = "");

    // Copy constructor demonstrating explicit copy semantics
    Commit(const Commit& other);

    // Destructor
    ~Commit();

    // Static member function to retrieve count of active Commit objects
    static int getCommitObjectCount();

    // Getter and setter methods
    const std::string& getId() const;
    void setId(const std::string& id);
    const std::string& getParent() const;
    const std::string& getParent2() const;
    void setParent2(const std::string& parent2);
    bool isMerge() const;
    const std::string& getTimestamp() const;
    const std::string& getMessage() const;
    const std::map<std::string, std::string>& getFiles() const;

    // Serializes the commit object into the standardized text format
    std::string serialize() const;

    // Deserializes a standardized text representation into a Commit object
    static Commit deserialize(const std::string& id, const std::string& content);

    // Operator Overloading: Equality operator (Binary operator)
    bool operator==(const Commit& other) const;

    // Operator Overloading: Inequality operator (Binary operator)
    bool operator!=(const Commit& other) const;

    // Stream Insertion Operator overloading (Unit 5 requirement)
    friend std::ostream& operator<<(std::ostream& os, const Commit& commit);

    // Stream Extraction Operator overloading (Unit 5 requirement)
    friend std::istream& operator>>(std::istream& is, Commit& commit);

    // Friend class declaration demonstrating friend class concept
    friend class Repository;
};
