from src.review.review_store import ReviewStore


def test_review_store_create_and_approve(tmp_path):
    store = ReviewStore(tmp_path)
    draft = store.create_draft(
        etl_spec_draft={"source_table": "main.stg.a", "target_table": "main.dw.b", "primary_key": "id"},
        requirement_summary={"requirement_summary": "test"},
        mapping_rows=[{"source_column": "a", "target_column": "b", "transformation": "a"}],
        source_files={"mapping_path": "mapping.xlsx"},
    )
    loaded = store.get_draft(draft["draft_id"])
    assert loaded is not None
    assert loaded["status"] == "pending_review"

    approved = store.approve_draft(draft["draft_id"])
    assert approved["status"] == "approved"
