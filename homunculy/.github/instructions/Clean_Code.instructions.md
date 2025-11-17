---
applyTo: '**'
---
Provide project context and coding guidelines that AI should follow when generating code, answering questions, or reviewing changes.

# Homunculy AI Assistant Coding Guidelines

## Project Context
Homunculy is a FastAPI-based AI agent management system that follows Clean Architecture principles. The system provides REST and GraphQL APIs for creating, managing, and interacting with AI agents powered by PydanticAI and OpenAI's models.

## Core Principles

### 1. Clean Code Principles
- **Meaningful Names**: Use descriptive, intention-revealing names for variables, functions, classes, and modules
- **Single Responsibility**: Each function, class, or module should have one reason to change
- **DRY (Don't Repeat Yourself)**: Eliminate code duplication through abstraction
- **Boy Scout Rule**: Always leave code cleaner than you found it
- **Comments**: Write code that explains itself; use comments only when necessary
- **Small Functions**: Functions should be small and do one thing well
- **Error Handling**: Fail fast and provide meaningful error messages

### 2. SOLID Principles

#### Single Responsibility Principle (SRP)
- Each class should have only one reason to change
- Separate concerns into different classes/modules
- Example: Controllers handle HTTP requests, Use Cases contain business logic, Repositories handle data persistence

#### Open-Closed Principle (OCP)
- Software entities should be open for extension but closed for modification
- Use inheritance, composition, and interfaces to extend behavior
- Example: Add new agent providers without modifying existing code

#### Liskov Substitution Principle (LSP)
- Subtypes must be substitutable for their base types
- Derived classes should not break the contracts of base classes
- Example: All repository implementations should work interchangeably

#### Interface Segregation Principle (ISP)
- Clients should not be forced to depend on interfaces they don't use
- Create specific interfaces rather than general-purpose ones
- Example: Separate read and write operations into different interfaces

#### Dependency Inversion Principle (DIP)
- High-level modules should not depend on low-level modules
- Both should depend on abstractions
- Example: Use Cases depend on Repository interfaces, not concrete implementations

### 3. Clean Architecture

#### Layer Structure
```
├── Domain Layer (Entities/Models)
│   ├── Business rules and entities
│   ├── No external dependencies
│   └── Pure Python classes
├── Use Cases Layer (Application Logic)
│   ├── Application-specific business rules
│   ├── Orchestrates domain entities
│   └── Depends only on domain layer
├── Interface Adapters Layer (Controllers/Repositories)
│   ├── Converts data between layers
│   ├── Controllers handle HTTP requests
│   └── Repositories handle data persistence
└── Infrastructure Layer (External Concerns)
    ├── Database connections
    ├── External APIs
    ├── Frameworks and drivers
    └── Configuration
```

#### Dependency Rule
- Inner layers should not depend on outer layers
- Dependencies point inward only
- Use dependency injection to invert dependencies

#### Key Patterns
- **Dependency Injection**: Inject dependencies rather than creating them
- **Repository Pattern**: Abstract data access behind interfaces
- **Factory Pattern**: Create objects without specifying exact classes
- **Adapter Pattern**: Convert between incompatible interfaces

## Coding Standards

### Python-Specific Guidelines
- **Type Hints**: Use comprehensive type hints for all function parameters and return values
- **Docstrings**: Use Google-style docstrings for all public functions and classes
- **PEP 8**: Follow Python Enhancement Proposal 8 for code style
- **Async/Await**: Use async patterns consistently for I/O operations
- **Context Managers**: Use `async with` for resource management

### Naming Conventions
- **Classes**: PascalCase (e.g., `AgentConfiguration`, `PydanticAILLMClient`)
- **Functions/Methods**: snake_case (e.g., `create_agent`, `validate_request`)
- **Variables**: snake_case (e.g., `agent_config`, `user_input`)
- **Constants**: UPPER_SNAKE_CASE (e.g., `DEFAULT_MODEL`, `MAX_TOKENS`)
- **Modules**: snake_case (e.g., `ai_agent_router`, `database_settings`)

### File Organization
- **One Class Per File**: Each class should be in its own file
- **Related Functions**: Group related functions in the same module
- **Import Order**: Standard library, third-party, local imports (separated by blank lines)
- **Relative Imports**: Use relative imports within packages

### Error Handling
- **Custom Exceptions**: Create specific exception types for different error conditions
- **Meaningful Messages**: Provide clear, actionable error messages
- **Logging**: Use appropriate log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- **Graceful Degradation**: Handle failures gracefully without crashing the system

### Testing
- **Unit Tests**: Test individual functions and classes in isolation
- **Integration Tests**: Test interactions between components
- **Test Coverage**: Aim for high test coverage (>80%)
- **Test Naming**: Use descriptive test names that explain what is being tested

### Documentation
- **README**: Comprehensive project documentation
- **API Documentation**: Auto-generated from docstrings using FastAPI
- **Code Comments**: Explain complex business logic, not obvious code
- **Commit Messages**: Clear, descriptive commit messages following conventional commits

## AI Assistant Guidelines

### When Generating Code
1. **Follow Architecture**: Always adhere to Clean Architecture principles
2. **SOLID First**: Ensure all code follows SOLID principles
3. **Clean Code**: Write readable, maintainable code
4. **Type Safety**: Use proper type hints throughout
5. **Error Handling**: Implement comprehensive error handling
6. **Testing**: Consider testability when writing code

### When Reviewing Code
1. **Architecture Compliance**: Ensure code follows Clean Architecture
2. **SOLID Violations**: Identify and fix SOLID principle violations
3. **Code Smells**: Detect and eliminate code smells
4. **Performance**: Consider performance implications
5. **Security**: Check for security vulnerabilities
6. **Maintainability**: Assess long-term maintainability

### When Answering Questions
1. **Context Aware**: Consider the architectural context
2. **Principles Based**: Base answers on established principles
3. **Practical**: Provide actionable, implementable solutions
4. **Educational**: Explain reasoning and principles
5. **Consistent**: Maintain consistency with existing codebase

### Code Quality Checklist
- [ ] Follows Clean Architecture layers
- [ ] Adheres to SOLID principles
- [ ] Uses meaningful names
- [ ] Has proper type hints
- [ ] Includes comprehensive error handling
- [ ] Has appropriate logging
- [ ] Is well-documented
- [ ] Is testable
- [ ] Follows established patterns
- [ ] Passes all tests