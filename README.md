# AI-Powered ETL QA Accelerator

QA workspace that turns user stories, mapping sheets, and optional KPI SQL into a reviewable draft, then a QA pack (functional test cases, SELECT-only Databricks SQL, markdown report, Excel).

The web UI is the supported way to use this project. CLI commands are optional.

---

## What you must provide

Nothing in this repo will generate tests until Azure OpenAI is configured. Everything else is optional depending on the workflow.

| You need this | When | Where |
|---|---|---|
| **Azure OpenAI** endpoint, key, deployment | Always (draft + test generation) | `.env` |
| **Azure DevOps** org, project, PAT | Importing user stories from ADO | `.env` |
| **Work item IDs** or area/iteration filters | If you do not want the default ADO query | `.env` or Import page |
| **Mapping Excel** | ETL / hybrid stories (source-to-target columns) | ADO attachment, Upload tab, or Build page |
| **Requirement / BRD** (`.txt` / `.docx` / `.pdf`) | File-based ETL without ADO | Import → File Upload |
| **UI screenshots** (optional) | Richer functional/UI test cases | Import / Build uploaders |
| **KPI logic document** (optional) | Developer SQL for UI KPI checks | Import or Review → KPI Logic Document |
| **Azure Databricks** host, warehouse path, token | Only if you tick **Execute SQL on Azure Databricks** | `.env` |

Azure OpenAI is **required**. Databricks is **not** required to generate SQL; leave execution unchecked if tables are not available.

---

## One-time setup

1. Open PowerShell in this folder.
2. Run:
   ```powershell
   .\setup.ps1
   ```
3. Copy `.env.example` to `.env` if `.env` does not exist.
4. Fill `.env` (see [Environment variables](#environment-variables)).
5. Start the UI:
   ```powershell
   .\run_ui.ps1
   ```
6. Open the URL Streamlit prints (usually `http://localhost:8501`).

Confirm connections on **Settings** (Azure OpenAI, Azure DevOps, Azure Databricks).

---

## Daily use — sidebar workflow

Use the left menu in this order for a full run:

| Menu | What you do |
|---|---|
| **Home** | Connection cards, counts, quick actions, recent runs |
| **Import** | Pull ADO stories, upload files, or enter a story manually. Optional KPI SQL upload |
| **Build Spec** | Create a draft from the latest ADO import, uploads, samples, or a JSON spec |
| **Review** | Read gaps, mapping analysis (VR rules / risk), edit ETL JSON if present, attach KPI logic |
| **Generate** | Approve and generate the QA pack (functional cases and/or SQL tests) |
| **Exports** | Download `qa_validation_pack.md` and `qa_test_cases.xlsx` |
| **Test Cases** | Browse generated cases |
| **Spec Library** | Approved ETL specs |
| **History** | Past runs |
| **Settings** | Health checks and live connection tests |

### Workflow modes

The app picks a mode automatically (you can override on **Build Spec**):

| Mode | When | What gets generated |
|---|---|---|
| **functional** | UI/story work, no usable ETL mapping | Manual/functional test cases. No ETL spec required |
| **etl** | Mapping + data pipeline requirements | ETL spec, VR mapping analysis, SQL validation tests |
| **hybrid** | UI story **and** mapping/KPI SQL | Functional cases plus SQL (KPI and/or mapping) |

A functional draft stores an empty ETL spec on purpose. You can still generate a QA pack; SQL table tests are skipped until a mapping (or KPI document) is attached.

### Option A — Azure DevOps (typical)

1. **Import** → **Azure DevOps** tab.
2. Leave org/project empty to use `.env`, or override for one run.
3. Enter work item ID(s) if you are not using `.env` filters.
4. **Test Connection**, then **Import User Stories**.
5. Download requirements/stories if needed, then **Build Draft from this Import** (or open **Build Spec**).
6. On **Build Spec**, choose **Latest ADO import**, set workflow mode (`auto` is fine), generate the draft.
7. **Review**: check gaps, Mapping Analysis (if ETL), KPI upload if needed.
8. **Generate**: Approve & Generate QA Pack. Keep Databricks execution **off** unless target tables exist.
9. **Exports**: download the report and Excel. Close `output/qa_test_cases.xlsx` in Excel before regenerating.

### Option B — Files only

1. **Import** → **File Upload**: requirement document, mapping Excel (ETL), optional screenshots.
2. **Save Uploads & Go to Build**, or open **Build Spec** → **Uploaded files**.
3. Review → Generate → Exports (same as above).

### Option C — Manual story

**Import** → **Manual Entry**: title, description, acceptance criteria. Builds a functional draft.

### Option D — Sample demo

```powershell
.\run_sample.ps1
```

Or **Build Spec** → **Sample files**. Uses `samples/requirements/sample_brd.txt` and `samples/mappings/sample_mapping.xlsx`.

---

## KPI logic documents

On **Import** or **Review**, upload developer SQL (`.sql`, `.xlsx`, `.txt`, `.docx`, `.pdf`, `.md`, `.json`).

The KPI agent rewrites each query to **SELECT-only Databricks SQL**. Use this for UI KPI validation when there is no warehouse mapping sheet. Attaching KPI logic to a functional draft makes the run **hybrid**.

---

## Mapping Excel (ETL)

Use `samples/templates/mapping_template.xlsx`, a `.csv` with the same headers, a Word STM document (`.docx`), or the sample sheet. Headers are flexible (`Source Table` / `SOURCE_TABLE` / `Src Table`).

Word mapping documents (for example CoE “Data Warehouse Documentation”) are accepted when they contain **Source to Target Mapping (STM)** tables. Typical layout:

- Heading 1: Source to Target Mapping (STM) & Pseudo Code (architecture chapters are skipped)
- Heading 2: target entity (Person Account, Positions, …)
- STM table columns: Target Column; Source Column, Source Column & Logic, or Source Column / Logic; Source Table(s); Original Source
- Pseudo Code under each entity is kept with that table and passed to the Mapping Agent

Tables such as environments, lakehouses, tech stack, and orchestrators are not ingested. The parser writes a normalized Excel next to the Word file and uses those rows for QA. Upload the `.docx` on **Import** or **Build Spec** as the mapping file. A sample is `samples/mappings/sample_stm_mapping.docx`.

To generate a mapping workbook from live Azure Databricks Unity Catalog:

```powershell
.\.venv\Scripts\python.exe scripts\export_catalog_mapping.py
```

This writes `samples/mappings/databricks_catalog_mapping.xlsx` (Summary, Mapping, Inventory, Gaps). Upload the **Mapping** sheet on Import / Build Spec. Review inferred DIRECT/CAST rows before treating them as approved mappings. `.env` `DATABRICKS_CATALOG=main` is ignored if that catalog does not exist; the script reads all Unity Catalogs except `system`, `samples`, and `hive_metastore`.

Recommended columns (CoE template):

| Source Database | Source Schema | Source Table | Source Column | Source Data Type | Transformation | Target Database | Target Schema | Target Table | Target Column | Target Data Type | Business Rule | Nullable | Primary Key | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|

Minimum required: **Source Column** and **Target Column**.

The Mapping Agent then:

- Builds canonical mapping JSON (`MAP-001`, …)
- Classifies transformations (DIRECT, STRING, LOOKUP, SCD, …)
- Assigns **VR01–VR26** validation rules
- Scores risk and lists gaps
- Hands approved rules to the SQL Agent (`mapping_id` + `rule_id`)

On **Review** and **Generate**, download Mapping Agent output as **JSON** or **Excel** (choose the format, then download). Excel includes Mapping Rows, Canonical Mappings, Analysis, Gaps, ETL Spec mapping, and Pseudo Code.

Optional platform metadata (types / PK / nullability) can be supplied as JSON:

```env
FABRIC_METADATA_PATH=samples/metadata/fabric_columns.json
```

---

## Azure DevOps

### `.env`

```env
AZURE_DEVOPS_ORG=your-organization-name
AZURE_DEVOPS_PROJECT=your-project-name
AZURE_DEVOPS_PAT=your-personal-access-token
```

| Variable | How to find it |
|---|---|
| `AZURE_DEVOPS_ORG` | `https://dev.azure.com/<ORG>/...` |
| `AZURE_DEVOPS_PROJECT` | Project that holds the stories |
| `AZURE_DEVOPS_PAT` | PAT with **Work Items (Read)** |

Optional:

```env
AZURE_DEVOPS_AREA_PATH=YourProject\ETL
AZURE_DEVOPS_ITERATION_PATH=YourProject\Sprint 1
AZURE_DEVOPS_WORK_ITEM_IDS=12345,12346
AZURE_DEVOPS_WORK_ITEM_TYPES=User Story
AZURE_DEVOPS_MAX_STORIES=25
```

Use **either** specific work item IDs **or** area/iteration filters.

### What is imported

Title, description, acceptance criteria, tags, area/iteration, and an attached mapping `.xlsx` if present.

```
imports/ado/<import-id>/
├── requirements_from_ado.txt
├── user_stories.json
├── mapping.xlsx                 ← only if attached
└── import_metadata.json
imports/ado/latest.json
```

Mapping resolution: ADO attachment → UI upload → `samples/mappings/sample_mapping.xlsx` (ETL fallback). Prefer attaching the real mapping to the story.

---

## Environment variables

Copy `.env.example` → `.env`.

### Azure OpenAI (required)

```env
AZURE_OPENAI_ENDPOINT=https://your-resource.cognitiveservices.azure.com/
AZURE_OPENAI_API_KEY=your-key
AZURE_OPENAI_DEPLOYMENT=gpt-5.1
AZURE_OPENAI_API_VERSION=2025-04-01-preview
AZURE_OPENAI_MODEL=gpt-5.1
```

### Azure Databricks (only for live SQL execution)

```env
DATABRICKS_SERVER_HOSTNAME=adb-xxxx.xx.azuredatabricks.net
DATABRICKS_HTTP_PATH=/sql/1.0/warehouses/your-warehouse-id
DATABRICKS_ACCESS_TOKEN=your-token
DATABRICKS_CATALOG=main
DATABRICKS_SOURCE_SCHEMA=stg
DATABRICKS_TARGET_SCHEMA=dw
```

### Azure DevOps

See above.

### Optional

```env
FABRIC_METADATA_PATH=samples/metadata/fabric_columns.json
```

---

## Outputs

Generated files **overwrite** the previous pack (not timestamped). Close Excel before regenerate.

| Output | Location |
|---|---|
| QA report | `output/qa_validation_pack.md` |
| Test cases | `output/qa_test_cases.xlsx` (includes Mapping Analysis / Gaps sheets when ETL) |
| Run log | `runs/<run-id>.json` |
| Approved specs | `metadata/qa_accelerator.db` |
| Drafts | `review/drafts/<draft-id>.json` |
| ADO imports | `imports/ado/<import-id>/` |
| KPI JSON | `uploads/kpi_logic/` |

---

## CLI (optional)

Activate the venv or call `.\.venv\Scripts\python.exe`.

```powershell
python main.py ado-test
python main.py ado-import
python main.py ado-import --build
python main.py build --from-ado
python main.py build --use-samples
python main.py build --mapping samples/mappings/sample_mapping.xlsx --requirements samples/requirements/sample_brd.txt
python main.py review --draft-id <draft-id>
python main.py approve --draft-id <draft-id> --no-execute
python main.py validate --spec samples/specs/sample_etl_spec.json --no-execute
python main.py list-specs
python main.py list-drafts
```

---

## Sample files

| File | Purpose |
|---|---|
| `samples/requirements/sample_brd.txt` | Sample BRD |
| `samples/mappings/sample_mapping.xlsx` | Sample mapping (full CoE headers) |
| `samples/mappings/sample_stm_mapping.docx` | Sample Word STM mapping document |
| `samples/templates/mapping_template.xlsx` | Empty mapping template |
| `samples/metadata/fabric_columns.json` | Example column metadata for enrichment |
| `samples/specs/sample_etl_spec.json` | Direct JSON spec |

---

## Agents and SQL pipeline

| Agent | Role |
|---|---|
| Requirement Agent | Facts, business rules, gaps from BRD/ADO |
| Mapping Agent | ETL spec + canonical mappings + VR01–VR26, risk, gaps |
| KPI SQL Agent | Normalize developer KPI SQL to Databricks SELECT |
| SQL Agent | SELECT-only validation SQL (what vs how: mapping/KPI say what to test) |
| Test Case Agent | Functional + data test cases |
| Reporting Agent | Markdown pack + execution evidence |

Approved ETL specs run:

`analyze_spec → generate_sql_tests → generate_test_cases → safety_check → execute_on_adb → format_qa_report`

Safety: **SELECT** / **WITH … SELECT** only. Blocked: INSERT, UPDATE, DELETE, MERGE, DROP, TRUNCATE, ALTER, CREATE, GRANT, REVOKE, EXEC.

---

## Tests

```powershell
.\.venv\Scripts\python.exe -m pytest
```

---

## Troubleshooting

| Issue | Fix |
|---|---|
| `source_table` / `target_table` / `primary_key` missing | Functional draft with empty spec — generate without ETL SQL, or add a mapping and rebuild as ETL/hybrid |
| Azure OpenAI error | Check endpoint, key, and `AZURE_OPENAI_DEPLOYMENT` |
| ADO connection failed | Org, project, PAT (Work Items Read) |
| ADO import returns 0 stories | Work item IDs, area path, iteration, work item type |
| Databricks table not found | Leave execution unchecked, or point at real Unity Catalog tables |
| Cannot write Excel | Close `output/qa_test_cases.xlsx` |
| No mapping Excel | Attach `.xlsx` to the ADO story, upload on Import/Build, or use the sample |
| `uv trampoline failed` | Re-run `.\setup.ps1` |
| UI looks huge / clipped | Use Chrome zoom (Ctrl + `-`). Do not rely on CSS page zoom |

---

## Project layout

```
app/                      Streamlit UI
  components/             Shared widgets (sidebar, theme, uploads)
  views/                  One module per sidebar page
  state/                  Session helpers
src/
  agents/                 Requirement, Mapping, KPI, SQL, Test Case, Reporting
  graph/                  LangGraph state, nodes, SQL pipeline
  integrations/           Azure DevOps, Databricks
  mapping/                VR library, classifier, gaps, risk, Fabric enrich
  models/                 Pydantic models
  parsers/                Documents, mapping Excel, KPI logic
  prompts/                Per-agent prompts
  services/               Shared UI + CLI workflow
  exporters/              Markdown / Excel / ZIP
  inputs/                 JSON spec loader
  metadata/               Local spec store
  review/                 Draft store
  utils/                  LLM JSON, SQL safety, run logger
samples/                  BRD, mapping, KPI, ETL spec, templates
scripts/                  Sample-file generator
tests/
main.py                   CLI
setup.ps1 / run_ui.ps1
```

Runtime folders created while you work (`imports/`, `output/`, `review/`, `runs/`, `uploads/`, `metadata/`) are gitignored.
