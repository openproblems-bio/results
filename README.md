# Benchmark results

One folder per task, one sub-folder per release:

```
data/results/<task>/<version>/
  task_info.json
  dataset_info.json
  method_info.json
  metric_info.json
  quality_control.json
  results.json
  config.json        # optional, maintainer-editable (see below)
```

The six `*_info` / `results` / `quality_control` files are the results_v4 outputs.

## config.json (optional)

A maintainer-editable file that lives next to the results, so task owners can tune how
a release is presented without changing the website source. Everything in it is
optional. It is not schema-validated yet; unknown method/metric ids in a preset are
ignored, and a malformed silence pattern silences nothing.

```jsonc
{
  // QC findings that are expected for this release and should be hidden from the
  // headline counts and the default list. They stay visible under a "silenced
  // (expected)" disclosure together with the reason.
  "qc_silenced": [
    {
      "category": "Raw results",                 // optional, matched exactly
      "label": "Metric 'hvg_overlap' %missing",  // exact label match
      // "labelPattern": "%missing$",            // alternative: regex source
      "reason": "Why this finding is expected for this task."
    }
  ],

  // Named leaderboard presets. Each one is a starting point that subsets the table
  // and (optionally) overrides display settings. The user can still tweak filters
  // afterwards (the preset then shows as "custom").
  "presets": [
    {
      "name": "all",                 // id
      "label": "All results",        // shown on the button
      "description": "What this view represents.",
      "default": true,               // selected on first load
      "paramsets": "all"             // "all" or any of ["best","median","worst"]
    },
    {
      "name": "graph",
      "label": "Graph metrics",
      "description": "...",
      "metrics": ["graph_connectivity", "ari"],  // metric ids; omit = all metrics
      "methods": ["combat", "harmony"],          // method ids; omit = all methods
      "datasets": ["pancreas"],                  // dataset ids; omit = all datasets
      // any display setting may also be overridden:
      "colorByRank": true,
      "scaleColumn": false,
      "showResources": true,
      "showControls": true,
      "density": "compact"           // "compact" | "cozy" | "comfortable"
    }
  ]
}
```
