# land — Memory

Destination- and API-specific quirks discovered during past runs. The skill reads this
before writing `pipeline_land.py` so known issues don't repeat.

## Format

`DESTINATION | API or pattern | quirk | fix applied`

## Entries

`BigQuery | any | dataset_name must be a valid BQ dataset id (no hyphens) | replace hyphens with underscores in dataset_name`
