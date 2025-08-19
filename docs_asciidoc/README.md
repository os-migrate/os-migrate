# OS Migrate AsciiDoc Documentation

This directory contains the OS Migrate documentation converted from Sphinx/RST to AsciiDoc format.

## Structure

- `index.adoc` - Main documentation entry point
- `user/` - User documentation (installation, usage, troubleshooting)
- `devel/` - Developer documentation (contributing, design, development setup)
- `modules/` - Ansible module documentation
- `roles/` - Ansible role documentation  
- `images/` - Images and diagrams (including PlantUML sources)

## Building Documentation

### Prerequisites

Install AsciiDoctor and required plugins:

```bash
# Install Ruby gems
gem install asciidoctor asciidoctor-pdf asciidoctor-diagram rouge

# Or using bundler (if Gemfile exists)
bundle install
```

### Build Commands

```bash
# Build HTML documentation
make html

# Build PDF documentation  
make pdf

# Build both formats
make all

# Build diagrams only
make diagrams

# Clean build artifacts
make clean
```

### Output

Built documentation will be available in:
- HTML: `_build/html/index.html`
- PDF: `_build/pdf/index.pdf`

## Original Source

This documentation was converted from the original Sphinx/RST format located in `docs/src/`.

## Features

- **AsciiDoc format**: More readable source format than RST
- **PlantUML diagrams**: Automatic diagram generation from source
- **Multiple output formats**: HTML and PDF generation
- **Cross-references**: Maintained document linking
- **Include directives**: Modular documentation structure
- **Syntax highlighting**: Code block highlighting with Rouge
- **Table of contents**: Automatic TOC generation