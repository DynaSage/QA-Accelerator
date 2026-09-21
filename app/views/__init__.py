from . import (
    build_spec,
    generate_qa,
    home,
    import_stories,
    results_exports,
    review_draft,
    run_history,
    settings,
    spec_library,
    test_cases,
)

PAGES = {
    "Home": home.render,
    "Import": import_stories.render,
    "Build ETL Spec": build_spec.render,
    "Review Draft": review_draft.render,
    "Generate QA Pack": generate_qa.render,
    "Results & Exports": results_exports.render,
    "Test Case Explorer": test_cases.render,
    "Spec Library": spec_library.render,
    "Run History": run_history.render,
    "Settings": settings.render,
}
