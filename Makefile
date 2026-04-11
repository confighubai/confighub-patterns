FIRST_WAVE_SOURCE_REPO ?= ../confighub-scan

.PHONY: test-python validate-copy-manifest validate-control-taxonomy validate-control-framework-bundle validate-framework-coverage-report validate-bundle-manifest validate-cross-tool-mapping validate-external-evidence-schema validate-control-projections validate

test-python:
	python3 -m unittest \
		test/test-build-bundle-manifest.py \
		test/test-build-control-taxonomy-summary.py \
		test/test-build-control-framework-bundle.py \
		test/test-build-framework-coverage-report.py \
		test/test-validate-control-projections.py

validate-copy-manifest:
	python3 scripts/build-first-wave-copy-manifest.py --source-repo "$(FIRST_WAVE_SOURCE_REPO)" --check

validate-control-taxonomy:
	python3 scripts/build-control-taxonomy-summary.py --check

validate-control-framework-bundle:
	python3 scripts/build-control-framework-bundle.py --check

validate-framework-coverage-report:
	python3 scripts/build-framework-coverage-report.py --check

validate-bundle-manifest:
	python3 scripts/build-bundle-manifest.py --check

validate-cross-tool-mapping:
	python3 scripts/build-cross-tool-mapping.py --check

validate-external-evidence-schema:
	python3 scripts/validate-external-evidence-schema.py

validate-control-projections:
	python3 scripts/validate-control-projections.py

validate:
	$(MAKE) test-python
	$(MAKE) validate-copy-manifest FIRST_WAVE_SOURCE_REPO="$(FIRST_WAVE_SOURCE_REPO)"
	$(MAKE) validate-control-taxonomy
	$(MAKE) validate-control-framework-bundle
	$(MAKE) validate-framework-coverage-report
	$(MAKE) validate-bundle-manifest
	$(MAKE) validate-cross-tool-mapping
	$(MAKE) validate-external-evidence-schema
	$(MAKE) validate-control-projections
