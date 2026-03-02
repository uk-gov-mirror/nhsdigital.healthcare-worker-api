# This file is for you! Edit it to implement your own hooks (make targets) into
# the project as automated steps to be executed on locally and in the CD pipeline.

include scripts/init.mk

# ==============================================================================

# Example CI/CD targets are: dependencies, build, publish, deploy, clean, etc.

dependencies: # Install dependencies needed to build and test the project @Pipeline
	pip install --user pipx
	pipx install poetry

build:
	poetry install
	poetry build
	poetry run pip install --upgrade -t package dist/*.whl

publish: # Publish the project artefact @Pipeline
	# TODO: Implement the artefact publishing step

deploy: # Deploy the project artefact to the target environment @Pipeline
	# TODO: Implement the artefact deployment step

clean:: # Clean-up project resources (main) @Operations
	# TODO: Implement project resources clean-up step

resolve-specification: # Resolve external $refs in the OpenAPI specification @Quality
	npx -y @redocly/cli bundle specification/healthcare-worker-api.yaml -o specification/healthcare-worker-api.resolved.json

lint-specification: resolve-specification # Lint the OpenAPI specification @Quality
	NO_COLOR=1 npx -y @redocly/cli lint --config redocly.yaml

config:: # Configure development environment (main) @Configuration
	# TODO: Use only 'make' targets that are specific to this project, e.g. you may not need to install Node.js
	make _install-dependencies

# ==============================================================================

${VERBOSE}.SILENT: \
	build \
	clean \
	config \
	dependencies \
	deploy \
