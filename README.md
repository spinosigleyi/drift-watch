# drift-watch

> CLI tool that detects configuration drift between deployed services and their declared infrastructure-as-code state.

---

## Installation

```bash
pip install drift-watch
```

Or install from source:

```bash
git clone https://github.com/your-org/drift-watch.git && cd drift-watch && pip install .
```

---

## Usage

Run a drift check against your infrastructure state:

```bash
drift-watch check --config drift.yaml --provider aws
```

Compare a specific service against its declared state:

```bash
drift-watch check --service my-api --state ./infra/services/my-api.tf
```

Output a detailed drift report in JSON format:

```bash
drift-watch check --config drift.yaml --output json > report.json
```

**Example output:**

```
[DRIFT DETECTED] my-api
  - Expected instance_type: t3.medium
  + Actual instance_type:   t3.large

  - Expected replicas: 3
  + Actual replicas:   5

2 drift(s) found across 1 service(s).
```

---

## Configuration

Define your services and expected state in a `drift.yaml` file:

```yaml
provider: aws
services:
  - name: my-api
    state_file: ./infra/services/my-api.tf
```

---

## License

MIT © your-org