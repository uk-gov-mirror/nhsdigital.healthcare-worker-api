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

install-vacuum: # Install vacuum OpenAPI linter @Configuration
	curl -fsSL https://quobix.com/scripts/install_vacuum.sh | sh > /dev/null

lint-specification: # Lint the OpenAPI specification @Quality
	# TODO: Change --fail-severity to 'error' once pre-existing spec issues are resolved (HCW-310)
	vacuum lint -d -s -r .vacuum.yaml -u=false --fail-severity none specification/healthcare-worker-api.yaml

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
