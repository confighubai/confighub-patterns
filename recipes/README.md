# recipes

This directory holds compact operator workflow recipes.

Recipes are intentionally:
- short
- procedural
- machine-usable
- tied back to the same pattern/control/framework surfaces this repo already owns

They are **not** a fourth detection taxonomy and they are **not** a replacement
for `confighub-scan` execution docs.

Use them for recurring operational moves like:
- diagnosing a broken governed app
- proving `kubectl` is not the authoritative fix path
- running a governed fix with pre-apply validation
- doing read-only closeout or promotion preflight

Seeded recipes in this repo today:
- `confighub/diagnose-broken-governed-app.yaml`
- `confighub/show-kubectl-is-non-authoritative.yaml`
- `confighub/governed-fix-with-pre-apply-validation.yaml`
- `confighub/read-only-closeout.yaml`

Relationship to the open issues:
- `#15` defines the schema/contract for recipes
- `#14` is the broader recipe-pack buildout that will add more recipe files on
  top of that contract

Recipe files in this directory should validate against:
- `schema/operator-recipe-v1.schema.json`
