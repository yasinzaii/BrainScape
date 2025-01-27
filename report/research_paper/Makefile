# Makefile for LaTeX Research Paper

# ----------------------- Variables -----------------------
TEX=pdflatex
BIBER=biber
MAIN=main
BUILD_DIR=build
LOGS_DIR=logs

# ----------------------- Phony Targets -----------------------
.PHONY: all pdf clean

# ----------------------- Default Target -----------------------
all: pdf

# ----------------------- Compile PDF -----------------------
pdf:
	@echo "Starting compilation process..."
	@mkdir -p $(BUILD_DIR) $(LOGS_DIR)
	@$(TEX) -interaction=nonstopmode -output-directory=$(BUILD_DIR) -aux-directory=$(BUILD_DIR) $(MAIN).tex > $(LOGS_DIR)/$(MAIN).log 2>&1
	@echo "Running Biber..."
	@$(BIBER) --output-directory=$(BUILD_DIR) $(MAIN) >> $(LOGS_DIR)/$(MAIN).log 2>&1
	@echo "Re-running pdflatex (2nd pass)..."
	@$(TEX) -interaction=nonstopmode -output-directory=$(BUILD_DIR) -aux-directory=$(BUILD_DIR) $(MAIN).tex >> $(LOGS_DIR)/$(MAIN).log 2>&1
	@echo "Re-running pdflatex (3rd pass)..."
	@$(TEX) -interaction=nonstopmode -output-directory=$(BUILD_DIR) -aux-directory=$(BUILD_DIR) $(MAIN).tex >> $(LOGS_DIR)/$(MAIN).log 2>&1
	@echo "Compilation finished. PDF is located in the '$(BUILD_DIR)' directory."


# ----------------------- Clean Generated Files -----------------------
clean:
	@echo "Cleaning up build and log directories..."
	@rm -rf $(BUILD_DIR)/*
	@rm -rf $(LOGS_DIR)/*
	@echo "Clean complete."
