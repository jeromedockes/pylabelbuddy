# `labelbuddy`: a small tool for annotating documents

## Installation

`labelbuddy` requires Python 3. Install with:

```
pip3 install labelbuddy
```

`labelbuddy` does not have other dependencies than Python and its standard
library. It needs Python to have been installed with `tkinter` which should be
the case by default, otherwise it can be installed for example on ubuntu with
`apt-get install python-tk`.

## Usage

Once installed `labelbuddy` can be started with:
```
labelbuddy
```

(see `labelbuddy -h` for more options)

### Importing documents

When using `labelbuddy` for the first time, go to the "Import / Export" tab to
import documents and labels.
Documents can be provided either in a `.csv` file or a `.txt` file.

If `.csv`, the file must be a comma-separated-value file with one document per
row. The first column holds the contents of the document. Other columns are not
used by `labelbuddy` but are stored and provided in the `"extra_data"` field of
each document's exported `json` when exporting the annotations.

If `.txt` it must contain one document per line, terminated by `\n`.

### Importing labels

Labels must be imported from a `.json` file of the form

```
[
    {"text": "label name", "background_color": "#00ffaa"},
    {"text": "label 2", "background_color": "#ffaa00"},
    ...
]
```

`"backgroud_color"` is optional and can be changed from within the application.

### Annotating documents

Once documents and labels are imported we can see them in the "Dataset" tab and
select a document to annotate from there, or go directly to the "Annotate" tab.
There, select a snippet of text with the mouse and click on a label to annotate
it. Clicking on an already labelled snipped will select it; then its label can
be changed or it can be removed by clicking "delete".

### Exporting annotations

Back to the "Import / Export" tab, click "Export" and select a file in which
annoations will be written. The file will contain concatenated `json` documents,
one per document in the database, containing the text and annotations.

### Misc

We can switch to a different project by using the "File" menu and selecting a
location where a new database will be created. The path to the database to use
can also be passed as an argument when starting `labelbuddy` from the command
line.

## Reporting bugs

Please report bugs by opening an issue in
[https://github.com/jeromedockes/labelbuddy](https://github.com/jeromedockes/labelbuddy)

## Running the tests

To run the tests we need to `pip3 install pytest`, then from the root of the
package: `pytest tests/`.
