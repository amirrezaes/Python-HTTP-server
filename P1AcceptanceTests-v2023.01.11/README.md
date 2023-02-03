# P1 pre-submission acceptance tests

Required software dependencies:

* Python 3.8+
* behave

Acceptance tests formally check your code against the requirements of the spec. They are part of the SCRUM process in software engineering. Generally, code that passed most of these acceptance tests will get a high or full mark.

When we evaluate your submission, we will run a set of less-rigorous tests on a Linux machine.


## HOWTO: set up the acceptance test environment

The following instructions are tested in PicoLab. They are broken down into 4 logical steps:

1. Create a new virtual environment by using Python's built-in `venv` utility
2. Activate the virtual environment
3. Install the `behave` package in the virtual environment
4. Copy P1 acceptance tests into the virtual environment

### Step 1

Open a **(base)** terminal window and keep it open throughout this short tutorial.

Run the following commands in the **(base)** terminal window:

```sh
mkdir GradingEnv
python3 -m venv GradingEnv
```

### Step 2

In the **(base)** terminal window, change into the `GradingEnv` directory and "source" the `bin/activate` script:

```sh
cd GradingEnv/
source bin/activate
```

If done successfully, the terminal prompt should say `(base) (GradingEnv)`.

Just to double check, you may want to run `which python3` in the terminal and confirm that it outputs something in the lines of "/home/.../GradingEnv/bin/python3"

### Step 3

In this step, we will install the `behave` package from the `pip` package manager. `behave` is the framework that our acceptance tests are written in.

In the **(base) (GradingEnv)** terminal window, run

```sh
python3 -m pip install behave
```

To verify that `behave` is working in the `GradingEnv` virtual environment, run `behave --help`

### Step 4

```sh
tar -xvf P1AcceptanceTests.tgz -C GradingEnv/
ls GradingEnv/P1AcceptanceTests/
```


## HOWTO: run the acceptance tests

You will need two terminal windows: H1 and H2.

On **H2**:

1. By using the `cp` command, put `static/small.html` in the same directory as your web server (Don't move the HTML file)
2. Run your web server

On **H1**:

1. Activate the virtual environment
2. Change into the `P1AcceptanceTests` directory
3. Invoke the `behave` command in the virtual environment while your simple web server is running on H2

Command listing on H2:

```sh
cd "/path/to/P1AcceptanceTests/"
cp "GradingEnv/P1/static/small.html" "./"
cp "/path/to/sws.py" "./"
python3 sws.py 0.0.0.0 8080
```

Command listing on H1:

```sh
cd GradingEnv
source bin/activate
cd P1AcceptanceTests
behave -Daddress=N.N.N.N -Dport=8080
```

Replace `N.N.N.N` with the IP address of H2

Replace `8080` with the port of SWS if you used a different port

## Acceptance test parameters

`-Daddress` The IP address of your web server.
<br>Example: `-Daddress=127.0.0.1`

`-Dport` (optional) The port of your web server.
<br>Example: `-Dport=8080`

`-Dendl` (optional) The line ending to be used in HTTP request headers. Acceptable values are `lf` and `crlf` (The default is `lf`).
<br>Example: `-Dendl=lf`

`-i` (optional) Only test specific features that match a regex pattern.
<br>Example: `-i 03_` will run persistency tests only. Feature names can be found under `features/`

`-e` (optional) Don't test specific features that match a regex pattern.
<br>Example: `-e 04_` will skip buffering tests.
