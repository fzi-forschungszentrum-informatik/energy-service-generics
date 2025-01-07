# Energy Service Generics

A framework for the implementation of web-services (as well as the corresponding clients) that provide forecasting and optimization algorithms for energy management applications at scale.

## Rationale

Energy Management Systems (EMSs), in a sense of software computing optimized operational schedules and executing these on devices, have been demonstrated to be capable of reducing energy demand, lowering $CO_2$ emissions and/or unlocking flexibility. However, in order to have a practical impact to mitigate global warming EMSs will be required in large scales, like e.g. applied to thousands of buildings. This repository aims at supporting the widespread adoption of EMSs by enabling the provisioning of forecasting and optimization algorithms for energy management at scale. Energy Service Generics is a framework that allows scientists and developers to derive fully functional web services as well as the corresponding client software for forecasting or optimization code written in Python with ease.

For further information about the framework please consult the [corresponding paper available here](https://arxiv.org/abs/2402.15230). The latter provides further details about motivation and necessity of web-services for EMS applications, an extensive discussion of the technical design underlying the Energy Service Generics framework as well documentation of other relevant  aspects.

## Usage

After checking out or downloading the source code install the package with:

```bash
pip install ./source
```

If you would like to use the package to implement a service install the package including the additional dependencies with:

```bash
pip install ./source[service]
```

If you need [Pandas](https://pandas.pydata.org/) install with:

```bash
pip install ./source[pandas]
```

Both options can be combined.

Finally check that the installation was successful by executing the tests:

```
pytest ./source/tests
```

## Citation

Please consider citing us if this software and/or the accompanying [paper](https://arxiv.org/abs/2402.15230) was useful for your scientific work. You can use the following BibTex entry:

```
@misc{wölfle2024open,
      title={Open Energy Services -- Forecasting and Optimization as a Service for Energy Management Applications at Scale}, 
      author={David Wölfle and Kevin Förderer and Tobias Riedel and Lukas Landwich and Ralf Mikut and Veit Hagenmeyer and Hartmut Schmeck},
      year={2024},
      eprint={2402.15230},
      archivePrefix={arXiv},
      primaryClass={cs.SE}
}
```

## Development Instructions

The recommend way of working on the code is to run it in a docker container.

This repo employs a [test-driven development](https://en.wikipedia.org/wiki/Test-driven_development) schema in combination with a script that automatically runs the tests on file changes. In order to start the container execute:

```bash
docker compose -f docker-compose-autotest.yml up --no-log-prefix
```

Furthermore, a functional service is included for interactive testing. You can use the latter to evaluate your code changes, e.g. if working on settings that influence the interactive documentation (SwaggerUI). The following code will start the service:

```bash
docker compose -f docker-compose-interactive-test.yml up
```

You can access the interactive API documentation on http://localhost:8800/.

## Contact

Please open a GitHub issue for any inquiry that relates to the source code. Feel free to contact [David Wölfle](https://www.fzi.de/team/david-woelfle/) directly for all other inquiries.

## Contributing

Contributions are welcome! Please follow these guidelines:

* **Readability counts! Thus, before you start:** Read and understand [PEP 8](https://www.python.org/dev/peps/pep-0008/).

- **Documentation is Key:** Try to document <u>why</u> stuff is done. Furthermore document <u>what</u> is done if that is not obvious from the code.
- **Docstrings:** Every function/method/class should have a Docstring following the [Numpy convention](https://numpydoc.readthedocs.io/en/latest/format.html).
- **Provide tests for everything:** Tests ensure that your code can be maintained and is not thrown away after the first bug is encountered. Use [pytest](https://docs.pytest.org/).
- **Use the right format:** Use [Black](https://github.com/psf/black) to format your code. Maximum line length is 80 characters.

Code will only be accepted to merge if it is:

- **Formally correct:** [Flake8](https://flake8.pycqa.org/en/latest/) shows no errors or warnings. Again using a maximum line length of 80 characters.
- **Logically correct:** All tests pass and all relevant aspects of the code are tested.
