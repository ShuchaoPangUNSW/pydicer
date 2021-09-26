# pydicer: PYthon Dicom Image ConvertER

> ## CAUTION: This tool is currently under development
>
> This README currently provides some advice for contributing to this repository.

Welcome to pydicer, a tool to ease the process of converting DICOM data objects into a format typically used for research purposes. Currently pydicer support conversion to NIfTI format, but it can easily be extended to convert to other formats as well (contributions are welcome).

## Requirements

pydicer currently supports Python 3.7 and 3.8 (better compatibility with newer Python versions will be provided in the future). Make sure you install the library and developer requirements:

```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

## pydicer Pipeline

The pipeline handles fetching of the DICOM data to conversion and preparation of your research dataset. Here are the key steps of the pipeline:

1. **Input**: various classes are provided to fetch DICOM files from the file system, DICOM PACS, TCIA or Orthanc. A TestInput class is also provided to supply test data for development/testing.

2. **Preprocess**: The DICOM files are sorted and linked. Error checking is performed and resolved where possible.

3. **Conversion**: The DICOM files are converted to the target format (NIfTI).

4. **Visualistion**: Visualistions of data converted are prepared to assist with data selection.

5. **Dataset Preparation**: The appropriate files from the converted data are selected to prepare a clean dataset ready for use in your research project!

Running the pipeline is easy. You can run the pipeline using the provided test data with the following command from the command line:

```bash
python -m pydicer.pipeline
```

Alternatively, you may want to prepare a script to have finer control of some functionality you are implementing. The following script will get you started:

```python
from pathlib import Path

from pydicer.input.test import TestInput
from pydicer.pipeline import run

directory = Path("./testdata")
directory.mkdir(exist_ok=True, parents=True)

working_directory = directory.joinpath("working")
working_directory.mkdir(exist_ok=True, parents=True)
output_directory = directory.joinpath("output")
output_directory.mkdir(exist_ok=True, parents=True)

test_input = TestInput(working_directory)

run(test_input, output_directory=output_directory)
```

## Coding standards

Code in pydicer must conform to Python's PEP-8 standards to ensure consistent formatting between contributors. To ensure this, pylint is used to check code conforms to these standards before a Pull Request can be merged. You can run pylint from the command line using the following command:

```bash
pylint pydicer
```

But a better idea is to ensure you are using a Python IDE which supports linting (such as [VSCode](https://code.visualstudio.com/docs/python/linting) or PyCharm). Make sure you resolve all suggestions from pylint before submitting your pull request.

If you're new to using pylint, you may like to [read this guide](https://docs.pylint.org/en/v2.11.1/tutorial.html).

## Automated tests

A test suite is included in pydicer which ensures that code contributed to the repository functions as expected and continues to function as further development takes place. Any code submitted via a pull request should include appropriate automated tests for the new code.

pytest is used as a testing library. Running the tests from the command line is really easy:

```bash
pytest
```

Add your tests to the appropriate file in the `tests/` directory. See the [pytest documention](https://docs.pytest.org/en/6.2.x/getting-started.html) for more information.
