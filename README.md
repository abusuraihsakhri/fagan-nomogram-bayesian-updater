# Fagan Nomogram Bayesian Updater

### [Open the Live Application →](https://abusuraihsakhri.github.io/fagan-nomogram-bayesian-updater/)

A diagnostic probability calculator implementing Bayes' theorem and the likelihood-ratio form of the Fagan nomogram. Provides a zero-dependency Python core, an offline browser interface, CSV batch processing, and an optional FastAPI service.

## Use the calculator

[Open the live calculator](https://abusuraihsakhri.github.io/fagan-nomogram-bayesian-updater/) or open `index.html` locally. The browser application runs without Pyodide, backend services, API keys, third-party scripts, or network requests. Enter a **pre-test probability in percent**, then either sensitivity/specificity (also in percent) or the likelihood ratio for the observed positive/negative test result. The interface displays the updated probability, likelihood ratio, odds, a graphical nomogram, and a downloadable CSV row.

## Python CLI

Python 3.10 or newer is supported.

```bash
python fagan_nomogram.py single --pretest 30 --sensitivity 90 --specificity 80 --result positive
python fagan_nomogram.py single --pretest 30 --sensitivity 90 --specificity 80 --result negative
python fagan_nomogram.py single --pretest 30 --lr 4.5
python fagan_nomogram.py batch -i sample.csv -o results.csv
```

Alternatively, `python -m pip install -e .` exposes the `fagan-nomogram` console command. The core uses the standard library only.

Batch CSV inputs require `pretest_probability` and either `likelihood_ratio` or both `sensitivity` and `specificity`. Optional `result` values are `positive` or `negative` (default `positive`). Other columns are preserved. Invalid rows raise a line-specific error without overwriting an existing output file. Results include the likelihood ratio, pre/post-test odds, post-test probability, and probability change.

## Method

Let `p` be the pre-test probability expressed as a proportion.

```text
LR+ = sensitivity / (1 - specificity)
LR- = (1 - sensitivity) / specificity
Pre-test odds = p / (1 - p)
Post-test odds = pre-test odds × LR
Post-test probability = post-test odds / (1 + post-test odds)
```

The software uses log-odds for numerical stability, validates finite input percentages, and handles 0%/100% boundaries and theoretically infinite LRs. Undefined combinations return an error. For a 30% prior and a test with 90% sensitivity and 80% specificity, LR+ = 4.5 and LR− = 0.125. Positive and negative results give approximately **65.85%** and **5.08%**, respectively.

The LR method assumes test performance estimates are valid for the population and clinical setting. Sequential test updating is only justified when the relevant conditional dependence between tests is accounted for.

## Optional API and demonstration supervisor

```bash
python -m pip install -e ".[all]"
python cli.py serve --host 127.0.0.1 --port 8000
```

Visit `http://127.0.0.1:8000/` for the calculator and `http://127.0.0.1:8000/docs` for interactive API documentation. POST `/api/calculate` accepts a JSON object with `pretest_probability`, plus either `likelihood_ratio` or `sensitivity` and `specificity`, and an optional `result`.

The separate legacy demonstration system remains accessible through `python cli.py audit`, `batch`, `chat`, `verify-audit`, and the `/api/audit` endpoints. Its threshold rules and mock conversational responses are **not** a clinical validation system, medical alert service, or a substitute for the Bayesian calculator. The demo API is intended for trusted/local environments, not unauthenticated public hosting.

For Docker Compose, set a non-default `AUDIT_SECRET_KEY` in your environment before running `docker compose up --build`. Compose binds the API to the local loopback interface by default. A runtime-generated key is used only when running without a configured key outside Compose; such keys do not persist across restarts.

## Tests and development

```bash
python -m pip install -e ".[all]"
python -m pytest -q
python -m compileall -q fagan_nomogram.py cli.py agents tests
python -m pip check
```

CI tests Python 3.10, 3.11, and 3.12. The source is in `fagan_nomogram.py`; the browser version is in `index.html`; the API and legacy demonstration components are in `agents/` and `cli.py`.

## Privacy, compatibility, and limitations

The static calculator does not upload or persist data. Python/CSV processing takes place on the machine where it runs; exported CSVs may contain user-supplied columns, so avoid real patient identifiers. The optional API is a local service and does not provide production authentication. Modern browsers with JavaScript and SVG support are sufficient; the browser runs ordinary JavaScript rather than Python/Pyodide.

**Educational/research use only.** No diagnostic thresholds, medical recommendations, or regulatory conformance are claimed. Clinical interpretation requires appropriate pre-test assessment and validated test characteristics.

## License

MIT — see [LICENSE](LICENSE).
