# lint-info-extractor
(WIP) Extract information about every rust lints

I don't know why... But apparently someone needs this.

## Description

TBD

## Requirement

1. required python packages:

    - mistune (for converting markdown to html)
    
        ```bash
        pip install mistune
        ```

    - beautifulsoup (for parsing converted html)

        ```bash
        pip install beautifulsoup4
        ```

    - translate-api (for translating English into other languages)

        ```bash
        pip install translators
        ```

## Usage

```bash
python3 run.py
```

check `python3 run.py --help` for more usage
