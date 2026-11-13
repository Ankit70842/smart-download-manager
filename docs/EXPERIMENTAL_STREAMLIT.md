# Experimental Streamlit frontend

`app.py` is an experimental, unsupported alternative to `web_app.py`. It is not
the running UI and is outside the verified initial release surface. It has only
been syntax-checked; there is no tested dependency lock or complete transitive
vulnerability audit. Use the standard-library HTTP interface for supported usage.

## Optional setup

Use Python 3.12 or newer from python.org in a new environment. Do not reuse a
virtual environment created by MSYS2 Python.

```powershell
# Replace with your standard python.org interpreter path:
& "C:\Path\To\Python312\python.exe" -m venv .venv-streamlit
.\.venv-streamlit\Scripts\python.exe -m pip install -r requirements.txt
.\.venv-streamlit\Scripts\python.exe -m streamlit run app.py --server.address 127.0.0.1
```

On Linux/macOS use `python3 -m venv .venv-streamlit` and then
`.venv-streamlit/bin/python` for subsequent commands. In this frontend, the apply
button is named **Apply organization**, rather than **Apply these moves**.

## Observed installation failure

During implementation, PATH selected MSYS2 Python 3.12.7 with platform
`mingw_x86_64_ucrt_gnu`. The attempted environment contained pip but no Streamlit.
Installation first hit sandbox socket restrictions, then an elevated attempt
timed out downloading NumPy source. No compiler failure was actually observed.

MSYS2's [official Python documentation](https://www.msys2.org/docs/python/) explains
that its C extensions are incompatible with standard CPython wheels. This explains
why pip selected source packages. Standard CPython was separately available on the
review machine, but it was not the `python` on PATH.

The incomplete MSYS2 environment and failed downloads were removed during
publication preparation. These commands are optional instructions, not a claim
that Streamlit was successfully installed or verified.
